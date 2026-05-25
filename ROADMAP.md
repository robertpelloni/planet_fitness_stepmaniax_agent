# Roadmap

This roadmap outlines the major long-term plans to successfully pitch and place StepManiaX units in Planet Fitness locations via regional franchisees.

## Phase 1: Asset Preparation & Collateral Assembly
- [x] **Secure Manufacturer Alignment:** Obtained official commercial hardware specs and dimensions.
- [x] **Build the Pitch Deck:** Designed B2B presentation focusing on "Gamified HIIT" and member retention.

## Phase 2: Lead Generation & Target Mapping
- [x] **Identify the Local Franchise Powerhouse:** Expanded research to 11 major regional Franchise Groups (Flynn Group, CDM, ECP-PF, etc.) in `LEADS.md`.
- [x] **Target the Decision-Makers:** Refined contact info, email patterns, and LinkedIn URLs for key executives in `LEADS.md`.

## Phase 3: The Outreach & "Rogue Pilot" Pitch
- [x] **Personalized Collateral:** Developed tailored outreach scripts for priority Michigan targets in `outreach/`.
- [x] **Follow-up Automation:** Launched `cadence_trigger.py` for automated cadence management.
- [x] **Outreach Persistence:** Implemented follow-up tracking and automated counters in CRM.
- [x] **CRM Database Architecture:** Migrated lead tracking to SQLite for scalable operations.
- [x] **Automation:** Enhanced `generate_personalized_assets.py` for dynamic email and pitch deck generation from CRM DB.
- [x] **Follow-up Infrastructure:** Established multi-touch follow-up cadence (Day 3, 7, 14) in `outreach/follow-ups.md`.
- [x] **Cold Outreach Campaign:** Initiated first wave of contact templates and campaign launch tooling.
- [x] **Negotiation & Objection Handling:** Drafted `maintenance-slas.md` to address technical and service-level concerns.

## Phase 4: Contract Negotiation & Deal Closure
- [x] **Live Monitoring:** Launched multi-tenant web dashboard and Webhook notification system.
- [x] **Memorandum of Understanding (MOU):** Drafted 90-day pilot agreement (`pilot-mou.md`).
- [x] **Performance Reporting:** Established automated reporting via `report_generator.py` for data-driven ROI presentation.
- [x] **Expansion Methodology:** Formalized `regional-expansion-strategy.md` for portfolio-wide scaling.
- [x] **Member Lifecycle Integration:** Launched member onboarding workflow and retention-scaled analytics.
- [x] **Operational Readiness:** Developed `staff-training-manual.md` for club-level onboarding.
- [x] **The "Land and Expand" Trigger:** Developed `commercial-proposal-template.md` detailing regional procurement models.

## Phase 5: Operations & Multi-Tenant Infrastructure
- [x] **Multi-Tenant Management Dashboard:** Launched high-visibility dashboards for Global Admins, Franchisees, and Club Staff.
- [x] **Real-time Facility Monitoring:** Implemented HTMX-powered staff portal for asynchronous status updates and maintenance alerting.
- [x] **Historical Usage Analytics:** Developed time-series data ingestion and 7-day trend visualization for member engagement.

## Phase 6: Security & Deployment Readiness
- [x] **Enterprise-Grade RBAC:** Hardened platform security with granular Role-Based Access Control and secure User Management UI.
- [x] **Programmatic API Security:** Implemented dual-mode authentication (Session/API Key) for telemetry and management REST endpoints.
- [x] **Production Deployment Stack:** Established Gunicorn/Systemd infrastructure and automated readiness checks for 24/7 operations.

## Phase 7: Facility Operations & UI Standardization
- [x] **Unified Design System:** Standardized all dashboards (Admin, Staff, Member, Prospect) with a master Tailwind-based UI architecture.
- [x] **Live Operational Monitoring:** Launched the Facility Operations Center for sub-5-minute heartbeat tracking and reservation monitoring.
- [x] **Operational Security Audit:** Integrated 'last_login' and 'last_heartbeat' persistent audit trails.
- [x] **Advanced Usage Intelligence:** Deployed hourly peak-usage distribution models and member-engagement propensity scoring.
- [x] **Security Hardening Milestone:** Implemented account lockout policies, persistent audit logging, and secure password rotation. (v3.5.0)
- [x] **Strategic Optimization Milestone:** Deployed automated lifecycle recommendations and usage intensity tracking. (v3.6.0)
- [x] **Predictive Maintenance Milestone:** Launched the stability scoring engine and integrated predictive health into dashboards. (v3.7.0)
- [x] **Lead Engagement Milestone:** Deployed real-time intent tracking and engagement-based propensity scoring. (v3.8.0)
- [x] **Autonomous Background Engine Milestone:** Launched centralized heartbeat monitoring and management efficiency dashboards. (v3.9.0)
- [x] **Commerce & Sentiment Milestone:** Integrated automated payment gateways and pilot feedback dashboards. (v3.9.2)
- [x] **Enterprise Security Milestone:** Launched granular RBAC and sub-role permission management. (v4.0.0)

## Phase 8: Scaling & Predictive Intelligence
- [x] **Predictive Maintenance Engine:** Transition from reactive alerts to ML-based failure prediction.
- [x] **Automated ROI Reporting for Leads:** Dynamic, self-service ROI dashboards for prospective franchisees.
- [ ] **Regional Fleet Orchestration:** Centralized control for multi-club hardware deployment and rotation.
