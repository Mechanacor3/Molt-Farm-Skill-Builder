# Web Game Dev Loop

This skill is intentionally biased toward a short loop with fast human feedback.

Recommended order:
1. Scope the first playable slice.
2. Build only enough code to make that slice interactive.
3. Validate the behavior in the browser.
4. Observe what actually happened, not what you expected.
5. Improve one dimension.
6. Measure whether the pass helped.

Good first slices:
- one movement mechanic
- one hazard
- one score counter
- one restart path
- one deterministic debug hook

Bad first slices:
- multiple levels
- large art passes
- full menus and settings
- long content pipelines
- broad "make it fun" rewrites with no evidence

Useful measurements:
- what failed in the browser
- what control felt awkward
- how long it takes to reach the first loss or first reward
- whether score, timer, and restart logic stay stable across reruns

Stop a pass when:
- the requested dimension improved enough to re-test
- the next problem needs a different skill
- you are tempted to mix balance and polish into a bootstrap fix
