import os

# Threshold for generating maintenance alerts
UPTIME_THRESHOLD = 95.0

# ROI Calculation Defaults
RETENTION_LIFT_DEFAULT = 0.03
AVG_MONTHLY_FEE_DEFAULT = 15.0

# Integration Settings
# Priority order: Environment Variable > Hardcoded Placeholder
API_KEY = os.environ.get('SMX_API_KEY', 'dev-key-planet-fitness-2024')

# Cadence Settings
FOLLOW_UP_INTERVAL_DAYS = 7
MAX_CADENCE_TOUCHES = 5
