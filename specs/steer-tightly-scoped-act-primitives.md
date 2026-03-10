# Steer Tightly-Scoped Act Primitive Expansion

## Goal

Expand the macOS control surface carefully, without collapsing into a generic act RPC.

## Principle

Prefer explicit verbs with narrow blast radius.

Good:
- `steer apps hide Safari`
- `steer apps quit Safari --approval <id>`
- `steer window close Safari --approval <id>`
- `steer hotkey cmd+q --approval <id>`
- `steer clipboard write "text" --approval <id>`

Bad:
- `steer act '{"kind":"anything","payload":...}'`
- opaque multi-step macros without inspect/verify boundaries

## Additions in this pass

### App actions
- `apps hide <app>`
- `apps unhide <app>`
- `apps quit <app> --approval <id>`
- `apps force-quit <app> --approval <id>`

### Gated stronger actions
- `window close <app> --approval <id>`
- `clipboard write ... --approval <id>`
- `hotkey cmd+q|cmd+w|cmd+shift+q --approval <id>`

## Approval bindings

Action to target bindings:
- `steer.apps.quit` -> `app:<name>`
- `steer.apps.force-quit` -> `app:<name>`
- `steer.window.close` -> `app:<name>`
- `steer.clipboard.write-text` -> `clipboard:text`
- `steer.clipboard.write-image` -> `clipboard:image`
- `steer.hotkey` -> `combo:<normalized-combo>`

## Why this is safer

- inspect and act remain separable
- stronger actions have explicit intent and target scope
- approval contracts can expire, be revoked, and remain single-use
- higher-level agents can compose actions without gaining an unbounded control primitive
