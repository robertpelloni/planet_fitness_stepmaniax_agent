# ROADMAP - StepManiaX B2B Sales Automation

## Phase 12: Scalability & Enterprise Hardening (v5.5.0)
- [x] **Multi-Region Cluster Support:** Implement shard-based data isolation for international franchise expansion (UK, Canada, Mexico). (Completed in v5.9.0)
- [x] **ML-Based Outreach Optimization:** Implement sentiment-aware prioritized outreach to increase Discovery Call conversion rates. (Completed in v5.9.0)
- [x] **Spatial Intelligence:** Integrated Leaflet.js heatmaps and Geolocation APIs for global fleet visualization. (Completed in v6.0.0)
- [x] **Automated Weekly ROI:** Implemented background summary generation for regional managers to track pilot progress. (Completed in v6.1.0)
- [x] **API Access Lists:** Launched IP-based whitelisting for the Enterprise Export API to secure corporate data streams. (Completed in v6.2.0)
- [x] **Biometric Telemetry Ingestion:** Support secure NFC/Biometric member check-ins on SMX units to eliminate manual scan entry. (Completed in v5.2.0)
- [x] **Enterprise Reporting API:** Launch secure REST endpoints for large franchise groups to pull raw engagement data. (Completed in v4.8.0)
- [x] **Automated Service Dispatch:** Integrate with maintenance workflows to automatically trigger work orders for hardware repairs. (Completed in v5.6.0)
- [x] **Internationalization & Pilot Analytics:** Integrated real-time translation and launched the Pilot Success Dashboard. (Completed in v6.3.0)
- [x] **Automated Outreach Cadence:** Launched multi-tier follow-up engine with granular admin controls. (Completed in v6.4.0)
- [x] **High-Intent Lead Intelligence:** Integrated interactive ROI simulator and intent-based propensity scoring. (Completed in v6.5.0)
- [x] **Outreach Orchestration:** Automated background cadence processing and launched manual dispatch controls. (Completed in v6.6.0)
- [x] **Sales Pipeline Kanban:** Integrated a visual, stage-based Sales Pipeline at `/admin/pipeline`. (Completed in v6.7.0)
- [x] **Proposal Automation:** Developed a dynamic commercial proposal generator based on pilot data. (Completed in v6.7.0)
- [x] **Engagement Intelligence:** Launched lead capture on the portal and pulsing intent indicators. (Completed in v6.8.0)
- [x] **Dual-Direction Sync:** Completed the Executive Protocol for full repository synchronization. (Completed in v6.9.0)

## Phase 13: Manufacturer Influence & Content Innovation (v7.8.0)
- [x] **Strategic Content Pitch:** Drafted the "Psytrance Marathon" value proposition and manufacturer-specific letters. (Completed in v7.7.0)
- [x] **AutoArrow ML Prototype:** Developed functional content generator with difficulty-specific quantization and safety validators. (Completed in v7.6.0)
- [x] **Manufacturer Outreach:** Drafted formal outreach letters for Step Revolution, Konami, and Andamiro. (Completed in v7.7.0)
- [x] **Flow-State Analytics:** Researched and documented metabolic benefits of rhythmic cardio. (Completed in v7.2.0)
- [x] **Technical Pilot:** Execute 90-day technical demonstration with a hardware partner. (Documented in `outreach/technical_pilot_plan.md`)

## Phase 14: Custom Hardware Vertical Integration (v9.0.0)
**Target Horizon:** Q3 2026 - Q4 2026
**Objective:** Transition from off-the-shelf commercial kiosks to proprietary 9-panel exergaming hardware manufactured via Andamiro, running the decoupled StepMania Fitness Fork.

### Strategic Foundation (v9.0.0 — Complete)
- [x] **Two-Path Strategic Vision:** Converged regional pilot strategy with custom hardware + corporate engagement path. (Completed in v9.0.0)
- [x] **Andamiro Partnership Proposal:** Drafted formal hardware co-development proposal for custom 9-panel fitness stage. (Completed in v9.0.0)
- [x] **StepMania Fitness Fork Spec:** Released technical specification for 9-panel driver, fitness UI, telemetry pipeline, and OTA content delivery. (Completed in v9.0.0)
- [x] **System Architecture Design:** Documented block diagram, data flows, interface contracts, and integration map for the custom platform. (Completed in v9.0.0)
- [x] **FitnessDifficulty.lua:** Implemented Lua script to translate NPS arrays into standardized 1-10 intensity scale. (Completed in v9.0.0)
- [x] **Test Infrastructure Restored:** Rebuilt missing `test_member_api.py` and centralized conftest with Gunicorn management. (Completed in v9.0.0)

