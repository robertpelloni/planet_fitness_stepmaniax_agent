# Andamiro — Custom Fitness Hardware Partnership Proposal

**Classification:** Strategic Partnership — Hardware Co-Development
**Target:** Andamiro Co., Ltd. — Business Development & Engineering Divisions
**Subject:** Joint Development of a Purpose-Built 9-Panel Commercial Fitness Rhythm Stage

---

## Executive Summary

This proposal requests a co-development partnership between this project and Andamiro to design, engineer, and manufacture a **custom 9-panel rhythm stage purpose-built for the $96B commercial fitness market**.

Rather than adapting existing arcade hardware (PIU Pro/Prime) for gym use, we propose a ground-up fitness-first design: a 9-panel stage with industrial-grade construction, medical-grade materials, and a form factor optimized for continuous 60-120 minute cardio sessions in Planet Fitness and similar commercial gym environments.

Software would be provided by our project — a custom StepMania-based fitness operating system with ML-generated marathon content (the AutoArrow Engine) — creating a vertically integrated solution that no competitor can match.

---

## The Opportunity

### Why Andamiro?
Andamiro has historically been the most experimental of the three major rhythm hardware manufacturers (vs. Konami's conservatism and Step Revolution's niche focus). Pump It Up's 5-panel layout already demonstrated that breaking from the 4-panel standard can create a differentiated experience. A **9-panel fitness stage** would be a genuinely new product category — not a rhythm game, but a purpose-built commercial fitness machine.

Andamiro's existing manufacturing infrastructure (PCB fabrication, load cell sourcing, cabinet assembly, global distribution) gives you a 2-3 year head start on any competitor who might attempt to enter this space.

### The Planet Fitness Addressable Market
- **~2,500 locations** in the US (corporate + franchise)
- **~20 million members**
- Typical cardio floor: 30-60 machines per location
- Even a **2-unit-per-club** placement represents a **5,000-unit hardware order**

This does not include secondary markets (Crunch, EOS, LA Fitness, international) that would open after a Planet Fitness reference deployment.

---

## Hardware Specifications: The 9-Panel Fitness Stage

### Panel Layout
A 9-panel matrix arranged as a 3×3 grid:

```
[UL] [U ] [UR]
[ L ] [C ] [ R ]
[DL] [D ] [DR]
```

**Rationale:** A 3×3 grid provides:
- **Wider stance options** for low-impact lateral movement (reduces repetitive stress vs. 4-panel DDR/SMX layouts)
- **Natural progression** from beginner (center + 4 cardinal directions) to expert (full 9-panel)
- **Biomechanical optimization** for 60+ minute sessions — the center panel allows standing rest without breaking flow, and diagonal panels enable rotational movement patterns that distribute muscle engagement

### Construction
| Component | Specification | Rationale |
|-----------|--------------|-----------|
| Frame | Heavy-duty welded steel, powder-coated | 24/7 commercial operation, 10+ year lifespan |
| Panels | 18″ × 18″ each, tempered glass over LED array | Visibility, durability, weight distribution |
| Sensors | Industrial load cells (500K+ cycle MTBF) | 100x consumer switch lifespan |
| Surface | Non-porous, disinfectant-resistant polymer | Medical-grade hygiene for gym environments |
| Handrails | Integrated adjustable-height support bar | Accessibility for all fitness levels |
| Lighting | Per-panel RGB LED (addressable strips) | Visual feedback, difficulty cues, "flow state" immersion |
| Display | 24″ commercial touchscreen, anti-glare | UI interaction, workout selection, progress display |
| Total footprint | ~72″ W × 72″ D (stage only, excluding display mount) | Fits standard cardio floor bay |

### Electrical
- **Power:** 120V AC, 15A dedicated circuit (standard US gym outlet)
- **Consumption:** <200W peak (LEDs + SBC + display)
- **Connectivity:** Wi-Fi 6 + Ethernet, Bluetooth 5.0 (heart-rate monitor pairing)
- **Audio:** Integrated 30W speaker bar + 3.5mm headphone jack + Bluetooth audio

