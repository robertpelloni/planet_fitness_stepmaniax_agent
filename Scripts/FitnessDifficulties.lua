-- FitnessDifficulties.lua
-- StepMania Fitness Fork Core Script
-- Translates raw arcade-style Notes Per Second (NPS) into a 1-10 fitness intensity scale.

local FitnessIntensity = {}

-- Define the maximum realistic NPS for continuous cardio.
-- Beyond this, it is anaerobic sprinting rather than aerobic pacing.
local MAX_CARDIO_NPS = 12.0

-- Function to convert NPS to a 1-10 scale (floating point)
function FitnessIntensity.GetIntensityFromNPS(nps)
    if not nps or nps <= 0 then
        return 1.0
    end

    local raw_scale = (nps / MAX_CARDIO_NPS) * 10.0

    -- Cap the scale at exactly 10.0 for safety and readability.
    if raw_scale > 10.0 then
        return 10.0
    end

    -- Round to one decimal place for UI cleanliness
    return math.floor((raw_scale * 10) + 0.5) / 10
end

-- Helper for StepMania Engine hook
-- Returns the integer floor of the intensity for broad categorization (e.g., Level 5)
function FitnessIntensity.GetCategoryFromNPS(nps)
    local intensity = FitnessIntensity.GetIntensityFromNPS(nps)
    return math.floor(intensity)
end

-- Hook to calculate MET (Metabolic Equivalent of Task) estimate
-- Base assumptions:
-- 1.0 MET = Resting
-- 3.0-6.0 MET = Moderate Intensity (Walking/Jogging equivalent)
-- > 6.0 MET = Vigorous (Running/Sprinting equivalent)
function FitnessIntensity.EstimateMET(nps)
    if not nps or nps <= 0 then
        return 1.0
    end

    local intensity = FitnessIntensity.GetIntensityFromNPS(nps)
    -- Scaling formula: Intensity 1 -> 3.0 MET, Intensity 10 -> 12.0 MET
    local met = 3.0 + (intensity - 1.0) * (9.0 / 9.0)

    return math.floor((met * 10) + 0.5) / 10
end

return FitnessIntensity