### 14.1 Hardware Prototyping & Andamiro Engagement
- [ ] **Andamiro Engineering Review:** Submit formal Partnership Proposal to Andamiro International corporate procurement and receive preliminary MOQ/tooling estimate.
- [ ] **9-Panel Mechanical Feasibility Study:** Validate 3x3 load cell matrix layout, structural load capacity of panels under 24/7 commercial abuse.
- [ ] **Firmware Architecture:** Finalize low-level firmware for Teensy 4.0 / SPI ADC interface with hysteresis filtering and auto-calibration to prevent sensor drift.
- [ ] **Prototype Build:** 5-unit pilot batch with Andamiro for gym installation and certification testing.

### 14.2 Software Fork Implementation (Core Engine)
- [ ] **9-Panel Input Driver:** Implement standalone C++ SPI ADC hardware driver with auto-calibration loop and hysteresis filtering.
- [ ] **StepMania Fork Build:** Fork StepMania/OutFox, patch engine for 9-panel GameButton support, compile on ARM64 target.
- [ ] **Fitness UI Theme:** Implement all screens (Workout Select, Active Session, Session Summary) with heart-rate zone display, calorie tracking, MET display. Strip arcade GUI artifacts.
- [ ] **Telemetry Pipeline:** Build WebSocket telemetry loop to sync hardware runtime events (session data, step counts, HRM data) with the centralized Flask management backend.
- [ ] **OTA Content Delivery:** Implement content pull pipeline (poll manifest + download + verify new charts from AutoArrow).
- [ ] **AutoArrow 9-Panel Output:** Extend chart generator to output Fitness-Marathon format for 9-panel layout at all 5 difficulty levels.
- [ ] **Bluetooth HRM:** Wire integration hooks to pipe real-time heart-rate monitor data into the StepMania UI layer.

### 14.3 Corporate Procurement Alignment
- [ ] **National Vendor Approval Deck:** Convert regional pilot operational data (retention, member engagement, MET output) into a formal Planet Fitness corporate proposal.
- [ ] **Certification:** Complete UL, CE, and ADA compliance certification blueprints for the custom cabinet assembly.
- [ ] **Corporate-Facing Pitch Deck:** Deliver procurement-ready deck positioning the platform as a new equipment category. (Drafted in `pitch-deck-corporate.md`)
- [ ] **Cold Outreach Campaign:** Deploy automated cold outreach templates to top 3 regional franchise groups to establish Phase 1 pilot baseline. (Strategy in `outreach/cold_outreach_campaign.md`)

## Phase 1: Asset Preparation & Collateral Assembly
- [x] **Secure Manufacturer Alignment:** Obtained official commercial hardware specs and dimensions.
- [x] **Build the Pitch Deck:** Designed B2B presentation focusing on "Gamified HIIT" and member retention.

## Phase 2: Lead Generation & Target Mapping
- [x] **Identify the Local Franchise Powerhouse:** Researched regional Franchise Groups (EPIC Fitness, NFP, OGP, etc.) and documented in `LEADS.md`.
- [x] **Target the Decision-Makers:** Refined contact info, email patterns, and LinkedIn URLs for key executives in `LEADS.md`.

## Phase 3: The Outreach & "Rogue Pilot" Pitch
- [x] **Personalized Collateral:** Developed tailored outreach scripts for priority Michigan targets in `outreach/`.
- [x] **Follow-up Infrastructure:** Established multi-touch follow-up cadence (Day 3, 7, 14) in `outreach/follow-ups.md`.
- [x] **Cold Outreach Campaign:** Initiate contact using optimized templates focusing on a risk-mitigated pilot. (Documented in `outreach/cold_outreach_campaign.md`)
- [x] **Negotiation & Objection Handling:** Drafted `maintenance-slas.md` to address technical and service-level concerns.

## Phase 4: Contract Negotiation & Deal Closure
- [x] **Memorandum of Understanding (MOU):** Drafted 90-day pilot agreement (`pilot-mou.md`).
- [x] **Performance Reporting:** Established `pilot-performance-report.md` for data-driven ROI presentation.
- [x] **The "Land and Expand" Trigger:** Developed `commercial-proposal-template.md` detailing regional procurement models.
