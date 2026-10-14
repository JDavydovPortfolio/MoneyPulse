from src.underwriting import UnderwritingPrecheck


def document(**overrides):
    base = {
        "requested_amount": "$75,000",
        "business_info": {
            "annual_revenue": "$525,000",
            "processing_volume": "$48,000",
            "years_in_business": "4",
        },
    }
    base.update(overrides)
    return base


def test_signals_only_computes_underwriting_metrics():
    result = UnderwritingPrecheck().evaluate(document())

    assert result["mode"] == "signals_only"
    assert result["status"] == "ready"
    assert result["preliminary_recommendation"] == "not_configured"
    assert result["metrics"]["requested_amount"] == 75000.0
    assert result["metrics"]["annual_revenue"] == 525000.0
    assert result["metrics"]["request_to_annual_revenue"] == 0.1429
    assert result["metrics"]["request_to_processing_volume"] == 1.5625


def test_policy_can_advance_when_all_configured_rules_pass():
    policy = {
        "min_years_in_business": 2,
        "min_annual_revenue": 300000,
        "min_processing_volume": 30000,
        "max_request_to_annual_revenue": 0.20,
        "max_request_to_processing_volume": 2.0,
    }

    result = UnderwritingPrecheck(policy).evaluate(document())

    assert result["mode"] == "policy"
    assert result["preliminary_recommendation"] == "advance"
    assert all(rule["result"] == "pass" for rule in result["rules"])


def test_policy_routes_failed_rule_to_manual_review():
    policy = {"max_request_to_annual_revenue": 0.10}

    result = UnderwritingPrecheck(policy).evaluate(document())

    assert result["preliminary_recommendation"] == "manual_review"
    assert result["rules"][0]["result"] == "fail"


def test_policy_reports_missing_data_instead_of_guessing():
    policy = {"min_annual_revenue": 300000}
    data = document()
    data["business_info"]["annual_revenue"] = ""

    result = UnderwritingPrecheck(policy).evaluate(data)

    assert result["status"] == "partial"
    assert result["preliminary_recommendation"] == "needs_more_data"
    assert result["rules"][0]["result"] == "missing_data"
