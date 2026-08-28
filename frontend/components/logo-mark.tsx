// The app's icon: a magnifying glass over a small connected-dot cluster --
// guided inspection of a dataset's structure. Shares this one definition
// with the header (and anywhere else it's needed) rather than duplicating
// the SVG markup; the standalone favicon (app/icon.svg) is a separate raw
// file since Next.js's icon convention can't consume a React component,
// but its shapes are kept identical to this one by hand -- see that file's
// own comment if the mark ever changes.
export function LogoMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 200 200" className={className} xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <rect x="4" y="4" width="192" height="192" rx="44" fill="#F7F3E9" />
      <line x1="118" y1="118" x2="145" y2="145" stroke="#3D6B7A" strokeWidth="16" strokeLinecap="round" />
      <line x1="88" y1="88" x2="74" y2="76" stroke="#2A2520" strokeWidth="3" />
      <line x1="88" y1="88" x2="100" y2="78" stroke="#2A2520" strokeWidth="3" />
      <line x1="88" y1="88" x2="96" y2="100" stroke="#2A2520" strokeWidth="3" />
      <circle cx="74" cy="76" r="6" fill="#8A6D2F" />
      <circle cx="100" cy="78" r="5" fill="#8A6D2F" />
      <circle cx="96" cy="100" r="6" fill="#8A6D2F" />
      <circle cx="88" cy="88" r="9" fill="#4A7A3A" />
      <circle cx="88" cy="88" r="42" fill="none" stroke="#3D6B7A" strokeWidth="16" />
    </svg>
  );
}
