# Why This Tool Exists

A plain-language explainer, written to be presented — for anyone who asks
"why not just use [existing thing]?"

## Who this is for

A research group lead at an institution like ACE Uganda — someone
responsible for their team's data, but without a data manager or data
librarian on staff. They know their research. They were never trained in
data stewardship, and nobody expects them to have been. But funders,
collaborators, and good scientific practice increasingly expect research
data to be **FAIR**: Findable, Accessible, Interoperable, Reusable.

This tool exists because that person needs two things nothing else in this
space gives them together: a way to find out, in plain language, whether
their data practices are actually okay — and a clear, ordered plan for what
to do about it if they're not. Not a technical report. Not a library to go
research. An answer, and a next step.

## What "FAIR" actually means, in one paragraph

Four questions about a dataset: Can someone find out it exists
(**Findable**)? Once found, is it clear how to get it (**Accessible**)? Is
it in a format other tools and systems can actually read (**Interoperable**)?
And is there enough context — what the columns mean, who collected it, what
license applies — for someone else to use it correctly (**Reusable**)? A
formal international group, the Research Data Alliance, wrote a detailed
"maturity model" defining 41 specific things to check across those four
questions. This tool asks 12 of those 41 — the ones a non-technical research
lead can actually answer about their own data, without a data science
background.

## The landscape: what else is already out there

Before building this, we looked at six things the wider FAIR community
already uses. Here's what each one actually is, in plain terms — because
even people who've sat through official training sessions on this (including
one of us) come away unsure how they all fit together. That confusion is
not a personal failing. It's the actual state of this field.

**1. The RDA FAIR Data Maturity Model** — the 41-question yardstick
mentioned above. This is the actual standard our 12 questions are drawn
from. Everything else on this list either automates part of it, expands on
it, or teaches you how to act on it.

**2 & 3. F-UJI and FAIR Checker** — two different tools that do the same
job: point them at a public web page for your dataset, and a robot
automatically checks whether the *machine-readable* parts are in order —
can a computer program find your dataset's ID, read its metadata format,
recognize its vocabulary terms. Genuinely useful, but entirely automated —
neither one ever asks a human a question, and neither can tell you whether
your data dictionary is any good, or explain anything in plain language.
They check the wrapping, not what's inside.

**4. FAIR-DSM (the "FAIR Dataset Maturity Model")** — a much bigger,
5-level roadmap, built for large institutions with real IT infrastructure.
Level 1 is roughly "the basics" (similar in spirit to what our tool checks).
Levels 2 through 5 talk about things like semantic databases, enterprise
"master data governance," and formal metadata registries — genuinely
useful for a large research consortium building shared infrastructure, but
far beyond what a single research group needs or has access to. This is an
institutional IT roadmap, not a self-assessment for one person.

**5. The FAIR Cookbook** — a library of over 60 detailed "recipes," each
covering one specific topic (licensing, identifiers, metadata standards,
and so on). It's honest about what it is: a reference book. You get value
out of it once you already know which recipe you need. If you don't know
that yet — which is exactly the position most research leads are in — it's
just one more thing to get lost in.

**6. ELIXIR's FAIRification framework** — the one piece of this landscape
that isn't a checklist or a reference library. It describes an actual
*process*: set a goal, examine what you have, then work through concrete
steps in order (sort out identifiers, then documentation, then standards,
then hosting, then sharing). This is the piece we found most valuable — and
it's the one thing none of the other five tools actually do for you.

## Why we didn't just point people at one of these

Because none of them, on its own, solves the actual problem. The two
automated checkers (F-UJI, FAIR Checker) can't talk to a human in plain
language. The two reference resources (FAIR-DSM, the Cookbook) assume you
already know which part applies to you — and one of them is scaled for
institutions, not individuals. That leaves six different named tools, each
covering different, overlapping ground, and nothing that tells a newcomer
which one — if any — they should even start with.

That fragmentation is not a minor inconvenience. It is, itself, the
problem. Six different things to learn, before you've even started fixing
your data, is exactly the kind of overload that makes people give up.

## What we built instead

One guided path. Answer 12 plain-language questions about your own data —
each with a worked example, so you never have to already know a term before
you can answer about it. Get a score and a plain-language report — what's
working, what isn't, and why it matters, no jargon assumed. Then get a
single ordered plan: not twelve separate suggestions to figure out how to
sequence yourself, but one walkthrough — sort out your identifiers first,
then your documentation, then your formats, then where you host it, then
how you share it — the same order the FAIRification framework above
describes, generated specifically from your own gaps.

You never need to know the RDA model exists, or that F-UJI and FAIR Checker
are two different tools that do the same thing, or which of 60+ Cookbook
recipes applies to you. That's the whole point.

## Questions people are likely to ask

**"Isn't this just reinventing F-UJI or FAIR Checker?"**
No — different job entirely. Those tools check whether a computer program
can read your published metadata. This tool checks your actual *practices*
— do you have a license stated, a data dictionary, a documented access
process — the human side those tools structurally cannot see. If you ever
want the machine-readable side double-checked too, that's a job for one of
those existing tools, not something we'd rebuild.

**"Why not just send people to the FAIR Cookbook?"**
Because using it well requires already knowing what you're looking for.
Someone who doesn't yet know what a "data dictionary" is won't know to go
search for that recipe. This tool asks them directly, in plain language,
and only surfaces detail when it's relevant to their actual answer.

**"Is the RDA model the 'real' standard, or did we pick an easy one?"**
It's the real one — the same 41-indicator model referenced by F-UJI, by
FAIR-DSM, by eLwazi's own guidance to researchers. We use a deliberately
chosen 12-question subset: the ones answerable by someone without a data
science background, not a simplified or invented version.

**"Does this replace institutional-level FAIR planning (FAIR-DSM)?"**
No, and it isn't meant to. FAIR-DSM is the right tool once an institution
is building shared infrastructure across many datasets. This tool is the
right one for a single research group figuring out where they stand today.
