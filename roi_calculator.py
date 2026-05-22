"""
StepManiaX B2B ROI Calculator (v1.2.0)
Calculates the potential financial impact of deploying StepManiaX units based on
Member Lifetime Value (LTV), retention lift, and tiered membership models.
"""

def calculate_roi(
    num_clubs=1,
    members_per_club=5000,
    avg_monthly_fee=15.0, # Blended rate between Classic and Black Card
    retention_lift_percent=0.03, # Increase in average member lifetime
    avg_member_lifetime_months=18,
    smx_monthly_cost_per_club=600.0 # Lease + Maintenance + Software
):
    """
    Calculates portfolio-wide ROI using Member Lifetime Value (LTV).
    """
    total_members = num_clubs * members_per_club

    # 1. Base LTV Analysis
    base_ltv = avg_monthly_fee * avg_member_lifetime_months
    base_total_portfolio_value = total_members * base_ltv

    # 2. Lifted LTV Analysis
    # Retention lift increases the average lifetime (in months)
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

if __name__ == "__main__":
    # Example: 10 Club Regional Deployment with 3% Retention Lift
    results = calculate_roi(num_clubs=10, members_per_club=6000, retention_lift_percent=0.03)

    print("===========================================================")
    print("   StepManiaX Regional ROI Projection (LTV Model)")
    print("===========================================================")
    print(f"Total Portfolio Members: {results['total_members']}")
    print(f"Base Member LTV: ${results['base_ltv']}")
    print(f"Lifted Member LTV (3% Lift): ${results['lifted_ltv']}")
    print(f"Projected Annual Revenue Gain: ${results['annual_revenue_gain']}")
    print(f"Projected Annual Net Profit: ${results['annual_net_profit']}")
    print(f"ROI Multiple: {results['roi_multiple']}x")
    print("===========================================================")
