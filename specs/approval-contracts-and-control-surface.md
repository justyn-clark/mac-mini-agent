# Approval Contracts and Control Surface Tightening

## Goal

Unify dangerous-action approvals across the terminal and GUI surfaces before expanding capability breadth.

Sequence:
1. Push current work
2. Unify approval contracts
3. Add tmux discovery primitives
4. Expand macOS controls from inspect to tightly-scoped act primitives

## Approval contract shape

Shared fields:

```json
{
  "id": "8f2c1a90b3e4d5f6",
  "action": "proc.kill",
  "target": "pid:12345",
  "created_at": 1760000000,
  "expires_at": 1760000300,
  "revoked_at": null,
  "max_uses": 1,
  "uses": 0,
  "uses_remaining": 1,
  "single_use": true,
  "metadata": {}
}
```

Semantics:
- expiry: contract becomes invalid after `expires_at`
- revocation: `revoked_at` makes the contract unusable immediately
- single-use: `max_uses=1`
- bounded multi-use: `max_uses=N`
- action-target binding: a contract for `proc.kill pid:12345` cannot be reused for another action or target

## Initial integration

Drive consumes approval contracts first because it already owns the highest-risk terminal lifecycle operations.

Phase 1 integrations:
- `drive proc kill --approval <id>`
- `drive session kill --approval <id>`
- `drive approval issue|show|list|revoke`

## Tmux discovery primitives

Agents need a read-only discovery layer before they steer more aggressively.

New primitive:
- `drive session inspect <name> --json`

Returns:
- session metadata
- window list
- pane list per window
- pane PID
- active command
- current working directory

This is intentionally discovery-first. It lets an agent answer:
- what windows exist?
- which pane is active?
- what PID backs this pane?
- what cwd is the process actually running in?

## macOS controls: inspect vs act

Steer should remain capability-oriented rather than introducing a broad "do anything" control surface.

Inspect primitives:
- `see`
- `ocr`
- `find`
- `focus`
- `wait`
- `screens`

Tightly-scoped act primitives:
- `click`
- `type`
- `hotkey`
- `scroll`
- `drag`
- `apps activate|launch`
- `window move|resize|minimize|restore|fullscreen|close`
- `clipboard write`

Guardrail:
- prefer specific verbs over a generic act RPC
- bind destructive actions to explicit approvals where the surface justifies it
- keep inspect and act separable so plans can do observe, decide, act, verify
