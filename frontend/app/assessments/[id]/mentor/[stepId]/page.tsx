"use client";

import { useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Send } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { LoadingState } from "@/components/loading-state";
import { PrincipleChip } from "@/components/fair-spectrum";
import { api, ApiError } from "@/lib/api-client";
import type { MentorAction, MentorConversation, MentorMessage, PlanIndicatorRef, PlanStep, SkillLevel } from "@/lib/types";

// Full markdown, not just bold/italics -- the model decides when structure
// (a short list, a code snippet, a comparison table) genuinely helps versus
// when a plain sentence does, per mentor_system.jinja's formatting
// guidance. remark-gfm adds tables/strikethrough/task lists on top of
// react-markdown's default CommonMark support. The child-selector styles
// below exist because none of this had ever needed rendering inside a
// chat bubble before -- headings especially are scaled down so a mentor
// reply can't visually overpower the conversation it's part of.
const MENTOR_MARKDOWN_CLASSES =
  "[&_h1]:text-[0.95em] [&_h1]:font-semibold [&_h1]:mt-2 [&_h1]:mb-1 " +
  "[&_h2]:text-[0.95em] [&_h2]:font-semibold [&_h2]:mt-2 [&_h2]:mb-1 " +
  "[&_h3]:text-[0.95em] [&_h3]:font-semibold [&_h3]:mt-2 [&_h3]:mb-1 " +
  "[&_ul]:list-disc [&_ul]:pl-5 [&_ul]:my-1 [&_ol]:list-decimal [&_ol]:pl-5 [&_ol]:my-1 [&_li]:my-0.5 " +
  "[&_a]:text-primary [&_a]:underline [&_a]:underline-offset-2 " +
  "[&_code]:rounded [&_code]:bg-muted [&_code]:px-1 [&_code]:py-0.5 [&_code]:text-[0.85em] [&_code]:font-mono " +
  "[&_pre]:my-1.5 [&_pre]:overflow-x-auto [&_pre]:rounded-md [&_pre]:bg-muted [&_pre]:p-2 [&_pre_code]:bg-transparent [&_pre_code]:p-0 " +
  "[&_blockquote]:border-l-2 [&_blockquote]:border-border [&_blockquote]:pl-2 [&_blockquote]:italic [&_blockquote]:text-muted-foreground " +
  "[&_table]:my-1.5 [&_table]:w-full [&_table]:border-collapse [&_th]:border [&_th]:border-border [&_th]:px-2 [&_th]:py-1 [&_th]:text-left [&_td]:border [&_td]:border-border [&_td]:px-2 [&_td]:py-1 " +
  "[&_hr]:my-2 [&_hr]:border-border";

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
  const params = useParams<{ id: string; stepId: string }>();
  const { id: runId, stepId } = params;

  // The plan's own copy of this step, used for the header before a chat
  // exists (title/detail/indicator list). Only findable while this step is
  // still part of the *current* plan version -- if the plan has since
  // regenerated, this stays null and the header falls back to something
  // generic, but the chat itself (if one already exists) still loads fine,
  // since the mentor routes resolve a step by id regardless of which plan
  // version it came from.
  const [planStep, setPlanStep] = useState<PlanStep | null>(null);
  const [conversation, setConversation] = useState<MentorConversation | null>(null);
  const [needsSkillLevel, setNeedsSkillLevel] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        try {
          const plan = await api.getPlan(runId);
          if (!cancelled) setPlanStep(plan.steps.find((s) => s.id === stepId) ?? null);
        } catch {
          // Non-fatal -- the header just falls back to something generic.
        }

        try {
          const convo = await api.getMentorConversation(runId, stepId);
          if (!cancelled) setConversation(convo);
        } catch (err) {
          if (cancelled) return;
          // No conversation started yet for this step -- the normal
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
  }, [runId, stepId]);

  async function handleStart(skillLevel: SkillLevel) {
    setError(null);
    try {
      const convo = await api.startMentorConversation(runId, stepId, skillLevel);
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

  if (!conversation && !needsSkillLevel) {
    return <LoadingState title="Opening the mentor…" />;
  }

  const title = planStep?.title ?? "This step";
  const indicators: PlanIndicatorRef[] = conversation?.indicators ?? planStep?.indicators ?? [];

  return (
    <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-6 px-6 py-10">
      <div className="space-y-2">
        <Link
          href={`/assessments/${runId}/plan`}
          className="text-sm text-muted-foreground underline underline-offset-4 hover:text-foreground"
        >
          ← Back to plan
        </Link>
        <h1 className="font-heading text-xl font-semibold text-balance">{title}</h1>
        {indicators.length > 0 && (
          <ul className="flex flex-wrap gap-2">
            {indicators.map((indicator) => (
              <li
                key={indicator.indicator_id}
                className="flex items-center gap-1.5 rounded-full border bg-card px-2.5 py-1 text-xs"
              >
                <PrincipleChip group={indicator.principle_group} />
                {indicator.title}
              </li>
            ))}
          </ul>
        )}
        <p className="text-sm text-muted-foreground">
          Talk this step through with a mentor -- it can update your answers for you once you confirm you&apos;ve
          actually done something.
        </p>
      </div>

      {needsSkillLevel ? (
        <SkillLevelPicker onPick={handleStart} />
      ) : (
        conversation && <ChatPanel runId={runId} stepId={stepId} initial={conversation} />
      )}

      <Button
        variant="outline"
        nativeButton={false}
        render={<Link href="/assessments/new">Start another assessment</Link>}
      />
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

function ChatPanel({ runId, stepId, initial }: { runId: string; stepId: string; initial: MentorConversation }) {
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
      const reply = await api.sendMentorMessage(runId, stepId, content);
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
          your answer changed and the assessment was rescored. New score:{" "}
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
          isMentor ? `bg-card ring-1 ring-foreground/10 ${MENTOR_MARKDOWN_CLASSES}` : "bg-primary text-primary-foreground"
        }`}
      >
        {isMentor ? (
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
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
