import os

# Production sign-in is Google only (EXCHANGE_AUTH_METHODS defaults to "google"); the suite
# exercises every method, so it opts in once here before any app is created.
os.environ.setdefault("EXCHANGE_AUTH_METHODS", "email,google,facebook")
# Request-count flushing runs on a background thread in production; tests flush explicitly instead.
os.environ.setdefault("EXCHANGE_ANALYTICS_FLUSH_SECONDS", "0")
