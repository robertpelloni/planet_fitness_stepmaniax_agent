/**
 * @file 9panel_driver.cpp
 * @brief Standalone C++ SPI ADC hardware driver and test harness for the Teensy 4.0 9-Panel Load Cell Matrix.
 *
 * WHY:
 * Commercial 9-panel exergaming hardware (Andamiro prototype / Path B) replaces binary microswitches
 * with high-precision load cell transducers across a 3x3 stage matrix. This requires microsecond-level
 * sampling over an SPI bus, continuous dynamic baseline tare (auto-calibration) to compensate for thermal
 * drift and structural deflection, and dual-threshold hysteresis filtering to eliminate sensor bounce / chatter
 * during high-speed 16th-note running patterns.
 *
 * STRUCTURAL SIDE EFFECTS:
 * When compiled natively with g++ -std=c++11, this file acts as an executable simulation test harness
 * that models SPI ADC transaction frames, validates tare calibration mathematical convergence, and verifies
 * debounce threshold transitions against simulated force vectors.
 */

#include <iostream>
#include <vector>
#include <cstdint>
#include <cmath>
#include <cassert>
#include <iomanip>

constexpr uint8_t NUM_PANELS = 9;
constexpr uint16_t ADC_MAX_VALUE = 4095; // 12-bit ADC resolution
constexpr float CALIBRATION_SAMPLES = 64.0f;

// Debounce and hysteresis thresholds (in ADC counts above tare baseline)
constexpr float HYSTERESIS_PRESS_THRESHOLD = 320.0f;   // Approx. 15-20 kg trigger force
constexpr float HYSTERESIS_RELEASE_THRESHOLD = 180.0f; // Approx. 8-10 kg release force

enum PanelIndex {
    PANEL_TOP_LEFT = 0,
    PANEL_UP = 1,
    PANEL_TOP_RIGHT = 2,
    PANEL_LEFT = 3,
    PANEL_CENTER = 4,
    PANEL_RIGHT = 5,
    PANEL_BOTTOM_LEFT = 6,
    PANEL_DOWN = 7,
    PANEL_BOTTOM_RIGHT = 8
};

struct PanelState {
    float tare_offset = 0.0f;
    float current_filtered_value = 0.0f;
    bool is_pressed = false;
    uint32_t step_count = 0;
};

class NinePanelDriver {
private:
    std::vector<PanelState> panels;
    bool calibrated = false;

public:
    NinePanelDriver() : panels(NUM_PANELS) {}

    /**
     * @brief Performs baseline tare auto-calibration across all 9 load cells.
     * Samples the ambient resting force (stage plate weight, structural frame tension)
     * and calculates the mean offset to zero out the stage before active sessions.
     */
    void auto_calibrate(const std::vector<std::vector<uint16_t>>& calibration_frames) {
        assert(!calibration_frames.empty() && "Calibration frames cannot be empty");
        size_t num_frames = calibration_frames.size();

        std::vector<float> accumulators(NUM_PANELS, 0.0f);
        for (const auto& frame : calibration_frames) {
            assert(frame.size() == NUM_PANELS && "Each frame must supply 9 panel values");
            for (size_t i = 0; i < NUM_PANELS; ++i) {
                accumulators[i] += static_cast<float>(frame[i]);
            }
        }

        for (size_t i = 0; i < NUM_PANELS; ++i) {
            panels[i].tare_offset = accumulators[i] / static_cast<float>(num_frames);
            panels[i].current_filtered_value = 0.0f;
            panels[i].is_pressed = false;
            panels[i].step_count = 0;
        }

        calibrated = true;
    }

    /**
     * @brief Processes an incoming SPI frame of raw 12-bit ADC readings.
     * Applies baseline subtraction, exponential moving average (EMA) smoothing,
     * and dual-threshold Schmitt trigger / hysteresis filtering.
     *
     * @param raw_frame Vector of 9 raw ADC readings.
     * @return std::vector<bool> Binary active state for each panel.
     */
    std::vector<bool> process_spi_frame(const std::vector<uint16_t>& raw_frame) {
        assert(calibrated && "Driver must be auto-calibrated before processing input");
        assert(raw_frame.size() == NUM_PANELS && "Frame must contain 9 ADC values");

        std::vector<bool> states(NUM_PANELS, false);
        const float alpha = 0.65f; // Fast EMA response for low latency

        for (size_t i = 0; i < NUM_PANELS; ++i) {
            float net_force = static_cast<float>(raw_frame[i]) - panels[i].tare_offset;
            if (net_force < 0.0f) net_force = 0.0f;

            // EMA filter to dampen mechanical vibration and sensor noise
            panels[i].current_filtered_value = (alpha * net_force) + ((1.0f - alpha) * panels[i].current_filtered_value);

            // Hysteresis Schmitt Trigger logic
            if (!panels[i].is_pressed) {
                if (panels[i].current_filtered_value >= HYSTERESIS_PRESS_THRESHOLD) {
                    panels[i].is_pressed = true;
                    panels[i].step_count++;
                }
            } else {
                if (panels[i].current_filtered_value <= HYSTERESIS_RELEASE_THRESHOLD) {
                    panels[i].is_pressed = false;
                }
            }

            states[i] = panels[i].is_pressed;
        }

        return states;
    }

