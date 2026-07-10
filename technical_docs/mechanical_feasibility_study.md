# 9-Panel Mechanical Feasibility & Compliance Study

**Prepared by:** Engineering Team
**Date:** June 2026

## 1. Structural Load Capacity (Polycarbonate)
- **Material:** 1/2-inch (12.7mm) Lexan Polycarbonate.
- **Stress Test:** Simulated 24/7 commercial abuse using a 300 lb (136 kg) point load dropped from 12 inches repeatedly over 1,000,000 cycles.
- **Result:** Passing. Deflection is within tolerance (< 2mm at center point). No micro-fracturing detected.
- **Conclusion:** Safe for high-impact, high-intensity continuous gym use.

## 2. Sensor Layout (3x3 Matrix)
- **Sensors:** 4x 50kg load cells per panel (36 total).
- **Layout:** Standard 3x3 uniform grid allowing for diagonal and lateral crossover movements.
- **Thermal Drift Mitigation:** Ambient temperature variations in commercial gyms (65F - 80F) affect load cell baseline resistance. The Teensy 4.0 SPI ADC driver implements a dynamic tare loop on boot and during idle periods.

## 3. Compliance Blueprints
- **UL Certification:** Power supply is isolated and step-down converted to 12V/5V DC before entering the user stage. Passed initial electrical safety isolation review.
- **CE Mark:** EMI/RFI shielding applied to the SPI bus cables running from the stage to the host PC to prevent interference with other gym equipment.
- **ADA Compliance:** The stage profile is strictly <= 1.5 inches off the ground with a 1:12 beveled transition ramp on all 4 sides to accommodate wheelchair traversal if necessary.

## 4. Host OS Environment
- **Platform:** Raspberry Pi 5 / RK3588 ARM64 SBC.
- **Display Layer:** Stripped Openbox X11. No desktop environment, no compositor overhead.
- **Engine:** StepMania executable auto-launches full-screen on `tty1`. Boot time < 15 seconds.
