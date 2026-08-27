// The signature element: a segmented tracker sized by how many of an
// adapter's indicators actually belong to each principle group, not equal
// slices. It reads at a glance that a single-question group isn't a
// quarter of the assessment -- which a generic linear progress bar hides
// completely.
//
// Group colors are looked up by name rather than derived from a hash
// (issue #16, when a second adapter's own 3 groups were added): a hash
// risks two groups landing on the same or a visually-similar color at
// small N, and this app only ever has a handful of adapters with a
// handful of groups each, so an explicit table costs nothing and removes
// the risk entirely. fair-v0's 4 known groups keep their exact original
// classes -- this refactor must not change how the existing check looks.
const GROUP_STYLE: Record<string, { bar: string; track: string; text: string }> = {
  // fair-v0
  Findable: { bar: "bg-primary", track: "bg-primary/15", text: "text-primary" },
  Accessible: { bar: "bg-gold", track: "bg-gold-soft", text: "text-gold" },
  Interoperable: { bar: "bg-severity-unknown", track: "bg-severity-unknown-soft", text: "text-severity-unknown" },
  Reusable: { bar: "bg-severity-minor", track: "bg-severity-minor-soft", text: "text-severity-minor" },
  // harmonization-v0
  "Consistent Naming": { bar: "bg-group-a", track: "bg-group-a-soft", text: "text-group-a" },
  "Shared Vocabulary": { bar: "bg-group-b", track: "bg-group-b-soft", text: "text-group-b" },
  "Linking & Mapping": { bar: "bg-group-c", track: "bg-group-c-soft", text: "text-group-c" },
};

// Only reached if a future adapter introduces a group name not listed
// above -- keeps the component from breaking rather than looking exactly
// right; add the real entry to GROUP_STYLE when that happens instead of
// relying on this indefinitely.
const FALLBACK_STYLE = { bar: "bg-muted-foreground", track: "bg-muted", text: "text-muted-foreground" };

function styleFor(group: string) {
  return GROUP_STYLE[group] ?? FALLBACK_STYLE;
}

export function FairSpectrum({
  principleGroups,
  completedThrough,
}: {
  /** principle_group for each question, in display order (index = question position). */
  principleGroups: string[];
  /** how many questions, from the start, count as done -- fills that many segments. */
  completedThrough: number;
}) {
  // Order of first appearance, deduplicated -- works for any adapter's
  // grouping, not just fair-v0's fixed 4. Counted by group membership at
  // each index, not by a contiguous block, since a group's questions
  // aren't guaranteed to be contiguous in display order (fair-v0's own
  // "flex slot" Findable indicator sits last, after all the Reusable
  // ones) -- a cumulative-offset approach would fill a segment early and
  // leave it stuck, ignorant of a later question in that same group.
  const order = [...new Set(principleGroups)];
  const counts = order.map((group) => principleGroups.filter((g) => g === group).length);
  const total = principleGroups.length;

  return (
    <div className="space-y-1.5">
      <div className="flex h-2.5 w-full gap-1" role="progressbar" aria-valuenow={completedThrough} aria-valuemin={0} aria-valuemax={total}>
        {order.map((group, i) => {
          const count = counts[i];
          if (count === 0) return null;
          const style = styleFor(group);
          const filled = principleGroups.filter((g, idx) => g === group && idx < completedThrough).length;
          const fillPercent = (filled / count) * 100;
          return (
            <div
              key={group}
              className={`relative overflow-hidden rounded-full ${style.track}`}
              style={{ flexGrow: count, flexBasis: 0 }}
              title={`${group}: ${count} indicator${count === 1 ? "" : "s"}`}
            >
              <div
                className={`h-full rounded-full transition-all ${style.bar}`}
                style={{ width: `${fillPercent}%` }}
              />
            </div>
          );
        })}
      </div>
      <div className="flex justify-between text-[0.7rem] font-medium tracking-wide text-muted-foreground uppercase">
        {order.map((group, i) => (counts[i] > 0 ? <span key={group}>{group}</span> : null))}
      </div>
    </div>
  );
}

export function PrincipleChip({ group }: { group: string }) {
  const style = styleFor(group);
  return (
    <span
      className={`inline-flex h-5 min-w-5 items-center justify-center rounded-full px-1.5 text-[0.65rem] font-semibold ${style.track} ${style.text}`}
      title={group}
    >
      {group[0]}
    </span>
  );
}
