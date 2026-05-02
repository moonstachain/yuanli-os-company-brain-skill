---
title: "Example meeting transcript: distill Company Brain into a skill"
type: transcript
date: 2026-05-02
circle: raw
participants: ["alice", "bob"]
duration: ~30min
---

# Example meeting transcript

> A short fictional transcript used as the example source for `decisions/2026-05-02-example-skill-distillation.md`. The 4-tuple extractor (`extract_decision.py`) reads this kind of transcript and produces a draft decision page.

---

**alice**: So I want to talk about the Company Brain stack we built. The methodology is the asset, not the data. If we keep it private, the IP stays trapped in one vault.

**bob**: I agree the methodology is the interesting part. But are you proposing we publish the actual notes too?

**alice**: No, just the skill — the spec, the scripts parameterized for any vault, and a small example vault. Like, ten or fifteen notes that show how it all hangs together.

**bob**: OK, that makes sense. But we just self-audited and the usage maturity was D. Should we wait until we have more usage data?

**alice**: Honestly, no. The scaffold is A grade. We have command-output evidence. We have a 100% grep-verified extraction across three real transcripts. That's enough for a v0.1 experimental release. We can re-score after 7 days.

**bob**: I worry about the framing though. If we publish 54 out of 60 scaffold and 4 out of 10 usage, won't that look unfinished and scare off adopters?

**alice**: Let's be explicit it's not production. We label it v0.1 experimental, we put the honest scores in the README. People can calibrate. That's better than overclaiming and losing trust later.

**bob**: Fine. I'll read the README before you commit. Make sure the honest-constraints section is clear.

**alice**: Deal. I'll do the build today — SKILL.md, five references, five parameterized scripts, the example vault. End of day.

**bob**: I'll do the review. What about scheduling the 7-day re-audit?

**alice**: Let's lock the re-score. Fire date 2026-05-09. I'll arm the agent at create time. After 7 days we re-run all three lint scripts on the public vault, check explicit-relationships growth, decisions count, typed edges. If usage is still D, that's data, not failure.

**bob**: Agreed. One more thing — I think we should reject the "spec only" option. Methodology without runtime is hard to evaluate; readers can't kick the tires. Let people clone and run on their own vault.

**alice**: Yes. We'll go with full skill. Done.

**bob**: Done. Let me know when the README is ready.

---

> End of transcript. Total ~800 words. Use this with `extract_decision.py` to generate the matching decision page.