    bool is_calibrated() const { return calibrated; }
    const PanelState& get_panel_state(size_t index) const { return panels.at(index); }
};

int main() {
    std::cout << "======================================================" << std::endl;
    std::cout << "  Teensy 4.0 9-Panel Load Cell Matrix Driver Test     " << std::endl;
    std::cout << "======================================================" << std::endl;

    NinePanelDriver driver;

    // 1. Generate ambient calibration frames (simulating ~200-250 counts baseline frame weight)
    std::vector<std::vector<uint16_t>> cal_data;
    for (int f = 0; f < 64; ++f) {
        std::vector<uint16_t> frame(NUM_PANELS);
        for (int p = 0; p < NUM_PANELS; ++p) {
            frame[p] = 220 + (p * 5) + (f % 3); // Small noise fluctuations
        }
        cal_data.push_back(frame);
    }

    std::cout << "[SIM] Executing auto-calibration tare sequence..." << std::endl;
    driver.auto_calibrate(cal_data);
    assert(driver.is_calibrated());
    std::cout << "[PASS] Auto-calibration converged across 9 panels." << std::endl;

    // Verify tare offsets
    for (size_t p = 0; p < NUM_PANELS; ++p) {
        std::cout << "  Panel " << p << " Tare Offset: "
                  << std::fixed << std::setprecision(2)
                  << driver.get_panel_state(p).tare_offset << " ADC counts" << std::endl;
    }

    // 2. Simulate step sequence on Center Panel (index 4) and Up Panel (index 1)
    std::cout << "\n[SIM] Testing Hysteresis Filtering and Chatter Elimination..." << std::endl;

    // Resting baseline frame (no foot on pad)
    std::vector<uint16_t> rest_frame(NUM_PANELS);
    for (int p = 0; p < NUM_PANELS; ++p) rest_frame[p] = static_cast<uint16_t>(driver.get_panel_state(p).tare_offset);
    auto rest_state = driver.process_spi_frame(rest_frame);
    assert(!rest_state[PANEL_CENTER] && "Center panel must not trigger at rest");

    // Partial load below press threshold (simulating foot hover / light contact 200 counts net)
    auto hover_frame = rest_frame;
    hover_frame[PANEL_CENTER] += 200;
    auto hover_state = driver.process_spi_frame(hover_frame);
    assert(!hover_state[PANEL_CENTER] && "Center panel must reject chatter below press threshold");

    // Full load exceeding press threshold (500 counts net)
    auto press_frame = rest_frame;
    press_frame[PANEL_CENTER] += 600;
    // Process two frames to allow EMA to settle
    driver.process_spi_frame(press_frame);
    auto press_state = driver.process_spi_frame(press_frame);
    assert(press_state[PANEL_CENTER] && "Center panel must engage upon exceeding press threshold");
    assert(driver.get_panel_state(PANEL_CENTER).step_count == 1);
    std::cout << "[PASS] Initial step registered on Center Panel (Count: 1)." << std::endl;

    // Hysteresis test: force drops to 250 counts net (between 180 and 320)
    // The panel must REMAIN PRESSED to prevent rapid toggling / chatter
    auto intermediate_frame = rest_frame;
    intermediate_frame[PANEL_CENTER] += 250;
    auto intermediate_state = driver.process_spi_frame(intermediate_frame);
    assert(intermediate_state[PANEL_CENTER] && "Center panel must remain pressed in hysteresis deadband");
    std::cout << "[PASS] Hysteresis hold verified (maintained state in 180-320 deadband)." << std::endl;

    // Force drops below release threshold (50 counts net)
    auto release_frame = rest_frame;
    release_frame[PANEL_CENTER] += 50;
    driver.process_spi_frame(release_frame);
    auto release_state = driver.process_spi_frame(release_frame);
    assert(!release_state[PANEL_CENTER] && "Center panel must release below release threshold");
    std::cout << "[PASS] Center panel cleanly released." << std::endl;

    std::cout << "\n======================================================" << std::endl;
    std::cout << "  ALL 9-PANEL DRIVER & HYSTERESIS TESTS PASSED!       " << std::endl;
    std::cout << "======================================================" << std::endl;

    return 0;
}
