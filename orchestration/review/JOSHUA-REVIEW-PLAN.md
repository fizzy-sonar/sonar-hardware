# Joshua's review plan — 2026-08-26 work batch

Everything below is bite-sized (2–10 min each). Do them in any order; the ones marked
**GATE** block spending money or ordering boards. If anything looks wrong, just tell the
next agent the item number and what you saw — each item names its fix-path.

Background reading (optional): `orchestration/review/REVIEW-2026-08-26.md` (what the
independent reviewer found) and `orchestration/review/FIXES-2026-08-26.md` (what was
already fixed — you do NOT need to re-check those; they were re-verified after fixing).

## Part 1 — Decisions only you can make (~25 min total)

1. **(2 min) GATE — D013 TX transducer default.** Read `orchestration/decisions/D013-tx-default-transducer.md`
   (one page). It proposes: v1 default TX = piezo horn tweeter for 20–32 kHz chirps;
   MA40S4S use gated on item 3. Reply "ratify D013" or edit it. *(Why: the review proved
   duty-chopping can't keep an MA40S4S under a 20 Vpp terminal limit at 12 V.)*
2. **(2 min) Cmod power strategy.** `orchestration/rails.md` — the Cmod is now powered
   from the carrier 5 V through R420 (0R, populated by default; DNP it to self-power
   from module USB). Confirm that's the v1 behavior you want. If unsure: leave as-is.
3. **(10 min) GATE — MA40S4S datasheet, Table 1:** is the 20 Vpp rating a *terminal-voltage*
   limit or a *fundamental-amplitude* limit? Your answer ratifies or kills the MA40S4S
   path in D013. (Reviewer's reading: terminal. If so, MA40S4S needs a lower VM or a
   series element — D013 says how.)
4. **(10 min) DRV8876 datasheet, one sitting, three straps** (closes the remaining CP-C
   TX items): PMODE polarity (high = IN1/IN2 mode?), IMODE=10 Ω-to-GND mode name, and the
   IN1/IN2 truth table (00 = coast, 11 = brake?). Tick them off in `orchestration/tx-limits.md`'s
   CP-C list.
5. **(5 min) GATE — TI CDCLVC1112PWR datasheet vs `BUFFER_PIN_MAP` in
   `coupons/mic-bakeoff/generate_coupon.py`** (pin names/numbers only). T-016 flagged this
   UNVERIFIED from day one and it gates the coupon order. This exact class of lookup already
   produced one correlated-recall failure, so it needs your eyes, not an agent's.
6. **(3 min) Coupon order sanity.** Skim `coupons/mic-bakeoff/docs/order-package.md` —
   quantities were made self-consistent today (all 5 boards/variant assemblable) and the
   bypass cap is now buyable (100 nF X7R 0603). You're looking for anything that surprises
   you before CP-BM.
7. **(5–10 min) GATE — T-007 purchases.** `orchestration/tickets/T-007-buy-now-list.md`:
   pick the reseller, pick mini-PC vs cloud VM for Vivado, place the ~$200 dev order.
   This unblocks the entire hardware path (T-020 bitstream, T-009 physical, CP-BM bench).

## Part 2 — Optional eyeball checks (~15 min if you do them all)

8. **(3 min)** Open `build/sonar-svg/sonar-digital.svg` in a browser. Find J40 (DIP-48):
   pin 24 should be `5V_CMOD` through R420, pin 25 GND, pins 15/16 NC. That corner was
   today's biggest bug; it's satisfying to see it right.
9. **(3 min)** Skim the "Provenance and audit status" section of `orchestration/pinmap.md` —
   it's the honest story of how the offline agents got the pinout wrong and the live fetch
   caught it. Worth knowing before you trust any agent-typed pinout again.
10. **(4 min)** Skim `orchestration/tx-limits.md` — the TX safety envelope with the new
    hard per-half-cycle bound. This is what keeps the transducer alive.
11. **(5 min)** Run `./scripts/check.sh` yourself (unsandboxed) once — confirms the harness
    is green on your machine and re-renders the SVGs in `build/`.

## Part 3 — When purchases/bench data exist (pointers only, nothing to do now)

- **CP-BM**: `coupons/mic-bakeoff/docs/order-package.md` pre-order checklist → order →
  bench per `docs/runbook.md` → ratify MPN (closes T-016, unblocks T-010).
- **Vivado host**: `gateware/README.md` has the two batch commands; append reports to T-020.
- **Unsandboxed DRC**: `kicad-cli pcb drc` SIGABRTs inside agent sandboxes — run it
  yourself after big schematic merges (`./scripts/check.sh` does it).

## What you can safely skip

Everything in `FIXES-2026-08-26.md` (already fixed + re-verified), all of Part 2 if time
is tight, and every journal file. The journals are for the next agent, not for you.
