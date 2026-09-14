# Sonar Vivado compute comparison — 2026-09-14

This compares prospective hosts for the first Cmod implementation and later
iterations. No service has been provisioned or tested with Vivado. Pricing is
USD before tax, additional network charges and optional services.

## Planning assumptions

- One job at a time, 4 vCPUs, 8 GiB RAM, no GPU. Modal describes one physical
  core as two vCPUs, so its comparison uses two physical cores. Equal allocation
  is not proof of equal performance across hosts.
- 100 GiB persistent storage for a selective Vivado installation, sources and
  reports. This is headroom, not a measured installation size. Avoid the full
  all-device offline installer. Linode's selected plan includes 160 GB.
- 20 billed compute hours: an allowance of 30 build/debug iterations at 30
  minutes plus 5 hours for installation and setup. This is an intentionally
  generous planning budget, not a measured compile time for our small FPGA.
- Scenario A retains the environment for 72 hours, then removes it after
  copying results. Scenario B retains it for a 730-hour month. Both have the
  same 20 compute hours. Sandbox compute is stopped outside those hours;
  storage stays allocated unless explicitly archived.
- Credits shown assume they are available to this account and not already
  consumed. A credit grant does not automatically increase storage quotas.

## Calculated costs

| Provider / configuration | 72-hour sprint | Month of intermittent use | Credit / access implications |
|---|---:|---:|---|
| [Linode shared 8 GB](https://www.akamai.com/cloud/pricing) | $5.18 | $48.00 | 4 vCPU / 8 GB / 160 GB included; no assumed promotion. Charges continue while powered off. |
| [Modal Sandbox, Starter](https://modal.com/pricing) | $0 with monthly credit; $9.52 usage | $0 with monthly credit; $9.52 usage | $30/month compute included. Model uses a persistent Volume within the published first 1 TiB free allowance, not a separately charged snapshot strategy. |
| [Daytona](https://www.daytona.io/pricing) | $7.36 before introductory credit | $14.11 before introductory credit | Advertises $200 trial compute credit. Storage above free-tier quota needs Tier 2: linked card and $25 wallet top-up; this is prepaid balance, not an extra monthly subscription. Confirm credit coverage for storage. |
| [Dedalus Machines Pro](https://www.dedaluslabs.ai/pricing) | $20.72 conservative estimate | $27.30 conservative estimate | Includes one $20 subscription month and its $20 compute credit. If that credit also covers storage, both estimates become $20. Hobby's 10 GiB hard cap does not fit this plan. |

The Dedalus estimates use its FAQ's $0.0001/GiB-hour storage rate. Its headline
labels storage as $0.073/GiB-hour, inconsistent with the FAQ/calculator. Confirm
the rate and whether Pro credit covers storage before treating this as a quote.
"Unlimited storage" is a quota statement, not a reliable promise of free disk.

Daytona's [quota rules](https://www.daytona.io/docs/limits) list 30 GiB for Tier
1 and 300 GiB for Tier 2. Its
[billing rules](https://www.daytona.io/docs/en/billing/) charge disk while
stopped, but archived **container** sandboxes are unbilled. Archiving between
jobs could lower the modeled month to about $6.83, plus transition time, if
only 20 hours of disk are billable. VM sandboxes do not have that archive state.
The $200 promotion does not establish a zero-cash path around the $25 top-up.

Modal's standard Function rate is lower than its Sandbox rate. Packaging the
build as a Function would cost about $3.17 for the same nominal 20 hours before
the monthly credit. That requires a container/Volume setup for Vivado and is a
later automation option. The official
[Sandbox lifecycle](https://modal.com/docs/guide/sandboxes) permits up to 24
hours when explicitly configured; the default is only five minutes. CPU/RAM
billing can use actual consumption above requests, so cap resources and measure
the first run. Persistent image/Volume setup and AMD licensing remain to test.

For a single uninterrupted 20-hour Linode allocation, deleting it immediately
after the work would cost $1.44. The $5.18 sprint budget accounts for leaving it
available across three days. Export results first; shutdown alone does not end
[Linode billing](https://techdocs.akamai.com/cloud-computing/docs/understanding-how-billing-works).

## Arithmetic

Rates checked on the linked provider pages:

```text
Dedalus CPU+RAM / h = 4*0.04536 + 8*0.01458 = 0.29808
Daytona CPU+RAM / h = 4*0.0504 + 8*0.0162 = 0.3312
Modal Sandbox / h  = (2*0.00003942 + 8*0.00000667)*3600 = 0.47592
Modal Function / h = (2*0.0000131 + 8*0.00000222)*3600 = 0.158256

Dedalus Pro = 20 + max(0, 20*0.29808 - 20) + 100*0.0001*retained_hours
Daytona     = 20*0.3312 + (100-5)*0.000108*retained_hours
Modal       = max(0, 20*0.47592 - 30), with included Volume allowance
Linode      = min(0.072*retained_hours, 48), one monthly billing period
```

## Recommendation and other credits

Use a short-lived Linode for the first diagnostic build if the priority is
getting actual Vivado evidence with little setup work. Modal is the strongest
recurring-price candidate if its installation/licensing works for this project;
its standard monthly credit covers this budget. Run one small real build before
investing in a reusable automated environment on any sandbox service.

Dedalus is worth a short student-project email because a persistent engineering
toolchain is a relevant workload for its Machines product. Ask for access and
storage as well as compute credit. Its
[current Machines reference](https://docs.dedaluslabs.ai/llms.txt) says access
may require beta admission and sleep preserves the root filesystem but not
processes, memory or `/tmp`. Marketing claims about persistent runtime should
not be used to assume an in-flight Vivado build survives sleep. The provider's
CPU architecture, Ubuntu compatibility, licensing behavior and active-job
timeout policy remain unconfirmed.

[Azure for Students](https://azure.microsoft.com/en-us/free/students) offers
eligible students $100 for 12 months without a card, including access to VMs.
That is another promising ordinary-VM route; this comparison does not invent a
region/SKU quote or assume the user's eligibility/VM quota has been approved.

[E2B](https://e2b.dev/pricing) is a weaker fit on its published plans: Hobby
has $100 one-time credit but 10 GiB disk and one-hour sessions; Pro is $150/month
before usage, with 20 GiB disk and up to 24 hours. Larger storage needs a quote.

Compute cost is unlikely to be the main blocker for the first implementation.
Emailing for credits can happen alongside it; obtaining a grant need not delay
the engineering evidence described in `vivado-validation.md`.

## Email draft — not sent

To: support@dedaluslabs.ai (published on the Dedalus home page)

Subject: Student FPGA project on Dedalus Machines

Hi Dedalus team,

I'm an engineering student at UBC building an FPGA-based ultrasonic sonar
system, using coding agents to develop and test the RTL. I'd like to try
Dedalus Machines for running AMD Vivado from my Apple Silicon Mac. I have
simulation regressions; the next step is synthesis and timing validation.

The workload needs x86-64 Linux compatible with Ubuntu 22.04, about 4 vCPUs,
8–16 GiB RAM, 100 GiB persistent disk, and uninterrupted multi-hour batch jobs.
Would that work on Machines? If so, could you offer student trial access with
the larger storage quota and around $100 in compute credits? Could you also
confirm the storage charges and how active jobs interact with automatic sleep?

Happy to share setup notes and feedback from running an FPGA toolchain on it.

Thanks,
Joshua
