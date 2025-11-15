import pytest


@pytest.mark.parametrize(
    "volume,ranges,status",
    [
        (10, {"min": 5, "max": 15}, "optimal"),
        (18, {"min": 5, "max": 15}, "high"),
        (10, {"min": 15, "max": 18}, "low"),
    ],
)
def test_calculate_volume_custom_ranges(client, volume, ranges, status):
    response = client.post(
        "/api/calculate_volume",
        json={
            "mode": "basic",
            "training_days": 3,
            "volumes": {"Chest": volume},
            "ranges": {"Chest": ranges},
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    chest_result = payload["results"].get("Chest")

    assert chest_result is not None
    assert chest_result["status"] == status


def test_calculate_volume_sanitizes_ranges(client):
    response = client.post(
        "/api/calculate_volume",
        json={
            "mode": "basic",
            "training_days": 3,
            "volumes": {"Chest": 10},
            "ranges": {"Chest": {"min": -5, "max": 8}},
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    chest_range = payload["ranges"].get("Chest")
    chest_result = payload["results"].get("Chest")

    assert chest_range is not None
    assert pytest.approx(chest_range["min"]) == 12
    assert pytest.approx(chest_range["max"]) == 12
    assert chest_result["status"] == "low"
