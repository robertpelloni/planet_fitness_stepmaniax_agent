"""
Shared Analytical Module for StepManiaX B2B Sales Agent.
Provides consolidated ROI and Lifetime Value (LTV) calculation logic.
"""

import config

def calculate_detailed_metrics(
    num_clubs=1,
    members_per_club=6000,
    avg_monthly_fee=config.DEFAULT_MONTHLY_FEE,
    retention_lift_percent=config.DEFAULT_RETENTION_LIFT,
    avg_member_lifetime_months=18,
    smx_monthly_cost_per_club=600.0,
    onboarding_conversion_rate=1.0 # 1.0 = 100%
):
    """
    Calculates comprehensive ROI metrics using the LTV framework.
    """
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
    num_clubs = lead_data.get('num_clubs', 1)
    if num_clubs > 100: score += 20
    elif num_clubs > 50: score += 15
    elif num_clubs > 20: score += 10

    # 2. Regional Priority (Michigan/Midwest)
    region = lead_data.get('region', '').lower()
    if 'michigan' in region or 'mi' == region: score += 15
    elif 'ohio' in region or 'midwest' in region: score += 10

    # 3. Status Bonus (Further down the funnel = higher propensity)
    status = lead_data.get('status', 'Identified')
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
