---
type: canonical
source: none
sync: none
sla: none
last_updated: 2026-07-26
---

# Contribution cadence

How often to commit, open PRs, and file tracker items, and what a good contributor looks like.
The bar in one line: a good contributor ships small, reviewed, one-concern changes on
short-lived branches, and reviews as much as they author.

The numbers below are not house taste. Most rows trace to the evidence table that follows.
A few (open-PR cap, tracker cadence, review turnaround, session end) have no study behind
them; they are judgment calls built on the rest, named as such.

## The standard

Two profiles. Team-led repos have human reviewers; solo repos have at most an automated one.
The caps are soft: exceed one with a stated reason in the PR body, not silently.

| Dimension | Team-led repos | Solo repos |
|---|---|---|
| PR size | target 400 changed lines and 20 files or fewer; larger is split or stacked, or the body states why not | same soft cap; sweeps split by concern even with no human reviewer |
| One PR is | one concern, standing alone, green | one concern (PR-as-commit is legitimate) |
| Review window | reviewers requested at creation; no self-merge before one human approval; an admin bypass is a recorded exception, never the mechanism | the automated review, where one is wired, completes and gets read before merge |
| Branch life | two days at most, deleted on merge | same; no unpushed branch older than a day |
| Open-PR cap | about three open PRs per repo; stale at seven days means close or ticket | same |
| Commits | one logical change per commit; imperative subject under about 50 characters; the host repo's prefix convention; a body when the why is not obvious | same |
| Commit count | no target; bursts are fine, grab-bags are not | same |
| Tracker | one item per shippable change or handoff, linked from the PR; never per commit or per in-session step; a canceled item keeps its reason | an item only when work crosses a session or person boundary |
| Reviewing | answer a requested review within one business day; reciprocity is part of the job | n/a |
| Session end | a clean tree or a checkpointed handoff; prune branches deleted on the remote | same |

## The evidence

Where each number comes from. The sizes measure two different things: the change-size guidance
(about 100 lines) measures what an author ships at once; the batch guidance (200 to 400 lines)
measures what a reviewer can judge in one sitting.

| Source | Finding |
|---|---|
| Google eng-practices small-CL guide | About 100 lines is usually a reasonable change; 1,000 is usually too large. One CL is one self-contained change. https://google.github.io/eng-practices/review/developer/small-cls.html |
| Google observed practice (Sadowski et al., ICSE-SEIP 2018, 9M changes) | Median change is 24 lines; about 90 percent touch under 10 files; median 1 reviewer; the median developer authors about 3 changes a week. https://sback.it/publications/icse2018seip.pdf |
| SmartBear/Cisco review study | 200 to 400 LOC per review session, under 500 LOC per hour; 60 to 90 minute sessions catch 70 to 90 percent of defects. https://smartbear.com/learn/code-review/best-practices-for-peer-code-review/ |
| Microsoft (Bosu et al. 2015, 1.5M review comments) | The useful-comment rate falls as files-per-change grows; over 20 files is already too big. https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/bosu2015useful.pdf |
| DORA / trunk-based development | High performers keep branch lifetime under a day or two and merge to trunk at least daily. https://dora.dev/capabilities/trunk-based-development/ |
| Git and Linux kernel submitting guides | Separate commits for logically separate changes; imperative subject, summary around 50 characters, body wrapped around 72. https://git-scm.com/docs/SubmittingPatches and https://www.kernel.org/doc/html/latest/process/submitting-patches.html |
| Graphite stacked-PR practice | Flag PRs over about 250 lines or about 25 files; each stack layer is one logical thing. https://graphite.com/docs/best-practices-for-reviewing-stacks |
| Kubernetes contributor guide | No issue-before-PR mandate; a trivial fix goes straight to PR; a design-shaped change gets discussed first. https://www.kubernetes.dev/docs/guide/pull-requests/ |

## Tips for agent-heavy teams

The literature assumes human authors. When agents write most of the code, the numbers shift in
one direction: authoring gets cheap and reviewing does not.

- The binding constraint is the reviewing human's batch capacity, about 400 lines per sitting.
  Cap open-PR inventory, not author cadence: an agent can produce ten PRs a day, but they only
  count when a human has judged them.
- One logical change per commit matters more, not less, when agents write the code. It is the
  reviewer's only way to replay the reasoning.
- Branches decay faster when agents open them, because nobody's memory keeps them alive.
  Prune daily.
- A tracker item exists per shippable change or handoff, never per commit. Agents generate
  commits far faster than a tracker should grow.
- Review reciprocity is part of the job. A lead who only authors trains the team to rubber-stamp.

## What the evidence does not settle

Kept so nobody re-litigates them as if the sources decided.

- Conventional Commits: no flagship open-source project among the sources uses it. Follow the
  host repo's convention, whatever it is.
- Squash versus merge commits: per repo. The sources measure change size and review batch, not
  merge mechanics.
- The exact size cap: 100 versus 400 is not a contradiction. The first measures an author's
  change, the second a reviewer's batch. Pick the cap for the thing you are limiting.
