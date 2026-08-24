import type { PrincipleGroup } from "@/lib/types";

// The signature element: a segmented tracker sized by how many of the 12
// indicators actually belong to each FAIR principle (4/3/1/4), not four
// equal slices. It reads at a glance that "Interoperable" is a single
// question, not a fourth of the assessment -- which is true, and which a
// generic linear progress bar hides completely.
const PRINCIPLE_ORDER: PrincipleGroup[] = ["Findable", "Accessible", "Interoperable", "Reusable"];

const PRINCIPLE_COLOR: Record<PrincipleGroup, string> = {
  Findable: "bg-primary",
  Accessible: "bg-gold",
  Interoperable: "bg-severity-unknown",
  Reusable: "bg-severity-minor",
};

const PRINCIPLE_TRACK: Record<PrincipleGroup, string> = {
  Findable: "bg-primary/15",
  Accessible: "bg-gold-soft",
  Interoperable: "bg-severity-unknown-soft",
  Reusable: "bg-severity-minor-soft",
};

export function FairSpectrum({
  principleGroups,
  completedThrough,
}: {
  /** principle_group for each question, in display order (index = question position). */
  principleGroups: PrincipleGroup[];
  /** how many questions, from the start, count as done -- fills that many segments. */
  completedThrough: number;
}) {
  // Counted by group membership at each index, not by a contiguous block --
  // the 12 indicators aren't grouped contiguously in display order (the
  // "flex slot" Findable indicator sits last, after all the Reusable ones),
  // so a cumulative-offset approach would fill the Findable segment early
  // and leave it stuck, ignorant of that final question.
  const counts = PRINCIPLE_ORDER.map(
    (group) => principleGroups.filter((g) => g === group).length
  );
  const total = principleGroups.length;

  return (
    <div className="space-y-1.5">
      <div className="flex h-2.5 w-full gap-1" role="progressbar" aria-valuenow={completedThrough} aria-valuemin={0} aria-valuemax={total}>
        {PRINCIPLE_ORDER.map((group, i) => {
          const count = counts[i];
          if (count === 0) return null;
          const filled = principleGroups.filter((g, idx) => g === group && idx < completedThrough).length;
          const fillPercent = (filled / count) * 100;
          return (
            <div
              key={group}
              className={`relative overflow-hidden rounded-full ${PRINCIPLE_TRACK[group]}`}
              style={{ flexGrow: count, flexBasis: 0 }}
              title={`${group}: ${count} indicator${count === 1 ? "" : "s"}`}
            >
              <div
                className={`h-full rounded-full transition-all ${PRINCIPLE_COLOR[group]}`}
                style={{ width: `${fillPercent}%` }}
              />
            </div>
          );
        })}
      </div>
      <div className="flex justify-between text-[0.7rem] font-medium tracking-wide text-muted-foreground uppercase">
        {PRINCIPLE_ORDER.map((group, i) =>
          counts[i] > 0 ? <span key={group}>{group}</span> : null
        )}
      </div>
    </div>
  );
}

export function PrincipleChip({ group }: { group: PrincipleGroup }) {
  return (
    <span
      className={`inline-flex h-5 min-w-5 items-center justify-center rounded-full px-1.5 text-[0.65rem] font-semibold ${PRINCIPLE_TRACK[group]} ${
        group === "Findable"
          ? "text-primary"
          : group === "Accessible"
            ? "text-gold"
            : group === "Interoperable"
              ? "text-severity-unknown"
              : "text-severity-minor"
      }`}
      title={group}
    >
      {group[0]}
    </span>
  );
}
