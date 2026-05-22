"""
StepManiaX B2B ROI Calculator
Calculates the potential financial impact of deploying StepManiaX units based on
member retention lift and increased visit frequency.
"""

def calculate_roi(
    num_clubs=1,
    members_per_club=5000,
    monthly_membership_fee=10.0,
    retention_lift_percent=0.02, # e.g., 2% increase in retention
    avg_member_lifetime_months=18,
    smx_monthly_cost_per_club=500.0 # Estimated lease/maintenance cost
):
    """
    Calculates monthly and annual ROI for a StepManiaX deployment.
    """
    total_members = num_clubs * members_per_club

    # 1. Retention Impact
    # Number of members saved from cancelling per month (hypothetical)
    # Average monthly churn is 1 / member_lifetime
    base_monthly_churn_rate = 1.0 / avg_member_lifetime_months
    members_saved_per_month = total_members * (base_monthly_churn_rate * retention_lift_percent)

    # Monthly revenue saved
    revenue_saved_per_month = members_saved_per_month * monthly_membership_fee

    # 2. Costs
    total_monthly_cost = num_clubs * smx_monthly_cost_per_club

    # 3. Final ROI
    monthly_net_profit = revenue_saved_per_month - total_monthly_cost
    annual_net_profit = monthly_net_profit * 12

    return {
        "total_members": total_members,
        "members_saved_per_year": round(members_saved_per_month * 12),
        "monthly_revenue_saved": round(revenue_saved_per_month, 2),
        "monthly_net_profit": round(monthly_net_profit, 2),
        "annual_net_profit": round(annual_net_profit, 2),
        "roi_multiple": round(revenue_saved_per_month / total_monthly_cost, 2) if total_monthly_cost > 0 else 0
    }

if __name__ == "__main__":
    # Example: 10 Club Regional Deployment
    results = calculate_roi(num_clubs=10, members_per_club=6000, retention_lift_percent=0.03)

    print("===========================================================")
    print("   StepManiaX Regional ROI Projection (10 Clubs)")
    print("===========================================================")
    print(f"Total Portfolio Members: {results['total_members']}")
    print(f"Members Saved Per Year (via 3% Retention Lift): {results['members_saved_per_year']}")
    print(f"Monthly Revenue Saved: ${results['monthly_revenue_saved']}")
    print(f"Monthly Net Profit (After Costs): ${results['monthly_net_profit']}")
    print(f"Annual Net Profit: ${results['annual_net_profit']}")
    print(f"ROI Multiple: {results['roi_multiple']}x")
    print("===========================================================")
