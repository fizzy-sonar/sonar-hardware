---
id: D005
title: Host link: gigabit Ethernet, raw UDP streaming
status: superseded by D012
date: 2026-08-25
author: claude (fable) — architecture review
---
## Decision
Stream raw samples over the i5's GbE PHY via LiteEth UDP. USB-C on the board remains power-only.

## Why
24 ch × 16 b × 192–450 kHz = 74–173 Mb/s — trivial for GbE, no USB driver work, long cables, laptop side is a USB-C↔GbE dongle.

## Consequences / what this forecloses
No USB data path on v1; don't route USB-C D±.
