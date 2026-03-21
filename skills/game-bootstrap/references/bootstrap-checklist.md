# Bootstrap Checklist

Minimum acceptable first slice:
- input works
- one game loop runs
- win or fail condition is visible
- restart is possible
- game state can be inspected or inferred reliably

Good early hooks:
- `window.__gameState`
- deterministic spawn seed
- manual step or advance-time helper
- text render of state for tests

Avoid:
- multiple game modes
- large asset pipelines
- deep menu systems
- untestable randomness in the first pass
