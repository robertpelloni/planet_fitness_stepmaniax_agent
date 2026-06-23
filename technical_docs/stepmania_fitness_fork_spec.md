# StepMania Fitness Fork & 9-Panel Hardware Specification

## 1. Overview
This document outlines the technical requirements for forking StepMania/OutFox to create a bespoke, commercial-grade fitness platform. The goal is to decouple the engine from its arcade origins, implement a proprietary C++ input layer for a custom Andamiro 9-panel matrix, and build a UI/UX optimized exclusively for continuous, heart-rate-driven metabolic conditioning.

## 2. Hardware Input Driver (C++)
The standard arcade input stack is insufficient for the 9-panel commercial hardware. We must implement a low-level driver:
- **Interface:** SPI ADC interface communicating with a Teensy 4.0 microcontroller.
- **Sensors:** 9 independent load cells.
- **Calibration:** Automated auto-calibration loop in firmware to calculate baseline ambient weight (accounting for panel resting weight) and adjust for structural shifting due to temperature/humidity in gyms.
- **Signal Processing:** Hysteresis filtering logic in the input decoder to eliminate sensor chatter and thermal drift during high-velocity 16th-note continuous runs.
- **Output:** Translates raw pressure data into standard step events and estimates MET (Metabolic Equivalent of Task) based on force vectors.

## 3. Core Engine Modifications (StepMania/OutFox Fork)
- **Target OS:** Bare-metal Openbox X11 on Linux ARM64 systems.
- **GUI Purge:** Strip all arcade artifacts (coin slots, grading panels, flashy attract modes).
- **Files to Modify:** Approximately 14 core engine files require patching to support the new 9-panel mapping and completely bypass the standard screen flow.

## 4. UI/UX Layer (Lua)
The interface must resemble high-end commercial gym equipment (e.g., Peloton, Matrix).
- **Auto-Join & Screen Bypass:** Rewrite `ScreenTitleMenu overlay.lua` to immediately auto-join Player 1 and bypass directly to `ScreenSelectMusic`. No arcade start screens.
- **Intensity Mapping:** Implement `Scripts/FitnessDifficulties.lua` to map raw Notes Per Second (NPS) arrays to a standardized 1-10 intensity scale.
- **Active Session HUD:** Display Heart Rate Zones, Elapsed Time, Total Steps, and real-time Caloric Burn (MET-calculated).
- **Post-Game Summary:** Stripped fitness summary actor frame showing aggregate workout data, omitting traditional letter grades (A, B, C, F).

## 5. Telemetry & Enterprise Integration
- **WebSocket Loop:** A real-time WebSocket connection to sync hardware runtime events (steps, HR, session duration) with the centralized Flask CRM management backend (`app.py`).
- **Data Payload:** JSON session upload schema tracking biometric IDs, equipment MAC addresses, and granular performance metrics.
- **Bluetooth HRM:** Integration hooks to pipe real-time Bluetooth Heart Rate Monitor data directly into the StepMania UI layer and out to the telemetry backend.
- **Content Delivery:** OTA (Over-The-Air) chart updates where the machine polls the backend for newly generated "AutoArrow ML" marathon content.
