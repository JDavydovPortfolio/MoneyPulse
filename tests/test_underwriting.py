from src.underwriting import UnderwritingMetrics


def document(**overrides):
    base = {
        "requested_amount": "$75,000",
        "business_info": {
            "annual_revenue": "$525,000",
            "processing_volume": "$48,000",
            "years_in_business": "4",
        },
        "review_approved": False,
        "review_state": "ready_for_review",
    }
    base.update(overrides)
    return base


def test_metrics_are_not_calculated_before_human_approval():
    result = UnderwritingMetrics().evaluate(document())

    assert result == {"status": "awaiting_review", "metrics": {}}


def test_reviewed_explicit_values_can_feed_deterministic_ratios():
    result = UnderwritingMetrics().evaluate(
        document(review_approved=True, review_state="approved")
    )

    assert result["status"] == "calculated"
    assert result["inputs"]["requested_amount"] == 75000.0
    assert result["inputs"]["annual_revenue"] == 525000.0
    assert result["inputs"]["processing_volume"] == 48000.0
    assert result["inputs"]["years_in_business"] == 4.0
    assert result["metrics"]["request_to_annual_revenue"] == 0.1429
    assert result["metrics"]["request_to_processing_volume"] == 1.5625


def test_missing_reviewed_values_are_not_inferred():
    data = document(review_approved=True, review_state="approved")
    data["business_info"]["annual_revenue"] = ""

    result = UnderwritingMetrics().evaluate(data)

    assert result["status"] == "calculated"
    assert result["inputs"]["annual_revenue"] is None
    assert result["metrics"]["request_to_annual_revenue"] is None
