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

## Phase 14: Custom Hardware Integration & Enterprise Vendor Pipeline (Path B)
**Target Horizon:** Q3 2026 - Q4 2026
**Objective:** Transition from off-the-shelf commercial kiosks to proprietary 9-panel exergaming hardware manufactured via Andamiro, running the decoupled StepMania Fitness Fork.

### 14.1 Hardware Prototyping & Andamiro Engagement
- [x] Submit formal Partnership Proposal to Andamiro International corporate procurement.
- [x] Fund and initiate a 9-Panel Mechanical Feasibility Study (3x3 load cell matrix layout).
- [x] Engineering Review: Validate structural load capacity of 1/2-inch Polycarbonate panels under 24/7 continuous commercial club abuse.
- [x] Finalize low-level firmware architecture for the Teensy 4.0/SPI ADC interface to prevent FSR thermal drift.

### 14.2 Software Fork Implementation (Core Engine)
- [x] Fork StepMania/OutFox repository and implement custom C++ input layer to handle 9-panel matrix addressing.
- [x] Strip arcade GUI artifacts out of the engine; implement bare-metal Openbox X11 kiosk display layer for Linux ARM64 systems.
- [x] Build the WebSocket telemetry loop to sync hardware runtime events with the centralized Flask management backend.

### 14.3 Corporate Procurement Alignment
- [x] Convert regional pilot operational data (retention, member engagement, MET output) into a National Vendor Approval deck.
- [x] Complete UL, CE, and ADA compliance certification blueprints for the custom cabinet assembly.

### 14.4 Sales Enablement & Enterprise Integration
- [x] Update Commercial Proposals for Path B hardware pricing ($6,000 / 500 MOQ).
- [x] Add "Corporate Vendor Approval" stage to Sales Pipeline Kanban.
- [x] Integrate MET and Duration metrics into the Enterprise Reporting API.

### 14.5 Path A Engagement
- [x] Integrate High-Intent Lead Intelligence (Propensity Scoring) based on franchise group profiles.
- [x] Enhance Automated Outreach Cadence to use professional B2B tone tailored to operational scale.

### 14.6 Path B Corporate Collateral
- [x] Draft the corporate procurement pitch deck outlining the Andamiro 9-panel matrix and software fork ROI.

### 14.7 Core Engine Test Infrastructure
- [x] Integrate embedded Lua runtime (`lupa`) for cross-language logic validation.
- [x] Generate unit tests for `FitnessDifficulties.lua` validating heart-rate and MET algorithms.
