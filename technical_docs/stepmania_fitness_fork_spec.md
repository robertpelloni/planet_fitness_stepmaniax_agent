# Technical Specification: StepMania Fitness Fork + 9-Panel Driver

**Version:** 1.0.0
**Status:** Preliminary Design
**Target Platform:** Custom Andamiro 9-Panel Fitness Stage (Linux SBC)

---

## 1. Overview

This document specifies the technical architecture for a **StepMania-based fitness operating system** to run on a custom 9-panel rhythm stage co-developed with Andamiro. The fork replaces the arcade gaming paradigm with a commercial fitness paradigm while retaining StepMania's proven chart playback engine, input system, and rendering pipeline.

### 1.1 Guiding Principles
- **Fitness-first, not arcade-first:** The user experience must present the machine as a piece of cardio equipment, not a video game.
- **Zero arcade terminology:** No "songs," "stages," "lives," "scores." Use "workouts," "sessions," "duration," "intensity level," "calories."
- **Persistent telemetry:** Every session uploads to the B2B analytics backend for retention tracking and ROI reporting.
- **Content decoupling:** Chart content is delivered as data (not built into the binary), enabling OTA updates, ML-generated content pushes, and difficulty-curve adjustments without firmware updates.

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Fitness UI Layer                       │
│  (Qt QML / WebView — renders workout UI, not game UI)    │
├─────────────────────────────────────────────────────────┤
│                    StepMania Engine                       │
│  (Chart playback, audio rendering, 3D stage rendering)    │
├─────────────────────────────────────────────────────────┤
│                  Input Abstraction Layer                  │
│  (9-panel driver, Bluetooth HRM, touchscreen, service)    │
├─────────────────────────────────────────────────────────┤
│              Telemetry & Sync Backend                     │
│  (Session upload, content download, health checks)        │
├─────────────────────────────────────────────────────────┤
│              Linux SBC Operating System                   │
│  (Ubuntu Server / Raspberry Pi OS, stripped to minimum)   │
└─────────────────────────────────────────────────────────┘
```

### 2.1 Platform Choices

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| SBC | Raspberry Pi CM5 / Rockchip RK3588 | Low-cost ($80-150), mass-producible, hardware video decode |
| OS | Ubuntu Server 24.04 LTS (minimal) | Long-term support, real-time kernel available |
| Display server | Weston (Wayland compositor) | Kiosk-mode, no desktop overhead |
| UI framework | Qt 6 + QML | Hardware-accelerated, native performance, custom skinning |
| StepMania base | StepMania 5.1.x (etterna fork base) | Most stable, well-documented input/theme API |
| ML integration | External (charts generated offline, pushed via OTA) | GPU not required on-unit; generation is server-side |
| Sync | HTTPS REST + WebSocket | Simple, firewall-friendly, existing backend compatibility |

---

## 3. 9-Panel Input Driver

### 3.1 Panel Mapping

Nine panels mapped as a 3×3 grid:

```
  Column 0    Column 1    Column 2
┌──────────┬──────────┬──────────┐
│  UL (0)  │  U  (1)  │  UR (2)  │  Row 0
├──────────┼──────────┼──────────┤
│   L (3)  │  C  (4)  │   R (5)  │  Row 1
├──────────┼──────────┼──────────┤
│  DL (6)  │  D  (7)  │  DR (8)  │  Row 2
└──────────┴──────────┴──────────┘
```

### 3.2 Hardware Interface

```
Load Cell Array (9× analog sensors)
       │
  [MCP3008 8-ch ADC] × 2 (daisy-chained via SPI)
       │
   [MCP23S17 GPIO Expander] (LED control via SPI)
       │
  ┌────┴────┐
  │  SBC    │  (SPI bus 0: ADC, SPI bus 1: LED expander)
  └─────────┘
```

### 3.3 Driver Plugin Implementation

Location: `src/arch/Input/InputHandler_9Panel.cpp`

```cpp
class InputHandler_9Panel : public InputHandler {
public:
    InputHandler_9Panel();
    ~InputHandler_9Panel() override;

