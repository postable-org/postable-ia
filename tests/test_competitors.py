from postable_ia.services.competitors import build_gap_candidates


def test_build_gap_candidates():
    candidates = build_gap_candidates(
        [
            {
                "handle": "@RivalOne",
                "status": "active",
                "themes": {"delivery speed": 0.20},
                "theme_signals": {
                    "delivery speed": {
                        "trend_momentum": 0.70,
                        "brand_fit": 0.82,
                        "confidence": 0.90,
                        "novelty_penalty": 0.03,
                    }
                },
            },
            {
                "handle": "RivalTwo",
                "status": "active",
                "themes": {"delivery speed": 0.40},
                "theme_signals": {
                    "delivery speed": {
                        "trend_momentum": 0.50,
                        "brand_fit": 0.78,
                        "confidence": 0.80,
                    }
                },
            },
        ]
    )

    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.theme == "delivery speed"
    assert round(candidate.signal.gap_strength, 2) == 0.70
    assert round(candidate.signal.trend_momentum, 2) == 0.60
    assert round(candidate.signal.brand_fit, 2) == 0.80
    assert round(candidate.signal.confidence, 2) == 0.85
    assert candidate.competitors_considered == ["@rivalone", "@rivaltwo"]


def test_handle_statuses_are_preserved():
    candidates = build_gap_candidates(
        [
            {"handle": "@ActiveOne", "status": "active", "themes": {"x": 0.1}},
            {"handle": "@PrivateOne", "status": "private", "themes": {"x": 0.4}},
            {
                "handle": "@OldOne",
                "status": "replaced",
                "replacement_handle": "@NewOne",
                "themes": {},
            },
        ]
    )
    statuses = {item.handle: item for item in candidates[0].competitor_statuses}
    assert statuses["@activeone"].status == "active"
    assert statuses["@privateone"].status == "private"
    assert statuses["@oldone"].status == "replaced"
    assert statuses["@oldone"].replacement_handle == "@newone"


def test_locality_basis_state_is_preserved():
    candidates = build_gap_candidates(
        [
            {
                "handle": "@RivalOne",
                "status": "active",
                "themes": {"healthy snacks": 0.25},
                "locality_basis": "state",
                "locality_state_key": "BR-SP",
            }
        ],
        locality_basis="state",
        locality_state_key="BR-SP",
    )

    assert candidates[0].locality_basis == "state"
    assert candidates[0].locality_state_key == "BR-SP"
