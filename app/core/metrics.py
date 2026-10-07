from prometheus_client import Counter, Histogram

chat_requests_total = Counter(
    "chat_requests_total",
    "Total number of /v1/chat requests",
    ["provider", "model", "cached"],
)

chat_request_duration_seconds = Histogram(
    "chat_request_duration_seconds",
    "Duration of /v1/chat requests in seconds",
    ["provider", "model"],
)

rate_limit_rejections_total = Counter(
    "rate_limit_rejections_total",
    "Total number of requests rejected by rate limiting",
    ["api_key"],
)
