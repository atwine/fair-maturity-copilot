import Link from "next/link";
import { LogoMark } from "@/components/logo-mark";

// Shared chrome across all screens -- part of the design-critique fix: each
// page used to float alone in an unframed viewport, which read as
// unfinished rather than intentionally minimal. Deliberately quiet (a
// wordmark and a rule) rather than a full nav bar -- the assessment itself
// is still a single linear flow. "About" is the one standing exception:
// a reference page someone might want mid-assessment, not a destination
// they're routed through, so it earns a permanent, always-visible link.
export function SiteHeader() {
  return (
    <header className="border-t-4 border-t-primary">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
        <Link href="/" className="flex items-center gap-2.5 font-heading text-lg font-semibold tracking-tight text-foreground">
          <LogoMark className="size-7 shrink-0" />
          FAIR Maturity Copilot
        </Link>
        <nav className="flex items-center gap-4">
          <Link href="/navigator" className="text-sm text-muted-foreground underline underline-offset-4 hover:text-foreground">
            Which tool fits?
          </Link>
          <Link href="/about" className="text-sm text-muted-foreground underline underline-offset-4 hover:text-foreground">
            About this tool
          </Link>
        </nav>
      </div>
    </header>
  );
}
