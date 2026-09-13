# Watcher artifacts

Machine-readable, generated. Do not hand-edit as if they were product source.

| file | purpose |
| --- | --- |
| `active-tasks.json` | current lane owners and write locks |
| `recursive-health.json` | RLH canary / halt / replay health |
| `integration-queue.json` | accepted work waiting to merge |
| `regressions.json` | open process failures |
| `model-promotions.json` | empty in v1 harness wave |

Schema notes live in `wiki/Recursive-Watcher-Protocol.md`.
