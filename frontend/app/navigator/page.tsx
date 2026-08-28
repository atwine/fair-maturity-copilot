import Link from "next/link";
import { Navigator } from "@/components/navigator";

export default function NavigatorPage() {
  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-10 px-6 py-12">
      <div className="space-y-2">
        <p className="text-sm font-semibold tracking-wide text-primary uppercase">FAIR Maturity Copilot</p>
        <h1 className="font-heading text-4xl font-semibold text-balance">Which tool fits your situation?</h1>
        <p className="text-lg leading-relaxed text-justify text-muted-foreground">
          There are half a dozen FAIR tools out there. Answer a few questions and we&rsquo;ll point you at the
          one that actually applies to you right now.
        </p>
      </div>

      <Navigator />

      <section className="space-y-3">
        <h2 className="font-heading text-xl font-semibold">Why this exists</h2>
        <p className="text-base leading-relaxed text-justify text-muted-foreground">
          Even people who&rsquo;ve sat through official FAIR training come away unsure how the tools fit
          together. That&rsquo;s not a personal failing — it&rsquo;s the actual state of this field. This short
          guide turns the flat list on the{" "}
          <Link href="/about" className="underline underline-offset-4 hover:text-foreground">
            About page
          </Link>{" "}
          into a real answer, so you don&rsquo;t have to already know which tool is for what.
        </p>
      </section>
    </main>
  );
}
