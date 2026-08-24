import Link from "next/link";

// Shared chrome across all 4 screens -- part of the design-critique fix: each
// page used to float alone in an unframed viewport, which read as
// unfinished rather than intentionally minimal. This is deliberately quiet
// (a wordmark and a rule), not a nav bar -- the app is a single linear flow,
// there's nothing to navigate to.
export function SiteHeader() {
  return (
    <header className="border-t-4 border-t-primary">
      <div className="mx-auto flex max-w-5xl items-center px-6 py-4">
        <Link href="/" className="font-heading text-lg font-semibold tracking-tight text-foreground">
          FAIR Maturity Copilot
        </Link>
      </div>
    </header>
  );
}