    // StepMania InputHandler interface
    void GetDevicesAndDescriptions(vector<InputDeviceInfo>& v) override;
    void Update(float deltaTime) override;
    void SetDevicesHaveInput(int deviceIndex) override;

private:
    static constexpr int NUM_PANELS = 9;
    static constexpr int SPI_CHANNEL_ADC1 = 0;  // Panels 0-7
    static constexpr int SPI_CHANNEL_ADC2 = 1;  // Panel 8 + spares
    static constexpr float ACTIVATION_THRESHOLD = 0.3f;  // 30% of max load
    static constexpr float DEBOUNCE_MS = 50.0f;

    struct PanelState {
        float raw_voltage;
        float filtered_value;   // Low-pass filtered for noise reduction
        bool pressed;
        float press_timestamp;  // For double-step prevention
        float peak_pressure;    // Tracks maximum pressure during press (for MET estimation)
    };

    PanelState panels_[NUM_PANELS];
    int adc_fd_[2];  // SPI file descriptors
    int gpio_fd_;     // GPIO expander for LEDs
    
    // ADC read with 4-sample averaging + median filtering
    float ReadPanelADC(int panel_index);
    
    // Pressure-to-MET estimation
    // Maps panel pressure + step frequency to estimated MET output
    float EstimateMETFromPressure(float avg_pressure, float steps_per_second);
    
    // LED feedback based on hit accuracy
    void SetPanelLED(int panel_index, RGBColor color, float brightness);
};
```

### 3.4 Driver Integration Into StepMania's Input System

StepMania's input system uses `GameInput` mappings. The 9-panel driver maps physical panels to StepMania's `GameController`:

```cpp
// In GameInput mapping setup
void Setup9PanelMappings() {
    INPUTMAPPER->AddMapping(InputDevice_9Panel, 0, "9Panel_Center", GameButton_Center);
    INPUTMAPPER->AddMapping(InputDevice_9Panel, 1, "9Panel_Up", GameButton_Up);
    INPUTMAPPER->AddMapping(InputDevice_9Panel, 2, "9Panel_Down", GameButton_Down);
    INPUTMAPPER->AddMapping(InputDevice_9Panel, 3, "9Panel_Left", GameButton_Left);
    INPUTMAPPER->AddMapping(InputDevice_9Panel, 4, "9Panel_Right", GameButton_Right);
    INPUTMAPPER->AddMapping(InputDevice_9Panel, 5, "9Panel_UpLeft", GameButton_UpLeft);
    INPUTMAPPER->AddMapping(InputDevice_9Panel, 6, "9Panel_UpRight", GameButton_UpRight);
    INPUTMAPPER->AddMapping(InputDevice_9Panel, 7, "9Panel_DownLeft", GameButton_DownLeft);
    INPUTMAPPER->AddMapping(InputDevice_9Panel, 8, "9Panel_DownRight", GameButton_DownRight);
}
```

Note: StepMania's `GameButton` enum may need extension to support 9 distinct directional inputs. The 4-panel and 5-panel layouts use only subsets. For a full 9-panel, custom note types and `GameButton` entries are required.

### 3.5 Load Cell Calibration Routine

On first boot (and optionally on-demand from the service menu):

1. **Tare:** Read all 9 panels with no weight → record zero-offset per panel
2. **Weight reference:** Prompt technician to place a known weight (25lb/50lb plate) on each panel sequentially → record scaling factor
3. **Threshold auto-tune:** Measure ambient vibration noise floor → set ACTIVATION_THRESHOLD = noise_floor × 3 (minimum 15% of max)
4. **Save calibration** to `/etc/9panel/calibration.conf`

---

## 4. Fitness UI Layer

### 4.1 Screen Flow

```
[IDLE / ATTRACT] ──┬──→ [WORKOUT SELECT] ──→ [DIFFICULTY] ──→ [COUNTDOWN]
                    │         │                                    │
                    │         └──→ [MARATHON MODE] ───────────────→│
                    │                                              │
                    │         ┌────────────────────────────────────┘
                    │         ▼
                    │    [ACTIVE SESSION]
                    │         │
                    │         ├──→ [PAUSE] ──→ [RESUME / QUIT]
                    │         │
                    │         ▼
                    │    [SESSION SUMMARY]
                    │         │
                    │         ▼
                    └──→ [IDLE / ATTRACT]
