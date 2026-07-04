-- 03_TelemetryUploader.lua
-- StepMania Fitness Fork
-- Handles WebSocket telemetry sync with the Flask CRM backend.

local TelemetryUploader = {}

local ws = nil
local BACKEND_URL = "ws://127.0.0.1:5000/api/v1/sessions/live" -- Mock URL

function TelemetryUploader.Init()
    -- Mocking WebSocket connection initialization
    if type(NETWORK) ~= "nil" then
        ws = NETWORK:ConnectWebSocket(BACKEND_URL)
    end
end

function TelemetryUploader.UploadSession(sessionData)
    -- Encode payload to JSON
    local payload = "{"
    for k, v in pairs(sessionData) do
        payload = payload .. string.format('"%s": "%s",', k, tostring(v))
    end
    payload = string.sub(payload, 1, -2) .. "}"

    -- Dispatch
    if ws then
        ws:Send(payload)
    else
        -- Fallback to standard HTTP POST if WS fails
        -- NETWORK:HttpRequest("POST", "http://127.0.0.1:5000/api/v1/sessions", payload)
    end
end

return TelemetryUploader
