"""
Shared Analytical Module for StepManiaX B2B Sales Agent.
Provides consolidated ROI and Lifetime Value (LTV) calculation logic.
"""

import config

def calculate_detailed_metrics(
    num_clubs=1,
    members_per_club=6000,
    avg_monthly_fee=None,
    retention_lift_percent=None,
    avg_member_lifetime_months=18,
    smx_monthly_cost_per_club=600.0,
    onboarding_conversion_rate=1.0 # 1.0 = 100%
):
    """
    Calculates comprehensive ROI metrics using the LTV framework.
    """
    # Defensive handling for None inputs
    if num_clubs is None: num_clubs = 1
    if members_per_club is None: members_per_club = 6000

    # Use defaults from config if not provided
    if avg_monthly_fee is None:
        avg_monthly_fee = getattr(config, 'AVG_MONTHLY_FEE_DEFAULT', 15.0)
    if retention_lift_percent is None:
        retention_lift_percent = getattr(config, 'RETENTION_LIFT_DEFAULT', 0.03)

    total_members = num_clubs * members_per_club

    # 1. Base LTV Analysis
    base_ltv = avg_monthly_fee * avg_member_lifetime_months
    base_total_portfolio_value = total_members * base_ltv

    # 2. Lifted LTV Analysis
    # Realized lift is scaled by the onboarding conversion rate
    realized_lift = retention_lift_percent * onboarding_conversion_rate
    lifted_lifetime_months = avg_member_lifetime_months * (1 + realized_lift)
    lifted_ltv = avg_monthly_fee * lifted_lifetime_months
    lifted_total_portfolio_value = total_members * lifted_ltv

    # 3. Financial Gain
    total_portfolio_value_gain = lifted_total_portfolio_value - base_total_portfolio_value
    annual_revenue_gain = total_portfolio_value_gain / (lifted_lifetime_months / 12)

    # 4. Costs
    total_monthly_cost = num_clubs * smx_monthly_cost_per_club
    total_annual_cost = total_monthly_cost * 12

    # 5. Final Metrics
    annual_net_profit = annual_revenue_gain - total_annual_cost
    roi_multiple = annual_revenue_gain / total_annual_cost if total_annual_cost > 0 else 0

    return {
        "total_members": total_members,
        "base_ltv": round(base_ltv, 2),
        "lifted_ltv": round(lifted_ltv, 2),
        "annual_revenue_gain": round(annual_revenue_gain, 2),
        "annual_net_profit": round(annual_net_profit, 2),
        "roi_multiple": round(roi_multiple, 2)
    }

def calculate_propensity_score(lead_data):
    """
    Calculates a 'Propensity Score' (0-100) based on lead metadata.
    Higher scores indicate better targets for StepManiaX.
    """
    score = 50 # Base score

    # 1. Scale Multiplier (Bigger is better for regional expansion)
    num_clubs = lead_data.get('num_clubs') or 0
    if num_clubs > 100: score += 20
    elif num_clubs > 50: score += 15
    elif num_clubs > 20: score += 10

    # 2. Regional Priority (Michigan/Midwest)
    region = (lead_data.get('region') or '').lower()
    if 'michigan' in region or 'mi' == region: score += 15
    elif 'ohio' in region or 'midwest' in region: score += 10

    # 3. Status Bonus (Further down the funnel = higher propensity)
    status = lead_data.get('status') or 'Identified'
    status_weights = {
        'Researching': 5,
        'Ready for Outreach': 10,
        'Outreach Active': 15,
        'Discovery Call Scheduled': 25,
        'Pilot MOU Signed': 40
    }
    score += status_weights.get(status, 0)

    # 4. Priority Multiplier
    priority = lead_data.get('priority', 'Medium')
    if priority == 'High': score += 10
    elif priority == 'Low': score -= 10

    # 5. Pilot Engagement Bonus (v3.4.0)
    pilot_engagement = lead_data.get('pilot_engagement', {})
    members = pilot_engagement.get('member_count', 0)
    points = pilot_engagement.get('total_points', 0)

    if members > 10: score += 10
    elif members > 0: score += 5

    if points > 1000: score += 10
    elif points > 100: score += 5

    # 6. Intent Signal (v3.8.0)
    views = lead_data.get('portal_views') or 0
    if views > 10: score += 20
    elif views > 5: score += 15
    elif views > 0: score += 10

    # 7. Sentiment Signal (v3.9.1)
    avg_rating = lead_data.get('avg_feedback_rating', 5.0)
    if avg_rating >= 4.5: score += 10
    elif avg_rating < 3.0: score -= 15

    # Cap at 100
    return min(100, score)

def generate_optimization_recommendations(metrics_list):
    """
    Generates strategic optimization recommendations based on fleet performance.
    Expects a list of dictionaries containing equipment metrics.
    """
    recommendations = []
    for unit in metrics_list:
        # 1. Capacity Constraints
        if unit.get('total_sessions', 0) > 450:
            recommendations.append({
                "unit": unit.get('equipment_name'),
                "type": "Capacity Warning",
                "message": f"Unit at {unit.get('location')} is operating at >90% peak capacity. Secondary deployment recommended."
            })

        # 2. Maintenance Predictor
        if unit.get('uptime_percent', 100) < 96:
            recommendations.append({
                "unit": unit.get('equipment_name'),
                "type": "Health Warning",
                "message": f"Uptime degradation detected for {unit.get('equipment_name')}. Schedule predictive maintenance."
            })

        # 3. Engagement Optimization
        if unit.get('avg_session_duration', 0) < 8 and unit.get('total_sessions', 0) > 100:
            recommendations.append({
                "unit": unit.get('equipment_name'),
                "type": "Engagement Opportunity",
                "message": f"Low session duration at {unit.get('location')}. Consider adjusting difficulty or hosting a HIIT challenge."
            })

    return recommendations

def calculate_predictive_health_score(unit_data, recent_history=[]):
    """
    Calculates a predictive health score (0-100) based on uptime,
    heartbeat stability, and recent session density.
    """
    score = unit_data.get('uptime_percent', 100.0)

    # 1. Intensity Penalty (High volume increases wear)
    total_sessions = unit_data.get('total_sessions', 0)
    if total_sessions > 1000: score -= 10
    elif total_sessions > 500: score -= 5

    # 2. Stability Factor (Check for irregular heartbeat gaps in history)
    # Mocking for now: if avg session duration is very low (< 3 mins),
    # it might indicate hardware resets or crashes.
    avg_duration = unit_data.get('avg_session_duration', 0)
    if avg_duration < 3.0 and total_sessions > 50:
        score -= 15

    # 3. Connectivity Penalty (If heartbeat is old)
    last_hb = unit_data.get('last_heartbeat')
    if last_hb:
        from datetime import datetime
        try:
            dt = datetime.strptime(last_hb, "%Y-%m-%d %H:%M:%S")
            diff = (datetime.now() - dt).total_seconds()
            if diff > 300: # > 5 mins
                score -= 10
        except:
            pass

    return max(0.0, min(100.0, score))

def calculate_capacity_utilization(total_sessions, uptime_percent):
    """
    Calculates the capacity utilization percentage (0-100).
    Assumes a max capacity of 500 sessions per reporting period.
    """
    if not total_sessions:
        return 0.0

    # Capacity is reduced if uptime is not 100%
    max_capacity = 500 * (uptime_percent / 100.0)
    utilization = (total_sessions / max_capacity) * 100

    return round(min(100.0, utilization), 1)
