import analytics

def test_propensity_intent_boost():
    # Base lead data
    lead_data = {
        'num_clubs': 5,
        'region': 'Michigan',
        'status': 'Ready for Outreach',
        'priority': 'Medium',
        'portal_views': 0,
        'avg_feedback_rating': 4.5,
        'notes': ""
    }

    score_base = analytics.calculate_propensity_score(lead_data)
    print(f"Base Score: {score_base}")

    # High Intent boost
    lead_data['notes'] = "HIGH INTENT: Prospect interacted with ROI Simulator."
    score_boosted = analytics.calculate_propensity_score(lead_data)
    print(f"Boosted Score: {score_boosted}")

    assert score_boosted == min(100, score_base + 30)
    print("Propensity Intent Boost Verified.")

if __name__ == "__main__":
    test_propensity_intent_boost()
