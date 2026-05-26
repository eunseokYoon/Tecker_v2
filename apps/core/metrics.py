from prometheus_client import Counter, Histogram

BOOKING_ATTEMPTS = Counter(
    "booking_attempts_total",
    "Booking attempt results",
    ["result"],
)

BOOKING_LATENCY = Histogram(
    "booking_latency_seconds",
    "Booking transaction latency",
    buckets=(0.025, 0.05, 0.1, 0.2, 0.5, 1, 2, 5),
)

AWS_REK = Counter(
    "aws_rekognition_calls_total",
    "AWS Rekognition API calls",
    ["op"],
)

ANTISPOOF_OUTAGE = Counter(
    "antispoof_outage_total",
    "Antispoof service outage count",
)
