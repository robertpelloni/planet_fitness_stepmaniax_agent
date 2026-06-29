# Memory

## Architectural Observations
- The project follows a hybrid approach: Markdown for B2B collateral and Python for lead generation.
- The "Rogue Franchise Loophole" is the core strategic driver, targeting regional decision-makers instead of corporate.
- Tone management is critical; strict avoidance of "arcade/gaming" terms in favor of "gamified HIIT/retention".
- Advanced security features including TOTP-based MFA and per-user API key management are now standard (v5.3.0).
- Telemetry history and hardware integration (NFC/Biometric) support detailed engagement tracking (v5.2.0).

## Discovered Traits
- Franchise Groups often have their own websites separate from the main Planet Fitness corporate site, which provides a more direct path to executive information.
- LinkedIn Sales Navigator is a primary blocker for automated executive contact extraction, requiring manual or semi-automated workarounds.

## Design Preferences
- Maintain a professional, B2B, corporate fitness tone.
- Use `VERSION.md` as the single source of truth for versioning.
- Prefer explicit documentation over complex, un-commented code.
- Prioritize multi-tenant isolation and granular RBAC for franchise safety.
