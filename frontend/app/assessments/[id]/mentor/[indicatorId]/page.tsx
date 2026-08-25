"use client";

import { useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Send } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { LoadingState } from "@/components/loading-state";
import { PrincipleChip } from "@/components/fair-spectrum";
import { api, ApiError } from "@/lib/api-client";
import type { MentorAction, MentorConversation, MentorMessage, Question, SkillLevel } from "@/lib/types";

const ADAPTER_ID = "fair-v0";

// Only bold/italics are rendered -- everything else (headings, links, lists,
// code, images, tables) is unwrapped back to plain text rather than
// rendered as its element, per an explicit choice to keep chat replies
// looking like plain-language prose, not a formatted document. The mentor's
// own system prompt (mentor_system.jinja) is told to only ever use
// **bold**/*italics* for exactly this reason -- the two are kept in sync.
const MARKDOWN_DISALLOWED_ELEMENTS = [
  "h1",
  "h2",
  "h3",
  "h4",
  "h5",
  "h6",
  "a",
  "img",
  "ul",
  "ol",
  "li",
  "blockquote",
  "code",
  "pre",
  "hr",
  "table",
];

// A "someone is typing…" indicator: just a chat bubble with three bouncing
// dots (the wave). The bubble shows for a while, disappears for a couple
// seconds (long enough to read as "something is about to happen," not a
// flicker), then comes back. Randomized durations keep it from reading as
// a fixed-interval bot. No words, no labels.
const BUBBLE_VISIBLE_DURATION: [number, number] = [3000, 4500];
const BUBBLE_HIDDEN_DURATION: [number, number] = [2000, 3500];

function randomBetween([min, max]: [number, number]): number {
  return min + Math.random() * (max - min);
}

export default function MentorPage() {
  const params = useParams<{ id: string; indicatorId: string }>();
  const { id: runId, indicatorId } = params;

  const [question, setQuestion] = useState<Question | null>(null);
  const [conversation, setConversation] = useState<MentorConversation | null>(null);
  const [needsSkillLevel, setNeedsSkillLevel] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const questions = await api.getQuestions(ADAPTER_ID);
        if (cancelled) return;
        setQuestion(questions.find((q) => q.indicator_id === indicatorId) ?? null);

        try {
          const convo = await api.getMentorConversation(runId, indicatorId);
          if (!cancelled) setConversation(convo);
        } catch (err) {
          if (cancelled) return;
          // No conversation started yet for this indicator -- the normal
          // first-visit case, not a real error. Anything else (e.g. the
          // run not being completed yet) is a real error to surface.
          if (err instanceof ApiError && err.status === 404) {
            setNeedsSkillLevel(true);
          } else {
            throw err;
          }
        }
      } catch (err) {
        if (!cancelled) setError(err instanceof ApiError ? err.message : "Couldn't open the mentor.");
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [runId, indicatorId]);

  async function handleStart(skillLevel: SkillLevel) {
    setError(null);
    try {
      const convo = await api.startMentorConversation(runId, indicatorId, skillLevel);
      setConversation(convo);
      setNeedsSkillLevel(false);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't start the mentor.");
    }
  }

  if (error) {
    return (
      <main className="flex flex-1 flex-col items-center justify-center gap-3 px-6 text-center">
        <p className="text-muted-foreground">{error}</p>
        <Button
          variant="outline"
          nativeButton={false}
          render={<Link href={`/assessments/${runId}/plan`}>Back to plan</Link>}
        />
      </main>
    );
  }

  if (!question || (!conversation && !needsSkillLevel)) {
    return <LoadingState title="Opening the mentor…" />;
  }

  return (
    <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-6 px-6 py-10">
      <div className="space-y-2">
        <Link
          href={`/assessments/${runId}/plan`}
          className="text-sm text-muted-foreground underline underline-offset-4 hover:text-foreground"
        >
          ← Back to plan
        </Link>
        <div className="flex items-center gap-2">
          <PrincipleChip group={question.principle_group} />
          <h1 className="font-heading text-xl font-semibold text-balance">{question.title}</h1>
        </div>
        <p className="text-sm text-muted-foreground">
          Talk through this one gap with a mentor -- it can update your answer for you once you confirm you&apos;ve
          actually done it.
        </p>
      </div>

      {needsSkillLevel ? (
        <SkillLevelPicker onPick={handleStart} />
      ) : (
        conversation && <ChatPanel runId={runId} indicatorId={indicatorId} initial={conversation} />
      )}
    </main>
  );
}