```

### 4.2 Screen Specifications

#### IDLE / ATTRACT Mode
- **Content:** Looping instructional video demonstrating basic steps, or rotating fitness statistics ("1,247 sessions completed this month")
- **Heart-Rate Pairing:** Bluetooth beacon visible; pairing button on screen
- **QR Code:** "Start a session instantly with the PF Fit app" (future)

#### WORKOUT SELECT
- **Layout:** Large tiles, not song wheels
- **Options:**
  - **Free Session** — Pick a Psytrance marathon set manually
  - **Quick Cardio** — 30/45/60 minute auto-generated session at default difficulty
  - **Progressive** — 12-week training program that increases duration/intensity weekly
  - **Beat the Clock** — Target calorie burn within a time limit (gamified but fitness-framed)

#### DIFFICULTY SELECT
- **Labels:** Beginner, Easy, Medium, Hard, Challenge
- **Visual:** Each level shows estimated MET range, calorie burn per 30 min, and a one-sentence description ("Good for recovery days — moderate pace, limited lateral movement")
- **Recommended level:** "Most members start here" indicator based on onboarding preference

#### COUNTDOWN
- 5-second countdown with target zone visualization
- "Aim to maintain Zone 2-3 for the full session" instructional text

#### ACTIVE SESSION (The Core Screen)
```
┌──────────────────────────────────────────────────┐
│          60:00  ◉ RECORDING                      │
│  ┌──────────────────────────────────────────────┐│
│  │                                              ││
│  │        [3D STAGE VIEWPORT]                    ││
│  │     (arrows streaming up, centered)           ││
│  │                                              ││
│  └──────────────────────────────────────────────┘│
│  ┌──────────┬──────────┬──────────┬─────────────┐│
│  │ ♥ 143    │ ⌚ 38:15  │ 🔥 412   │ ⚡ MET 8.2  ││
│  │ Heart    │ Duration │ Calories │ Intensity   ││
│  │ Rate     │ Elapsed  │ Burned   │ Level       ││
│  ├──────────┴──────────┴──────────┴─────────────┤│
│  │ ZONE: ▼▼▼▼▼▲▲○○○   ZONE 3 (Aerobic Power)   ││
│  └──────────────────────────────────────────────┘│
│    [PAUSE]  [QUIT WORKOUT]  [BLUETOOTH: PAIRED]  │
└──────────────────────────────────────────────────┘
```

**Key differences from standard StepMania HUD:**
- No "score" or "combo" display — replaced by MET, heart rate, calories
- No life bar — replaced by zone indicator (heart-rate zone, not a health meter)
- Progress bar shows session duration, not song position
- Arrow viewport is slightly smaller, giving more room for biometric data

#### PAUSE OVERLAY
- Time elapsed / remaining
- Current zone and average intensity
- Resume / Quit / Pair Bluetooth

#### SESSION SUMMARY
```
┌──────────────────────────────────────────────────┐
│          WORKOUT COMPLETE                         │
│                                                   │
│  Duration:    60:00                               │
│  Calories:    412 kcal                            │
│  Avg HR:      143 bpm                             │
│  Peak HR:     168 bpm (Zone 5)                    │
│  Avg MET:     8.2                                 │
│  Steps:       8,447                               │
│  Time in Zone:                                    │
│    Zone 2 (Fat Burn):    12:30                    │
│    Zone 3 (Aerobic):     28:45                    │
│    Zone 4 (Anaerobic):   15:20                    │
│    Zone 5 (Max Effort):   3:25                    │
│                                                   │
│  ┌──────────────────────────────────────────────┐│
│  │  [Heart-rate zone distribution bar chart]     ││
│  └──────────────────────────────────────────────┘│
│                                                   │
│  [NEW PERSONAL BEST - LONGEST SESSION] ⭐         │
│                                                   │
│  [START NEW SESSION]  [FINISH]                    │
└──────────────────────────────────────────────────┘
```

### 4.3 Theme Structure

StepMania themes live in `Themes/`. The fitness theme replaces the default:

```
Themes/_Fitness/
├── BGAnimations/
│   ├── ScreenSelectWorkout.lua       # Replaces ScreenSelectMusic
│   ├── ScreenGameplayFitness.lua     # Replaces ScreenGameplay
│   └── ScreenSessionSummary.lua      # Replaces ScreenEvaluation
├── Graphics/
│   ├── FitnessUI.sprite              # Main atlas
│   ├── zone_indicator.png            # Heart-rate zone visualization
│   └── workout_complete.png          # Success screen graphic
├── Scripts/
│   ├── 02_HeartRateManager.lua       # Bluetooth HRM integration
│   ├── 03_TelemetryUploader.lua      # Session data to backend
│   └── 04_METCalculator.lua          # Real-time MET estimation
├── Fonts/
│   └── Inter-Variable.ttf            # Clean, modern sans-serif
└── metric_definitions.json           # Config for which metrics display
```

---

## 5. Content Format & Difficulty Scaling

### 5.1 Marathon Chart Format

Existing AutoArrow prototype outputs `.ssc` (StepManiaX-compatible). For the fitness fork, we extend the format with fitness-specific metadata:

```ini
#NOTES:
     FITNESS-Marathon:
     9-Panel:
     Beginner:
     0.7500,0.5000,0.2500,0.1000,0.0500,0.0500,0.0500,0.0500,0.7500:
     0.0000,0.0000,0.5000,0.1000,0.1000,0.0500,0.0500,0.0500,0.0500,0.0500:
     // Step data (measures)...
