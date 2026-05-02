---
title: Right-time surface
type: concept
domain: company-brain
created: 2026-04-20
date: 2026-04-20
circle: institutional
audience: both
related:
  - "[[three-circles-protocol]]"
  - "[[typed-relationships-schema]]"
relationships:
  - type: supports
    target: "[[example-synthesis-company-brain-overview]]"
    evidence:
      - "[[example-synthesis-company-brain-overview]]"
    status: active
    note: "Right-time surface is one of the four Company Brain elements."
---

# Right-time surface

> A Company Brain shows up **at the moment of work**, not when the user remembers to search.

## What it is

Right-time surface means the system pushes related context the moment a piece of work is happening — drafting a doc, taking a customer call, assigning a ticket — instead of waiting for a search query.

## Why it matters

Search-based knowledge bases have a discoverability ceiling. Most context that *would* be useful is never searched for, because the user doesn't realize there is something to look up.

Right-time surface flips this: the system, knowing the current task context (e.g. "user is drafting a proposal about pricing"), surfaces related concepts / open commitments / historical drafts automatically.

## Five canonical scenarios (Sentra Part 2)

1. Before a customer call — surface open commitments + recent issues + prior conversations
2. While editing a roadmap doc — surface related customer asks + overlapping work
3. When assigning a ticket — surface historical incidents + likely owners
4. When approving a pricing exception — surface precedents
5. When onboarding a new hire — build a personalized first map

## Anti-patterns

- Pop-up notifications that interrupt without context (those are alerts, not surface).
- Sidebar widgets that show static content (those are dashboards).
- Search bars that the user has to actively use (search is a **fallback** for surface, not a substitute).

## How this skill implements it

`scripts/brain_surface.py` searches concepts / syntheses / decisions / transcripts / drafts by topic, returns ranked hits with snippets, and respects the role lens (self / student / partner / agent).

In production it should run on a hook (Claude Code `UserPromptSubmit`, IDE pre-commit, doc-editor plugin) so it fires *before* the user finishes drafting, not after.
