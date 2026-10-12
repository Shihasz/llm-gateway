from fastapi.testclient import TestClient

from tests.clock import FakeClock

HEADERS = {"X-API-Key": "test-key"}


def test_health(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_lists_registered_providers(client: TestClient) -> None:
    response = client.get("/v1/providers")

    assert response.status_code == 200
    assert "mock" in response.json()["providers"]


def test_chat_requires_api_key(client: TestClient) -> None:
    response = client.post("/v1/chat", json={"prompt": "hi"})

    assert response.status_code == 401


def test_chat_cache_miss_then_hit(client: TestClient) -> None:
    first = client.post("/v1/chat", json={"prompt": "hello"}, headers=HEADERS)
    second = client.post("/v1/chat", json={"prompt": "hello"}, headers=HEADERS)

    assert first.status_code == 200
    assert first.json()["cached"] is False
    assert second.status_code == 200
    assert second.json()["cached"] is True
    assert second.json()["text"] == first.json()["text"]


def test_unknown_provider_returns_400(client: TestClient) -> None:
    response = client.post(
        "/v1/chat",
        json={"prompt": "hi", "provider": "does-not-exist", "model": "x"},
        headers=HEADERS,
    )

    assert response.status_code == 400


def test_fallback_serves_request_when_primary_fails(client: TestClient) -> None:
    response = client.post(
        "/v1/chat",
        json={
            "prompt": "fallback test",
            "provider": "mock-failing",
            "model": "x",
            "fallbacks": [{"provider": "mock", "model": "mock-model"}],
        },
        headers=HEADERS,
    )

    assert response.status_code == 200
    assert response.json()["provider"] == "mock"
    assert response.json()["fallback_used"] is True


def test_returns_502_when_all_providers_fail(client: TestClient) -> None:
    response = client.post(
        "/v1/chat",
        json={"prompt": "all fail", "provider": "mock-failing", "model": "x"},
        headers=HEADERS,
    )

    assert response.status_code == 502


def test_rate_limit_returns_429_after_capacity(client: TestClient, clock: FakeClock) -> None:
    statuses = [
        client.post("/v1/chat", json={"prompt": f"prompt {i}"}, headers=HEADERS).status_code
        for i in range(11)
    ]

    assert statuses[:10] == [200] * 10
    assert statuses[10] == 429


def test_usage_counts_requests_and_cache_hits(client: TestClient) -> None:
    for _ in range(2):
        client.post("/v1/chat", json={"prompt": "usage test"}, headers=HEADERS)

    usage = client.get("/v1/usage").json()["usage"]

    assert len(usage) == 1
    assert usage[0]["provider"] == "mock"
    assert usage[0]["requests"] == 2
    assert usage[0]["cache_hits"] == 1