;
```

The `FITNESS-Marathon` step type triggers:
- Duration-based scoring (calories, not points)
- Zone-aware difficulty curve (auto-adjusting note density to keep user in target HR zone)
- Integrated cool-down segments every 15 minutes

### 5.2 Difficulty Progression (60-Minute Session)

| Level | Avg Steps/Min | Peak MET | Panel Usage | Description |
|-------|--------------|----------|-------------|-------------|
| **Beginner** | 40-60 | 4-5 | Center + 4 cardinal | Basic stepping pattern, steady rhythm, wide timing windows |
| **Easy** | 60-80 | 5-7 | 5 panels + diagonals | Introduces diagonal steps, simple 8th-note patterns |
| **Medium** | 80-110 | 7-9 | All 9 panels | Full panel usage, 8th/16th note mixed patterns |
| **Hard** | 110-140 | 9-11 | All 9, dense | Complex patterns, crossovers, 16th-note runs, holds |
| **Challenge** | 140-170 | 11-13 | All 9, maximum | Technical patterns, sudden direction changes, high-speed sections |

### 5.3 Metabolic Pacing Curve (Within a Session)

```
Intensity
  ▲
  │  Z5  │░░░░░░░░│        │        │░░░░│        │
  │  Z4  │░░░░███████████████░░░░███████████████████│
  │  Z3  │███████████████████████████████████████████│
  │  Z2  │███████████████████████████████████████████│
  │  Z1  │███████████████████████████████████████████│
  └─────┴──────────────────────────────────────────▶ Time
        0        15        30        45        60 min
         │        │         │         │         │
       Warmup  Build   Sustain   Push    Cooldown
       (Z1-2)  (Z2-3)  (Z3-4)   (Z4-5)  (Z1-2)
```

This curve is encoded in the `.ssc` metadata as `#MARATHON_PHASES:Warmup:5,Build:10,Sustain:25,Push:15,Cooldown:5`.

---

## 6. Telemetry & Backend Integration

### 6.1 Session Upload Schema

```json
{
  "session_id": "uuid-v4",
  "machine_id": "andamiro-9p-serial-001",
  "club_id": "pf-michigan-0123",
  "started_at": "2026-07-01T09:00:00Z",
  "duration_seconds": 3600,
  "difficulty": "medium",
  "workout_type": "marathon_60",
  "steps": 8447,
  "avg_met": 8.2,
  "peak_met": 11.5,
  "avg_heart_rate": 143,
  "peak_heart_rate": 168,
  "time_in_zones": {
    "zone_1": 120,
    "zone_2": 750,
    "zone_3": 1725,
    "zone_4": 920,
    "zone_5": 85
  },
  "calories_burned": 412,
  "panel_usage": {
    "center": 0.18,
    "up": 0.14,
    "down": 0.16,
    "left": 0.13,
    "right": 0.13,
    "up_left": 0.07,
    "up_right": 0.07,
    "down_left": 0.06,
    "down_right": 0.06
  },
  "chart_id": "autoarrow-psyt-001-marathon-medium-v3"
}
```

### 6.2 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/sessions` | POST | Upload completed session |
| `/api/v1/sessions/live` | WebSocket | Real-time session telemetry (for live dashboard) |
| `/api/v1/content/pull` | GET | Fetch latest chart manifests for OTA update |
| `/api/v1/content/download/{chart_id}` | GET | Download specific chart `.ssc` + audio |
| `/api/v1/machine/heartbeat` | POST | Health check + uptime report (every 60s) |
| `/api/v1/machine/config` | GET | Remote configuration (adjust thresholds, firmware) |

