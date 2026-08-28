import pytest
from analytics import calculate_mets_from_nps, classify_heart_rate_zone

def test_calculate_mets_from_nps():
    # Base cases
    assert calculate_mets_from_nps(0) == 1.0
    assert calculate_mets_from_nps(-5) == 1.0

    # Max bound limits
    assert calculate_mets_from_nps(12.0) == 12.0
    assert calculate_mets_from_nps(20.0) == 12.0

    # 6.0 nps -> 5.0 intensity -> 3.0 + (5.0 - 1.0) * (9.0 / 9.0) = 7.0
    assert calculate_mets_from_nps(6.0) == 7.0

def test_classify_heart_rate_zone():
    assert classify_heart_rate_zone(60) == 'Resting'
    assert classify_heart_rate_zone(115) == 'Zone 1 (Warmup)'
    assert classify_heart_rate_zone(130) == 'Zone 2 (Fat Burn)'
    assert classify_heart_rate_zone(145) == 'Zone 3 (Aerobic)'
    assert classify_heart_rate_zone(160) == 'Zone 4 (Threshold)'
    assert classify_heart_rate_zone(175) == 'Zone 5 (Max)'