---

## Software Stack

The project will develop and maintain a custom fitness operating system based on the open-source StepMania engine. Andamiro would not bear software development costs.

### Architecture
```
┌─────────────────────────────────────────┐
│    Fitness UI Layer (HTML5/Webview)      │  ← Workout selection, progress, HR zones
├─────────────────────────────────────────┤
│    StepMania Engine (C++/Lua)            │  ← Chart playback, input, rendering
├─────────────────────────────────────────┤
│    9-Panel Driver Plugin (C++)           │  ← Custom input mapping, LED control
├─────────────────────────────────────────┤
│    Linux SBC (Rockchip/Raspberry Pi CM)  │  ← Low-cost, mass-producible
└─────────────────────────────────────────┘
```

### Key Software Features
- **Workout Mode UI:** Presents sessions as "cardio workouts" not "game rounds" — duration, calories, heart-rate zones, MET score, difficulty level
- **Heart-Rate Integration:** Bluetooth pairing with Polar/Garmin/Apple Watch for real-time zone display and intensity auto-adjustment
- **Marathon Content Library:** 60-minute Psytrance sets at Beginner through Challenge difficulty, generated by the AutoArrow ML Engine
- **Telemetry Upload:** Session data (duration, steps, heart-rate zones, difficulty) sent to the B2B analytics dashboard
- **Remote Management:** OTA updates, content push, health monitoring, usage reports
- **Headphone Mode:** Full silent operation for non-disruptive gym floor integration

---

## Commercial Model

### Proposed Partnership Structure
| Party | Responsibility | Revenue Share |
|-------|---------------|---------------|
| **Andamiro** | Hardware manufacturing, QA, warranty service, global logistics | Hardware COGS + 25% margin |
| **This Project** | Software development, content generation (AutoArrow), sales & marketing, deployment | Per-unit software license + content subscription |

### Pricing Estimate (per unit, at 500-unit scale)
| Component | Estimated Cost |
|-----------|---------------|
| Stage assembly (9 panels + frame + sensors) | $2,800 |
| LED system + controller | $400 |
| Touchscreen display + mounting | $600 |
| SBC + audio + networking | $300 |
| Cabinet/casing + handrails | $500 |
| Assembly + QA | $200 |
| **Hardware BOM (est.)** | **$4,800** |
| Andamiro margin (25%) | $1,200 |
| **Hardware sale price (est.)** | **$6,000** |
| Software license (one-time) | $500 |
| Content subscription (annual) | $200/unit/yr |

**Comparable:** Planet Fitness currently pays $8K-$15K per treadmill unit. A $6.5K all-in-one interactive cardio station is highly competitive.

### Pilot Path to Production
1. **Feasibility Study (8 weeks):** Andamiro engineering reviews 9-panel mechanical design, load cell layout, PCB schematics. Project team delivers prototype 9-panel driver and fitness UI for test.
2. **Prototype Batch (12-16 weeks):** 5 units manufactured at Andamiro's facility. 3 for gym pilot installations, 2 for internal testing/ certification.
3. **Certification (8 weeks):** UL/CSA/CE safety certification, FCC/CE emissions, ADA compliance review.
4. **Production Run (8 weeks after PO):** First production batch of 100-500 units.

---

## Next Steps

We request a preliminary engineering review with Andamiro's hardware team to assess:
1. Feasibility of the 9-panel load cell matrix within existing manufacturing processes
2. Estimated tooling costs for a custom panel mold
3. MOQ for initial prototype and production runs
4. Timeline availability for a joint development project

We are prepared to share our full technical specifications, software prototype, and a list of pre-committed pilot locations.

---

**Contact:** [Autonomous Sales Agent]
**Project:** StepManiaX B2B Platform — Fitness Hardware Division
**Status:** Proposal Draft — Awaiting Engineering Feasibility Review
