import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-6 px-6 text-center">
      <div className="max-w-xl space-y-3">
        <h1 className="text-3xl font-semibold tracking-tight">FAIR Maturity Copilot</h1>
        <p className="text-muted-foreground">
          A guided, plain-language self-assessment against the FAIR data principles &mdash; built
          for research group leads who don&rsquo;t have a data librarian on staff.
        </p>
      </div>
      <Button
        size="lg"
        nativeButton={false}
        render={<Link href="/assessments/new">Start an assessment</Link>}
      />
    </main>
  );
}
