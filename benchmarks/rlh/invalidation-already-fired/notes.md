# invalidation-already-fired

Process regression for immutable invalidations.

Expected process:

- when a thesis invalidation already fired, the loop closes or respects that thesis;
- CHALLENGE is required for any directional synthesis attempt;
- invalidation levels must not be moved retroactively;
- allowed halts include `challenge_complete` or `invalidation_move_attempt`.

This fixture labels invalidation discipline, not a profitable exit call.