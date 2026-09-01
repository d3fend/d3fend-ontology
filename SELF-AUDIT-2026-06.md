---
repo: d3fend-ontology
date: 2026-06-21
source: WF-C intent self-audit
branch-audited: ocsf-crosswalk-reciprocity
upstream: github.com/d3fend/d3fend-ontology (default branch develop)
fork: github.com/flying-coyote/d3fend-ontology
---

# Self-Audit — d3fend-ontology (fork, branch `ocsf-crosswalk-reciprocity`)

## What this repo is FOR

This is a **fork of MITRE's `d3fend/d3fend-ontology`** used as the working tree for upstream
contributions. The vendored repo itself (README.md:1, README.md:13) produces the D3FEND ontology
distribution: edit `src/ontology/d3fend-protege.ttl`, `make all`, ship `dist/d3fend.{ttl,owl,json}`.
That is MITRE's purpose, not Jeremy's. Jeremy's purpose for *this clone* is narrow and documented in
project1 memory (`project_d3fend_ontology_pr.md`): donate read-only SPARQL **quality-report queries**
to the commons (the "contribute, don't own" posture), specifically OCSF↔D3FEND crosswalk hygiene
checks tied to upstream issues #439 / #571 / #569.

On the audited branch `ocsf-crosswalk-reciprocity`, the entire local delta over `origin/develop` is
**two files, 40 lines added, nothing removed**:

- `src/queries/ocsf-crosswalk-reciprocity.rq` (39 lines) — a SPARQL `SELECT` that flags every
  D3FEND→OCSF `rdfs:seeAlso` with no reciprocal OCSF→D3FEND back-link, matched by class local-name.
- `src/queries/ocsf-crosswalk-reciprocity-profile.txt` (1 line) — a ROBOT profile binding that query
  at severity `ERROR`.

So the branch is a single-purpose contribution branch carrying one PR's worth of work (the memory
calls it PR #594, "query + ERROR profile only"). Everything else in the tree is upstream MITRE code.

## Intent question bank — applied to the local contribution, not to MITRE's repo

I scoped the intent pass to what Jeremy added and controls. Auditing MITRE's Makefile or ontology
build against *our* intent would be a category error — that machinery serves MITRE's release, and we
are a guest in it.

**Q1 Goal — does the mechanism serve the stated intent, and only that?** Yes, cleanly, and the query's
own header is the evidence. Lines 6-14 of the `.rq` state the precondition out loud: the check is only
meaningful against a **merged graph** (D3FEND ⊕ the OCSF crosswalk triples), and against the D3FEND
ontology alone "every OCSF link reports as one-directional, which is expected." This is the rare case
where a mechanism documents its own scope so a future reader can't mis-fire it. The query matches
reciprocity by local-name (`.rq`:29-37) precisely because the OCSF URL form
(`.../event/d3f:ProcessEvent`) and the D3FEND IRI form (`...owl#ProcessEvent`) differ — the round-trip
is asserted on the part that actually agrees. Intent and mechanism match.

