-- 02_HeartRateManager.lua
-- StepMania Fitness Fork
-- Manages the ingestion of Bluetooth HRM (Heart Rate Monitor) telemetry via C++ engine hooks.
-- Broadcasts active heart rate to the UI layer to enable dynamic zone rendering and MET correlation.

local HeartRateManager = {}

-- State variables
local currentHR = 0
local targetHR = 140 -- Default target, will be overridden by member's biometric profile
local maxHR = 190    -- Age-derived default (e.g. 220 - age)
local isConnected = false

-- Zone Thresholds (Percentage of Max HR)
local ZONES = {
    ZONE_1 = 0.50, -- 50-60%: Warmup / Recovery
    ZONE_2 = 0.60, -- 60-70%: Fat Burn / Endurance
    ZONE_3 = 0.70, -- 70-80%: Aerobic / Cardio
    ZONE_4 = 0.80, -- 80-90%: Anaerobic / Threshold
    ZONE_5 = 0.90  -- 90-100%: Maximum Effort / VO2 Max
}

-- Initialize connection state
function HeartRateManager.Init()
    -- Request the underlying C++ driver to begin scanning for paired BLE devices
    -- Note: This assumes a custom Lua binding `FITNESS_BLE:StartScan()` exists in the StepMania fork
    if type(FITNESS_BLE) ~= "nil" then
        FITNESS_BLE:StartScan()
        isConnected = false
        currentHR = 0
        MESSAGEMAN:Broadcast("HRMStatusChanged", { status = "Scanning" })
    end
end

-- Called periodically via an Actor's Update function or directly from the engine callback
function HeartRateManager.Update(delta_time)
    if type(FITNESS_BLE) == "nil" then return end

    local new_hr = FITNESS_BLE:GetLatestHeartRate()
    local conn_status = FITNESS_BLE:IsConnected()

    -- State change: Connection gained or lost
    if conn_status ~= isConnected then
        isConnected = conn_status
        local msg = isConnected and "Connected" or "Disconnected"
        MESSAGEMAN:Broadcast("HRMStatusChanged", { status = msg })
    end

    -- State change: Heart Rate update
    if isConnected and new_hr ~= currentHR and new_hr > 0 then
        -- Rolling average should be handled in the C++ layer to prevent UI jitter,
        -- but we enforce basic sanity constraints here.
        if new_hr > 40 and new_hr < 220 then
            currentHR = new_hr

            -- Calculate active zone
            local current_zone = 0
            local percent_max = currentHR / maxHR

            if percent_max >= ZONES.ZONE_5 then current_zone = 5
            elseif percent_max >= ZONES.ZONE_4 then current_zone = 4
            elseif percent_max >= ZONES.ZONE_3 then current_zone = 3
            elseif percent_max >= ZONES.ZONE_2 then current_zone = 2
            elseif percent_max >= ZONES.ZONE_1 then current_zone = 1
            end

            MESSAGEMAN:Broadcast("HeartRateUpdated", {
                bpm = currentHR,
                zone = current_zone,
                percent = percent_max
            })
        end
    end
end

-- Utility Accessors for UI Elements
function HeartRateManager.GetCurrentHR()
    return currentHR
end

function HeartRateManager.GetTargetHR()
    return targetHR
end

function HeartRateManager.SetMemberBiometrics(age, target)
    if age and age > 10 and age < 100 then
        maxHR = 220 - age
    end
    if target and target > 80 and target < 200 then
        targetHR = target
    end
end

return HeartRateManager
