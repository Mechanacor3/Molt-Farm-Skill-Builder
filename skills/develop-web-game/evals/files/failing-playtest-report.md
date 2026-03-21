# Playtest Report

Game: dodge-the-boxes

Observed in browser:
- the player square moves, but the first obstacle can spawn directly on top of the player
- score increments twice during some collisions
- restart works with the button but not with the `R` key
- there is no clear visual feedback when the run ends

Console:
- no fatal errors
- one repeated warning about reading `undefined` from a score label during reset

Desired next step:
- improve the game without turning this into a full visual redesign