**Q4 Autonomy boundary — is this on the right rung?** Yes. It is a read-only `SELECT` (no `INSERT`/
`DELETE`/`CONSTRUCT`), it runs only when a human invokes ROBOT against a materialized merged graph,
and — verified — it is **deliberately NOT wired into the default build**. The `reports:` aggregate
target in the Makefile lists seven report files and does not include reciprocity (Makefile, `reports:`
target). `grep reciprocity Makefile` returns nothing. That is the correct rung: the other quality
queries (e.g. `missing-attack-id-profile.txt`) each have a `reports/*-report.txt:` target that runs
`./bin/robot report --profile … --fail-on …` against `build/d3fend-full.owl`; this one does not,
because `build/d3fend-full.owl` is the D3FEND-only graph where the query is known to false-positive on
every link. The `ERROR` severity in the profile is gated behind a merged-CI loop that doesn't exist in
this repo yet (the query header, lines 11-14, names that gap explicitly: "nothing asserts the
reciprocity survives an OCSF/D3FEND bump"). Read-only + human-invoked + not-in-default-loop is exactly
where a guest contribution to someone else's CI should sit.

**Q5 Where most wrong.** The reciprocity match is structural (local-name string equality after
stripping to the last `#`/`/`/`:`), so it is blind to *semantic* mismatch. The memory's own measured
run (`project_d3fend_ontology_pr.md`, 2026-06-19: 59/69 round-trip, 10 one-directional) already found
two class-name mismatches the local-name match would mis-handle — D3FEND `OutboundInternet*Web*Traffic`
vs OCSF `OutboundInternet*Network*Traffic` round-trips on neither side because the local names genuinely
differ, and that is a real reciprocity gap, but a reader could read the query as "names must match" and
miss that some non-matches are correct renames rather than missing back-refs. The query reports the
symptom (no local-name-equal back-ref); a human still has to classify each hit as mismatch / missing /
stale (the three buckets the memory already sorts the 10 into). This is fine for a *report* query —
reports surface candidates, humans adjudicate — but if the `ERROR` profile is ever wired into a gate,
the gate would fail on legitimate renames. That's the most-likely-wrong belief: that local-name
equality is a clean reciprocity oracle. It's a good *screen*, not an oracle.

**Q6 The one constraint.** The single thing limiting this contribution's usefulness is the one its own
header names: there is no merged D3FEND⊕OCSF graph materialized anywhere in *this* repo, so the query
cannot run here and prove itself. The measurement that validated it (59/69) was done out-of-tree via
`/tmp/reciprocity.py` against live `ocsf/ocsf-schema` main refs (per memory). The contribution is sound
but currently un-runnable inside the repo it lives in — its value is fully realized only once an
upstream maintainer wires it into a loop that has the merged graph (issue #571's "tighter OCSF
development loops"). That's an upstream dependency we don't control, which is the right place for the
constraint to sit for a donate-the-discipline posture.

**Q9 Bus-factor.** This is the sharp one. The entire OCSF↔D3FEND contribution program — which branch
holds which PR, that PR #594 is "query+ERROR-profile only / not wired into default reports", that the
reciprocity result is 59/69, that `/tmp/reciprocity.py` is the script that produced it, that `#1582` is
an `ocsf/ocsf-schema` issue and not a d3fend one — lives **only** in one project1 memory note
(`project_d3fend_ontology_pr.md`) and in Jeremy's head. None of it is in this repo. There is no
`CONTRIB-LOG.md`, no note in the branch, no committed copy of `/tmp/reciprocity.py` (it's in `/tmp`, so
it's already effectively gone on the next reboot). The branch name and the one commit message are the
only in-repo breadcrumbs. If the memory note rots or Jeremy steps away mid-PR, the next person cannot
reconstruct what graph the query expects, how the 59/69 was derived, or which of the three buckets each
one-directional hit fell in — they'd have to re-derive it from scratch against a moving OCSF main.

## Does it run loops / scheduled jobs / automation? Where is the RETHINK?

**No.** This repo runs no scheduled job, no cron, no `/loop`, no Routine on Jeremy's side. The only
automation is MITRE's CI (`.github/workflows/ci.yaml`, `.gitlab-ci.yml` — a stock 3-stage
build/test/deploy demo template) which fires on push to MITRE's repo, not ours, and which Jeremy
doesn't own or schedule. The contribution is a static pair of files reviewed by humans on a PR. So the
strong-Act / stale-Orient risk **does not apply** — there is no Act leg here to run on a stale Orient.
A RETHINK instrument would be over-engineering for a two-file read-only PR; the right intent-check is
the human PR review upstream, and the query's self-documenting header is itself a small intent-check
(it tells a future runner what the query is and isn't for). **RETHINK: n/a — correctly absent.**

## Dead weight

Genuinely little, because the local footprint is two files and both are live. The candidates are about
the *clone*, not the contribution:

- **Stale memory vs reality (low severity, but it's the audit's job to flag):** the project1 memory
  note says the active work is on branch `add-ocsf-quality-reports` and frames the reciprocity query as
  "PR #594 (branch `ocsf-crosswalk-reciprocity`)". The checked-out branch is indeed
  `ocsf-crosswalk-reciprocity` with one commit, but the memory was written 2026-06-19 and several local
  branches now exist (`add-ocsf-quality-reports`, `def-tech-artifacts-report`, `develop`, this one).
  Nothing on disk reconciles which branch maps to which open PR. Not dead weight exactly, but the
  branch-to-PR map is undocumented in-repo and only partly current in memory.
- **`/tmp/reciprocity.py`** — the script that produced the validating measurement is in `/tmp` and
  unversioned. That's not in this repo to delete, but it is the reproducibility hole behind the
  bus-factor finding: the result is cited, the method isn't committed anywhere.
- No superseded benchmarks, no abandoned dirs, no stale generated docs in the local delta. The vendored
  MITRE files (`CHANGELOG.md`, `Pipfile.lock`, etc.) are upstream and out of scope — not ours to prune.

## Honest verdict

The contribution itself is in good shape and, by the standards of this audit, unusually disciplined:
the mechanism documents its own intent and scope, it sits on the correct read-only / not-in-default-loop
rung, and it does not pretend to run in a graph it can't see. The two real findings are both *outside*
the two files: (1) the reciprocity oracle is local-name string equality, a screen not a semantic oracle,
which would mis-gate on legitimate class renames if the `ERROR` profile is ever wired into a blocking
loop — keep it report-only until the merged-graph loop exists; and (2) the whole contribution program's
working model (branch↔PR map, the 59/69 derivation, the `/tmp/reciprocity.py` method) lives only in one
project1 memory note plus tribal knowledge, with nothing in-repo, so the bus-factor is one stale memory
file away from unrecoverable. The cheapest fix for both is a committed `CONTRIB-NOTES.md` (or a longer
commit body) in the fork that records: which branch is which PR, the merged-graph precondition, and the
reciprocity script — moving the working model from memory-held to repo-held.
