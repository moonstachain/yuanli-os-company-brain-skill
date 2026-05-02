# Sentra Company Brain · 3 Layers × 4 Elements

> Distilled from Ashwin Gopinath's "Company Brain Part 1 / Part 2" X articles (2026-04). Read this before adopting the skill — if the mental model doesn't fit your context, the rest of the skill won't help.

## Core formula

```
Factual memory + Human communication + Context graph & reasoning + Governed action
                              = Company Brain
```

Miss any one of the four and you only have:

| Missing | What you actually have |
|---|---|
| Factual memory | Search and archives |
| Human communication | Transcript and summarization |
| Context graph & reasoning | Inference and guessing |
| Governed action | Fragile automation |

A Company Brain is **not** any of those alone. It's the four wired together.

## Layer 1 · Factual memory

The record of what happened across:

- meetings / messages / emails / docs / tickets / CRM notes
- commits / incidents / dashboards
- customer calls / support conversations

Required properties:

- **Provenance** — every fact knows where it came from
- **Permissions** — who is allowed to see it
- **Timestamps** — when it became true
- **Grounding** — backed by source evidence
- **Freshness** — knows when it was last verified
- **Ownership** — has an accountable steward

Anti-pattern: dumping everything into a vector index and calling it "memory". Vectors are search infrastructure, not memory.

## Layer 2 · Context graph & reasoning

Where facts become a model of the company. The graph traces:

```
customer call → opportunity → product gap → engineering tradeoff → roadmap decision → strategy
```

The relationships **are** the memory. Without typed edges, you have a folder of artifacts, not a brain.

Required ability — **metacognition**:

The brain must know when:

- evidence is weak
- context is stale
- assumptions conflict
- a commitment has no owner
- an agent needs to ask for help

A brain that doesn't know what it doesn't know is just a confident search engine.

## Layer 3 · Action coordination

The brain decides when to:

- move
- wait
- ask for help
- escalate
- stop

This is **not** automation executing a known workflow. It's coordination from context.

Difference:

- Automation: "When ticket X arrives, run script Y."
- Coordination: "Given the open commitments / customer state / blockers, what should this team do next?"

## Three-circle invariant (Part 2 hard rule)

```
INSTITUTIONAL  (company / ecosystem record)
       ↑
SHARED         (team / project / customer common ground)
       ↑
INDIVIDUAL     (personal notes, drafts, private commitments)
```

Iron rule: `personal ≠ shared ≠ company record`.

Wrong approach:

- Build a central archive
- Force everyone to stop their natural workflow and feed the archive

Right approach (**emergence**):

- Personal notes → team docs → roadmap decisions → customer commitments
- The producer decides when something crosses a circle, by writing it differently
- The system supports promotion gates; it does not command them

## Six key oppositions (what a Company Brain is NOT)

| It is NOT | It IS |
|---|---|
| A central repository | An emergent semantic file system |
| RAG over enterprise data | A typed relationship graph |
| Enterprise search + chat box | Proactive surface in the moment of work |
| A passive query container | Right-time push |
| The same answer for everyone | Role-personalized projection (IC / manager / CEO / agent) |
| Just facts | Facts + why they matter + dissenting opinions + counterfactuals |

If your design violates more than two of these, you're building enterprise search, not a Company Brain.

## Five right-time surface scenarios (Part 2)

A real Company Brain surfaces context in moments like these:

1. **Before a customer call** — open commitments / recent issues / prior conversations
2. **While editing a roadmap doc** — related customer asks / overlapping work
3. **When assigning a ticket** — historical incidents / owners
4. **When approving a pricing exception** — precedents
5. **When onboarding a new hire** — personalized first map

If your "memory system" doesn't show up in these moments, it's archive software.

## How this relates to the rest of the skill

| Element | Skill artifact |
|---|---|
| L1 Factual memory | Your existing wiki + transcript folder (this skill is wiki-agnostic; bring your own) |
| L2 Context graph | [`scripts/relationship_graph.py`](../scripts/relationship_graph.py) + [`references/typed-relationships-schema.md`](typed-relationships-schema.md) |
| L2 Metacognition | [`scripts/metacognition_signals.py`](../scripts/metacognition_signals.py) |
| L3 Action coordination | Out of scope for v0.1 (this is where ticketing / governance bridges go) |
| Three circles | [`references/three-circles-protocol.md`](three-circles-protocol.md) |
| Right-time surface | [`scripts/brain_surface.py`](../scripts/brain_surface.py) |
| 4-tuple extraction | [`templates/decision-page.md`](../templates/decision-page.md) + [`scripts/extract_decision.py`](../scripts/extract_decision.py) |

## Sources

- Ashwin Gopinath, "Company Brain: Why Most Companies Have Data But No Memory", X article id `2049623729198743552`, 2026-04
- Ashwin Gopinath, "Company Brain, Part 2: Factual Memory", X article id `2049877146936786944`, 2026-04
- Author: Sentra.app CEO, formerly MIT professor

This skill quotes the structure, not the prose. For the original framing read the X articles directly.
