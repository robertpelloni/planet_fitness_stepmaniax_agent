# Memory

## Core Vision & Progress
The repository is currently in **Phase 4: Scaling & Infrastructure Hardening (v4.2.0)**.
The primary goal is the complete automation of a B2B sales pipeline for Planet Fitness, while maintaining a robust production-grade management platform for pilots.

## Architectural Observations
- **Blueprint Architecture (v4.2.0):** The application is fully modularized into Blueprints (`auth`, `admin`, `staff`, `member`, `api`). This decoupling prevents `app.py` from becoming a bottleneck and clarifies role-based boundaries.
- **Security First:** Security is a first-class citizen with persistent audit logging (`AuditLog`), brute-force protection, and a dedicated Security Intelligence dashboard.
- **Analytical Propensity:** The lead scoring engine in `analytics.py` is the "brain" of the sales pipeline, now factoring in real-world pilot engagement and sentiment.
- **Multi-Tenant Isolation:** Data is strictly isolated by `franchise_id` across all dashboards and APIs.

## Key Design Patterns
- **Gateway Adapter:** Used for payment processing to allow provider swapping without logic changes.
- **Decorator-Based RBAC:** Role and permission enforcement are centralized in `blueprints/decorators.py`.
- **Hybrid Auth:** Supports both user sessions (OIDC-like) and Machine-to-Machine API Keys.

## Future Focus
- Hardening the autonomous outreach engine.
- Expanding real-time telemetry analytics.
- Automating the generation of high-fidelity B2B marketing assets based on real pilot data.
