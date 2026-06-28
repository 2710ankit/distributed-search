"""Simple search latency benchmark. Run after seeding data."""

import statistics
import time

import requests

BASE_URL = "http://localhost:8000"
TENANT = "netflix"
QUERY = "revenue"
REQUESTS = 50


def main():
    latencies = []

    for _ in range(REQUESTS):
        start = time.perf_counter()
        response = requests.get(
            f"{BASE_URL}/search",
            params={"q": QUERY, "tenant": TENANT, "page_size": 10},
            timeout=5,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        latencies.append(elapsed_ms)
        response.raise_for_status()

    latencies.sort()
    p50 = latencies[int(len(latencies) * 0.50)]
    p95 = latencies[int(len(latencies) * 0.95)]
    p99 = latencies[int(len(latencies) * 0.99)]

    print(f"Requests: {REQUESTS}")
    print(f"Query: {QUERY}")
    print(f"Mean:   {statistics.mean(latencies):.1f} ms")
    print(f"p50:    {p50:.1f} ms")
    print(f"p95:    {p95:.1f} ms")
    print(f"p99:    {p99:.1f} ms")


if __name__ == "__main__":
    main()
