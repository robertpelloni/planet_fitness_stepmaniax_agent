"""
Shared Analytical Module for StepManiaX B2B Sales Agent.
Provides consolidated ROI and Lifetime Value (LTV) calculation logic.
"""

def calculate_detailed_metrics(
    num_clubs=1,
    members_per_club=6000,
    avg_monthly_fee=15.0,
    retention_lift_percent=0.03,
    avg_member_lifetime_months=18,
    smx_monthly_cost_per_club=600.0
):
    """
    Calculates comprehensive ROI metrics using the LTV framework.
    """
    total_members = num_clubs * members_per_club

    # 1. Base LTV Analysis
    base_ltv = avg_monthly_fee * avg_member_lifetime_months
    base_total_portfolio_value = total_members * base_ltv

    # 2. Lifted LTV Analysis
    lifted_lifetime_months = avg_member_lifetime_months * (1 + retention_lift_percent)
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
