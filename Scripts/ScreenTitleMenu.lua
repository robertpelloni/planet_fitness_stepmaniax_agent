-- ScreenTitleMenu.lua
-- StepMania Fitness Fork Core Script
-- Replaces the standard arcade Title Menu overlay.
-- Implements immediate auto-join and bypasses directly to ScreenSelectMusic for a seamless fitness experience.

local t = Def.ActorFrame {
    InitCommand=function(self)
        -- Suppress arcade elements
        self:visible(false)
    end,

    OnCommand=function(self)
        -- Immediately force Player 1 to join (assuming kiosk/single-player commercial gym setup)
        if not GAMESTATE:IsHumanPlayer(PLAYER_1) then
            GAMESTATE:JoinPlayer(PLAYER_1)
        end

        -- Set the play mode to standard/dance (or a custom Fitness mode if defined in the fork)
        GAMESTATE:SetCurrentPlayMode("PlayMode_Regular")
        GAMESTATE:SetCurrentStyle("single") -- Default to 9-panel single style when driver is ready

        -- Bypass title and warning screens, go straight to music/workout selection
        SCREENMAN:SetNewScreen("ScreenSelectMusic")
    end
}

return t
