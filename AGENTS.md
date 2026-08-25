# Agent operating rules for this repo

Read this before doing any work here, agentic or otherwise. It doesn't replace
`README.md`'s "Branching convention" section (that's still the source of
truth on *why*) — this file exists so the hard limits survive even when an
agent is given broad autonomous/auto-approve permissions.

## Hard limits — no autonomy override permits these, ever

An agent must stop and get the project owner's **explicit, in-the-moment**
go-ahead before any of the following, regardless of what tool-approval mode
is active:

1. **Pushing `staging` to `main`, or opening/merging a PR into `main`.**
2. **Pushing `development` to `staging`.**
3. **Pushing local commits on `development` or `staging` to `origin`
   (GitHub)** — even if merging onto that branch was already approved.
   Approval to merge locally is not approval to push.
4. **Merging any pull request** — an open PR is never itself permission to
   merge, no matter how long it's been open or how clean the review was.
5. **Committing directly to `development`, `staging`, or `main`.** All work
   starts on a `feature/<name>` branch cut from `development`.

## What autonomy *does* cover

Everything in the direction of already-agreed work: running commands,
reading/writing/editing files, committing to a feature branch, running
tests, and self-reviewing/merging a feature branch **locally** into
`development` (not pushing it) after that review. The rule is about
*production-facing or remote-facing* moves, not ordinary implementation
work on an isolated branch.

## Branching structure

```
feature/<name>  →  development  →  staging  →  main
 (isolated)          (integration)   (pre-prod)   (production)
```

One direction only. See `README.md` for the full description of the review
gates at each promotion step (self-review before `development`, review
before `staging`, a second independent review before the `main` PR goes up).
