import fakeredis

from app.core.ratelimit import check_rate_limit
from tests.clock import FakeClock


def test_allows_requests_up_to_capacity(fake_redis: fakeredis.FakeRedis, clock: FakeClock) -> None:
    for expected_remaining in (2, 1, 0):
        allowed, remaining = check_rate_limit("key-a", capacity=3, refill_rate=1.0)
        assert allowed is True
        assert remaining == expected_remaining


def test_rejects_when_bucket_is_empty(fake_redis: fakeredis.FakeRedis, clock: FakeClock) -> None:
    for _ in range(3):
        check_rate_limit("key-a", capacity=3, refill_rate=1.0)

    allowed, remaining = check_rate_limit("key-a", capacity=3, refill_rate=1.0)

    assert allowed is False
    assert remaining == 0


def test_tokens_refill_over_time(fake_redis: fakeredis.FakeRedis, clock: FakeClock) -> None:
    for _ in range(3):
        check_rate_limit("key-a", capacity=3, refill_rate=1.0)

    clock.advance(2.0)
    allowed, remaining = check_rate_limit("key-a", capacity=3, refill_rate=1.0)

    assert allowed is True
    assert remaining == 1  # 2 tokens refilled, 1 consumed


def test_refill_is_capped_at_capacity(fake_redis: fakeredis.FakeRedis, clock: FakeClock) -> None:
    check_rate_limit("key-a", capacity=3, refill_rate=1.0)

    clock.advance(100.0)
    allowed, remaining = check_rate_limit("key-a", capacity=3, refill_rate=1.0)

    assert allowed is True
    assert remaining == 2  # bucket refills to capacity (3), never beyond


def test_buckets_are_isolated_per_key(fake_redis: fakeredis.FakeRedis, clock: FakeClock) -> None:
    for _ in range(3):
        check_rate_limit("key-a", capacity=3, refill_rate=1.0)

    allowed, _ = check_rate_limit("key-b", capacity=3, refill_rate=1.0)

    assert allowed is True
