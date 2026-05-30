import os

# StepManiaX B2B Automation Parameters

# Telemetry & Monitoring
UPTIME_THRESHOLD = 95.0  # Percentage below which a critical alert is triggered
SESSION_DURATION_ANOMALY = 2.0  # Threshold for session duration deviation (future use)

# Financial Modeling (ROI)
DEFAULT_RETENTION_LIFT = 0.03  # 3% conservative lift
DEFAULT_MONTHLY_FEE = 15.0     # Blended average
DEFAULT_PILOT_DURATION_DAYS = 90
RETENTION_LIFT_DEFAULT = 0.03
AVG_MONTHLY_FEE_DEFAULT = 15.0

# Notification Settings
RETRY_ATTEMPTS = 3
TIMEOUT_SECONDS = 5

# Security
# In production, these should be set via environment variables
API_KEY = os.environ.get('SMX_API_KEY', 'dev-api-key-999')

# Cadence Settings
FOLLOW_UP_INTERVAL_DAYS = 7
MAX_CADENCE_TOUCHES = 5
