"""
StepManiaX B2B ROI Calculator (v1.4.0)
Utilizes the shared analytics module to project financial impact.
"""
from analytics import calculate_detailed_metrics

if __name__ == "__main__":
    # Example: 10 Club Regional Deployment with 3% Retention Lift
    results = calculate_detailed_metrics(num_clubs=10, members_per_club=6000, retention_lift_percent=0.03)

    print("   StepManiaX Regional ROI Projection (LTV Model)")
    print(f"Total Portfolio Members: {results['total_members']}")
    print(f"Base Member LTV: ${results['base_ltv']}")
    print(f"Lifted Member LTV (3% Lift): ${results['lifted_ltv']}")
    print(f"Projected Annual Revenue Gain: ${results['annual_revenue_gain']}")
    print(f"Projected Annual Net Profit: ${results['annual_net_profit']}")
    print(f"ROI Multiple: {results['roi_multiple']}x")