function SkillLevelPicker({ onPick }: { onPick: (level: SkillLevel) => void }) {
  return (
    <Card>
      <CardContent className="space-y-4 pt-6">
        <p className="text-base">Before we start -- how familiar are you with this kind of work?</p>
        <p className="text-sm text-muted-foreground">
          This only changes how much the mentor explains along the way -- it&apos;s about this specific process,
          not about you.
        </p>
        <div className="flex flex-col gap-3 sm:flex-row">
          <Button className="flex-1" onClick={() => onPick("new_to_this")}>
            I&apos;m new to this
          </Button>
          <Button className="flex-1" variant="outline" onClick={() => onPick("done_this_before")}>
            I&apos;ve done this before
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function ChatPanel({
  runId,
  indicatorId,
  initial,
}: {
  runId: string;
  indicatorId: string;
  initial: MentorConversation;
}) {
  const [messages, setMessages] = useState<MentorMessage[]>(initial.messages);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [sendError, setSendError] = useState<string | null>(null);
  const [lastAction, setLastAction] = useState<MentorAction | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  async function handleSend() {
    const content = input.trim();
    if (!content || sending) return;
    setSending(true);
    setSendError(null);
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content, created_at: new Date().toISOString() }]);
    try {
      const reply = await api.sendMentorMessage(runId, indicatorId, content);
      setMessages((prev) => [...prev, reply.mentor_message]);
      if (reply.action_taken) setLastAction(reply.action_taken);
    } catch (err) {
      setSendError(err instanceof ApiError ? err.message : "The mentor couldn't reply -- try sending that again.");
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="flex flex-1 flex-col gap-4">
      {lastAction && (
        <div className="rounded-md border-2 border-severity-pass/30 bg-severity-pass-soft p-3 text-sm text-severity-pass">
          <span className="font-semibold">Updated — </span>
          your answer for this indicator changed and the assessment was rescored. New score:{" "}
          <span className="font-semibold">{lastAction.new_score}/100</span>.
        </div>
      )}

      <div
        className="flex flex-1 flex-col gap-3 overflow-y-auto rounded-lg border bg-muted/30 p-4"
        style={{ maxHeight: "50vh", minHeight: "16rem" }}
      >
        {messages.map((m, i) => (
          <ChatBubble key={i} message={m} />
        ))}
        {sending && <TypingBubble />}
        <div ref={bottomRef} />
      </div>

      {sendError && <p className="text-sm text-destructive">{sendError}</p>}

      <div className="flex gap-2">
        <Textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          rows={2}
          placeholder="Tell the mentor what's going on, or ask a question…"
          disabled={sending}
          className="flex-1"
        />
        <Button onClick={handleSend} disabled={sending || !input.trim()} size="icon" aria-label="Send message">
          <Send className="size-4" />
        </Button>
      </div>
    </div>
  );
}

function ChatBubble({ message }: { message: MentorMessage }) {
  const isMentor = message.role === "mentor";
  return (
    <div className={`flex ${isMentor ? "justify-start" : "justify-end"}`}>
      <div
        className={`max-w-[85%] rounded-lg px-3.5 py-2.5 text-sm leading-relaxed [&_p]:m-0 [&_p+p]:mt-2 ${
          isMentor ? "bg-card ring-1 ring-foreground/10" : "bg-primary text-primary-foreground"
        }`}
      >
        {isMentor ? (
          <ReactMarkdown disallowedElements={MARKDOWN_DISALLOWED_ELEMENTS} unwrapDisallowed>
            {message.content}
          </ReactMarkdown>
        ) : (
          <span className="whitespace-pre-wrap">{message.content}</span>
        )}
      </div>
    </div>
  );
}

// A "someone is typing…" indicator: just a chat bubble with three bouncing
// dots. The bubble shows for a bit, briefly disappears, then comes back --
// randomized durations keep it from reading as a fixed-interval bot. No
// words, no labels, nothing else.
function TypingBubble() {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const duration = visible ? randomBetween(BUBBLE_VISIBLE_DURATION) : randomBetween(BUBBLE_HIDDEN_DURATION);
    const timeoutId = setTimeout(() => setVisible((v) => !v), duration);
    return () => clearTimeout(timeoutId);
  }, [visible]);

  if (!visible) return <div className="flex justify-start py-3.5" aria-hidden />;

  return (
    <div className="flex justify-start">
      <div className="flex items-center rounded-lg bg-card px-4 py-3.5 ring-1 ring-foreground/10">
        <div className="flex items-center gap-1">
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              className="size-2 animate-bounce rounded-full bg-muted-foreground/60"
              style={{ animationDelay: `${i * 0.2}s`, animationDuration: "1.4s" }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
