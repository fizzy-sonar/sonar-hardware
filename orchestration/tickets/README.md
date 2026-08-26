# Tickets

One file per unit of work: `T-xxx-slug.md`. Frontmatter is the state machine:

- `status`: backlog → ready → in-progress → blocked / review → done.
  `ready` means all `depends_on` are done and the phase's entry gate is open.
  `needs_human: true` tickets end at `review`; only Joshua closes them.
- `assignee`: empty until an agent claims it (codex / claude / kimi / …).
- Pick order: lowest `priority` number first among `ready`.

Every ticket needs: Goal, Definition of Done, Verification (real commands),
and an append-only Log. Work without a Log entry didn't happen.
New tickets: next free number, follow TEMPLATE.md. Numbering blocks by phase:
T-0xx = P1, T-01x = P2 (see ROADMAP), T-02x = P5, T-03x = P3, T-04x = P4, T-06x = P6.
