# Molt Farm Visualization Plan

## Goal

Turn the 1602-style browser game into a readable visual shell over a running Molt Farm.

This should not become a separate fantasy economy game that merely borrows the metaphor. The metaphor is the interface:

- islands = agents
- crops = skills
- boats = agent-agent communication
- ports and warehouses = inbox, outbox, and artifact staging
- harvest = useful output becoming available to other agents

## What The User Should See

The main screen should feel like a small living archipelago, but every visual element should map to real Molt behavior.

### World Layer

- Each island is one agent instance.
- Island size and buildings reflect that agent's role, not generic decoration.
- Fields on the island show the skills that agent can use.
- Crop state shows whether a skill is idle, active, blocked, or recently productive.
- Boats move between islands only when there is a real handoff, request, or delivery.

### Inspector Layer

Selecting an island should show:

- agent id
- role
- current task
- active skills
- inbox depth
- outbox depth
- last evidence paths

Selecting a field should show:

- skill id
- current state
- last use
- recent outputs or failures tied to that skill

Selecting a boat should show:

- source island
- destination island
- cargo summary
- linked task or artifact paths
- delivery state

### Timeline Layer

The lower or side panel should show a compact event log in plain language:

- agent activated
- skill used
- boat departed
- boat arrived
- output harvested
- task blocked
- retry started

The timeline should link back to exact artifact paths when possible.

## World Model Mapping

### Islands

An island is the visible body of one working agent.

Minimum visible properties:

- `id`
- `label`
- `role`
- `status`
- `skills`
- `queue_depth`
- `last_event_at`

Rendering defaults:

- `overseer` island sits near the center or in a harbor/town-hall role
- worker islands orbit around it by responsibility
- blocked islands look visibly stalled
- busy islands show local motion without becoming visually noisy

### Crops

Crops represent skills, not goods in the abstract.

Recommended mapping:

- planted field = skill is available on that island
- growing crop = skill is being prepared or used
- ripe crop = skill produced a useful output
- blighted crop = recent failure, bad output, or blocked dependency
- harvested field = output was delivered and the skill is idle again

Do not create one generic crop sprite for everything. Skills should eventually cluster into readable crop families by function, but the first pass can use one crop style plus labels.

### Boats

Boats are the visible form of communication and dependency flow.

Recommended mapping:

- departure = agent starts a handoff
- cargo = task brief, request, output, or artifact bundle
- travel = in-flight work between agents
- docking = delivery acknowledged
- stranded boat = blocked handoff or unresolved dependency

The first pass should treat boats as short-lived event carriers, not a full economic shipping simulation.

### Ports And Warehouses

Ports and warehouses are where abstract agent state becomes inspectable.

Use them to surface:

- inbox
- outbox
- pending artifacts
- recent outputs
- linked run or log paths

## Minimum Data Contract

The external browser game should not call into Molt internals directly. It should consume exported JSON.

### `farm-state.json`

This is the current world snapshot.

Minimum shape:

```json
{
  "farm_id": "local-dev",
  "generated_at": "2026-04-10T12:00:00",
  "mode": "replay",
  "agents": [
    {
      "id": "overseer",
      "label": "Overseer",
      "role": "coordinator",
      "status": "active",
      "skills": [
        {"id": "fishbowl-overseer", "state": "growing"}
      ],
      "queue_depth": 1,
      "last_event_at": "2026-04-10T12:00:00"
    }
  ],
  "routes": [
    {"id": "route-overseer-shipwright", "from": "overseer", "to": "shipwright"}
  ],
  "artifacts": [
    {"path": "runs/run-20260410061727-a4e8078c.json", "kind": "run"}
  ]
}
```

### `farm-events.jsonl`

This is the replay or live event stream.

Minimum event types:

- `agent_started`
- `skill_activated`
- `handoff_departed`
- `handoff_arrived`
- `artifact_produced`
- `agent_blocked`
- `agent_recovered`

Minimum event shape:

```json
{
  "at": "2026-04-10T12:00:03",
  "type": "handoff_departed",
  "source_agent": "overseer",
  "target_agent": "shipwright",
  "skill_id": "fishbowl-overseer",
  "summary": "Delegated first playable slice bootstrap.",
  "artifact_paths": ["fishbowl/journal/backlog.md"]
}
```

## Build Phases

### Phase 1: Visual Spec And Static Slice

Goal:

- prove the metaphor reads clearly before live integration

Deliver:

- one map screen
- 3 to 4 islands
- labeled fields per island
- one or two boat routes
- selection inspector
- timeline panel
- fixture-backed `farm-state.json` and `farm-events.jsonl`

Stop when:

- a viewer can infer island = agent, crop = skill, boat = handoff without explanation

### Phase 2: Replay A Real Molt Run

Goal:

- make the world driven by real Molt evidence instead of hand-authored fiction

Deliver:

- one adapter that converts a real run or small run set into the state and event contract
- replay controls: play, pause, scrub, reset
- direct links from inspectors to real artifact paths

Suggested first source signals:

- run record summary
- trace items such as `function_call:activate_skill:*`
- generated logs

Stop when:

- one real Molt run can be replayed start to finish in the browser

### Phase 3: Live Fishbowl Feed

Goal:

- watch an active Molt Farm while it runs

Deliver:

- a local adapter process that emits fresh state and events
- polling or local socket updates into the browser game
- visible busy, blocked, idle, and delivery transitions

Stop when:

- the browser shows state changes during a live run without manual file refresh

### Phase 4: Richer Farm Semantics

Goal:

- deepen the metaphor only after the core instrumentation works

Possible additions:

- storage limits or clutter for overloaded agents
- weather or sea state for uncertainty or degraded model performance
- crop families for different skill types
- route quality based on repeated successful handoffs

Do not start here.

## Initial External Repo Shape

The external repo should start as a small browser app, not a full simulation engine.

Recommended first modules:

- `src/world/` for island, field, and boat rendering
- `src/data/` for loading fixture or replay files
- `src/inspectors/` for selected island, crop, and boat details
- `src/timeline/` for the event rail
- `fixtures/` for `farm-state.json` and `farm-events.jsonl`

## Acceptance Signals

The plan is working when:

- the metaphor explains real agent behavior instead of hiding it
- a viewer can trace a boat trip to a real handoff or artifact path
- a field's crop state explains a real skill condition
- the browser can replay at least one real Molt run
- the end result feels like instrumentation with game language, not a fake economy pasted over logs

## Defaults For The Next Build Pass

- Build the first external repo as a browser app.
- Use replay fixtures before live data.
- Start with the four existing fishbowl agents.
- Prefer readability over simulation depth.
- Treat the first game slice as an observability surface wearing 1602 clothes.
