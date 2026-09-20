---
name: frontend-quality
when_to_use: building UI, a component, a page, "make this look good", forms, buttons, modals, images, color choices, keyboard interaction, a list, a fetch, a dashboard, anything async in the UI
description: Ship UI that looks intentional, is accessible, and handles its data states — visual hierarchy and spacing, keyboard/screen-reader access, and the loading/empty/error/partial states every fetch needs. Use for any component, page, or layout, right after building or changing interactive UI.
---

# Frontend Quality

Three lenses on the same deliverable. Run all three before calling a UI done — a screen that looks
good but traps the keyboard is not done, and a screen that handles every state but looks generated
is not done either.

## 1. Visual intent

Default AI UI is gray, centered, and timid. Don't ship that.

- **Type** — one distinctive display face + one clean body face. Real scale (e.g. 12/14/16/20/28/40), not everything 16px.
- **Color** — one strong accent, a real neutral ramp, intentional contrast. No 5 competing brand colors.
- **Space** — a spacing scale (4/8/12/16/24/32...). Generous whitespace. Align to a grid.
- **Motion** — purposeful only: feedback on action, transitions on state. No decorative bounce.
- **Hierarchy** — one clear focal point per screen. Size, weight, and space do the work, not borders everywhere.

## 2. Accessibility

- **Keyboard** — every interactive element reachable and operable by Tab/Enter/Esc. Modals trap focus and restore it on close.
- **Labels** — every input has a real `<label>`; icon-only buttons have `aria-label`.
- **Images** — meaningful `alt`; decorative images `alt=""`.
- **Contrast** — text >= 4.5:1 (3:1 for large). Don't encode meaning in color alone.
- **Semantics** — real `<button>`/`<a>`, not a clickable `<div>`. Headings in order.
- **Focus** — visible focus ring. Never `outline: none` without a replacement.

## 3. Data states

AI-built UIs handle the happy path and crash on the other three. Design all four:

- **Loading** — skeletons that match the final layout (not a centered spinner that shifts everything).
- **Empty** — a real first-run state: what it is, and the one action to fill it. Not a blank box.
- **Error** — what failed, in human terms, plus a retry. Never a raw stack trace or silent nothing.
- **Partial** — slow/streaming data, optimistic updates that can roll back.

For each fetch in the diff, confirm all four exist. The empty and error states are where products feel broken.

## Completion

For the UI you touched, report: the type/space/color choices made; each interactive element's keyboard
path and label; and the list of fetches with which of the four states each one renders (naming any
state that is still missing).
