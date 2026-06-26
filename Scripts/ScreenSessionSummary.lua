-- ScreenSessionSummary.lua
-- Replaces ScreenEvaluation for the StepMania Fitness Fork
-- Strips all arcade metrics (Scores, Combo, Letter Grades) in favor of B2B fitness telemetry.

local FitnessDifficulties = require("Scripts.FitnessDifficulties")

local t = Def.ActorFrame {
    InitCommand=function(self)
        self:Center()
    end,

    -- Background
    Def.Quad {
        InitCommand=function(self)
            self:zoomto(SCREEN_WIDTH, SCREEN_HEIGHT)
            self:diffuse(color("#0f172a")) -- Tailwind slate-900
        end
    },

    -- Header
    Def.BitmapText {
        Font="Common Normal",
        Text="WORKOUT SUMMARY",
        InitCommand=function(self)
            self:y(-SCREEN_HEIGHT/2 + 50)
            self:zoom(1.5)
            self:diffuse(color("#3b82f6")) -- Tailwind blue-500
            self:uppercase(true)
        end
    },

    -- Central Stats Container
    Def.ActorFrame {
        OnCommand=function(self)
            local stats = STATSMAN:GetCurStageStats():GetPlayerStageStats(PLAYER_1)

            -- Gather basic StepMania stats
            local total_steps = stats:GetActualDancePoints() -- Repurposing dance points as step counter
            local duration_sec = STATSMAN:GetCurStageStats():GetGameplaySeconds()
            local avg_nps = total_steps / duration_sec

            -- Calculate Fitness Metrics using our custom Lua module
            local avg_intensity = FitnessDifficulties.GetIntensityFromNPS(avg_nps)
            local est_met = FitnessDifficulties.EstimateMET(avg_nps)

            -- Basic caloric burn estimation (MET * weight_kg * duration_hours)
            -- Assuming standard 75kg for anonymous users if no biometric profile is loaded
            local calories_burned = est_met * 75 * (duration_sec / 3600)

            -- Broadcast data so telemetry WebSocket can upload it to Flask backend
            MESSAGEMAN:Broadcast("WorkoutComplete", {
                duration = duration_sec,
                steps = total_steps,
                met = est_met,
                calories = calories_burned,
                intensity = avg_intensity
            })

            -- UI Elements
            self:GetChild("DurationText"):settext(string.format("TIME: %02d:%02d", math.floor(duration_sec/60), duration_sec%60))
            self:GetChild("StepsText"):settext(string.format("STEPS: %d", total_steps))
            self:GetChild("CaloriesText"):settext(string.format("CALORIES: %d KCAL", math.floor(calories_burned)))
            self:GetChild("IntensityText"):settext(string.format("INTENSITY: %.1f", avg_intensity))
        end,

        Def.BitmapText { Name="DurationText", Font="Common Normal", y=-40, zoom=1.2, diffuse=color("#ffffff") },
        Def.BitmapText { Name="StepsText", Font="Common Normal", y=0, zoom=1.2, diffuse=color("#ffffff") },
        Def.BitmapText { Name="CaloriesText", Font="Common Normal", y=40, zoom=1.2, diffuse=color("#fbbf24") }, -- Tailwind yellow-400
        Def.BitmapText { Name="IntensityText", Font="Common Normal", y=80, zoom=1.2, diffuse=color("#f87171") } -- Tailwind red-400
    },

    -- Finish Button Prompt
    Def.BitmapText {
        Font="Common Normal",
        Text="PRESS CENTER PANEL TO FINISH",
        InitCommand=function(self)
            self:y(SCREEN_HEIGHT/2 - 50)
            self:zoom(0.8)
            self:diffuse(color("#94a3b8")) -- Tailwind slate-400
            self:bob()
            self:effectmagnitude(0, 5, 0)
            self:effectclock("beat")
        end
    }
}

return t