### 6.3 OTA Content Pipeline

```
AutoArrow ML Engine (server-side)
       │
       ▼
  Chart generation (60-min marathon .ssc + encoded audio)
       │
       ▼
  Content signed + uploaded to CDN
       │
       ▼
  Content manifest updated (API)
       │
       ▼
  Machine polls /api/v1/content/pull
       │
       ▼
  New chart detected → download in background
       │
       ▼
  Next session start → new content available
```

---

## 7. Build & Deployment

### 7.1 Build Process

```bash
# Cross-compile for ARM64 target
mkdir build && cd build
cmake .. \
    -DCMAKE_TOOLCHAIN_FILE=../cmake/toolchain-aarch64.cmake \
    -DWITH_9PANEL=ON \
    -DWITH_FFMPEG=ON \
    -DWITH_QT=ON \
    -DFORCE_FITNESS_THEME=ON \
    -DDISABLE_ONLINE_UPDATES=OFF
make -j4
```

### 7.2 Firmware Image Structure

```
fitness-os-v1.0.0.img
├── boot/
│   ├── config.txt
│   └── overlays/
│       └── 9panel-adc.dtbo    # Device tree overlay for SPI ADC
├── rootfs/
│   ├── usr/local/bin/
│   │   ├── sm-fitness          # StepMania fitness engine binary
│   │   ├── 9panel-calibrate    # Load cell calibration utility
│   │   └── fitness-updater     # OTA update daemon
│   └── etc/
│       ├── 9panel/
│       │   └── calibration.conf # Factory calibration data
│       ├── fitness/
│       │   ├── content.db       # SQLite index of installed content
│       │   └── machine.conf     # Serial number, club ID, API keys
│       └── systemd/
│           └── fitness.service  # Auto-start on boot
```

---

## 8. Development Milestones

| Phase | Deliverable | Timeline |
|-------|-------------|----------|
| **P0** | 9-panel input driver (standalone test harness) | Week 1-2 |
| **P1** | StepMania fork compiles on ARM64 with 9-panel support | Week 3-4 |
| **P2** | Fitness UI theme (all screens) implemented | Week 5-8 |
| **P3** | Bluetooth HRM integration + telemetry upload | Week 6-8 |
| **P4** | OTA content pipeline + AutoArrow integration | Week 8-10 |
| **P5** | Full 60-min marathon session end-to-end test | Week 10-12 |
| **P6** | Load cell calibration tool + manufacturing test suite | Week 11-12 |

---

## 9. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| StepMania input system doesn't cleanly support 9 distinct buttons | Requires engine patch | Extend GameButton enum; patch is ~50 lines in `GameInput.cpp` + `GameManager.cpp` |
| Real-time HRM via Bluetooth has latency | Zone display lags 5-15s behind | Use rolling 30s average for zone display, not instantaneous |
| ML-generated charts don't feel "natural" on 9-panel | Poor user experience | Build a 9-panel pattern validator (leg-flow, repetition detection) as a post-processing step in AutoArrow |
| Thermal throttling on SBC during 60-min session | Frame drops, input lag | Test with heat sink + fan; underclock if needed (chart rendering is not GPU-intensive at 60fps) |

---

## Appendix A: StepMania Source Files to Modify

| File | Change |
|------|--------|
| `src/GameInput/GameInput.cpp` | Add `GameButton_UpLeft`, `GameButton_UpRight`, `GameButton_DownLeft`, `GameButton_DownRight`, `GameButton_Center` |
| `src/GameInput/InputMapper.cpp` | Map new button types |
| `src/StepMania.cpp` | Add `--fitness-mode` CLI flag that forces fitness theme, disables arcade screens |
| `src/ScreenManager.cpp` | Add routing for `ScreenSelectWorkout`, `ScreenSessionSummary` |
| `src/arch/Input/InputHandler_9Panel.cpp` | New file (full driver) |
| `src/arch/Sound/TimerThreaded.cpp` | Verify timer accuracy for 60-min+ sessions (no 32-bit overflow) |
| `CMakeLists.txt` | Add `WITH_9PANEL` option, link SPI libraries |
