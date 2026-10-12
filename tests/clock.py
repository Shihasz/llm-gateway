class FakeClock:
    """Controllable replacement for the `time` module, so rate-limit tests are deterministic."""

    def __init__(self, start: float = 1_000.0) -> None:
        self.now = start

    def time(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds
