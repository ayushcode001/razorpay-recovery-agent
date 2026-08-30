"""
Generates synthetic time-series payment failure counts with seasonal patterns and injected outages.

Simulates 30 days (720 hours) across bank x payment method channels.
Includes:
  - Diurnal volume cycles (daytime 9am-9pm peak vs off-peak night)
  - Day-of-week volume cycles (weekday vs weekend)
  - Baseline normal failure rate (~3-6% depending on instrument)
  - 3 Ground-truth injected system degradation anomalies (outages) for evaluation:
      1. HDFC + card outage on Day 8 (hours 14-20): failure rate spikes to ~42%
      2. SBI + netbanking outage on Day 15 (hours 2-6): failure rate spikes to ~55%
      3. ICICI + upi degradation on Day 22 (hours 10-13): failure rate spikes to ~30%
"""

import os
import sys
import json
import random
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "data", "failure_rate_timeseries.json")

random.seed(42)
np.random.seed(42)

BANKS = ["HDFC", "ICICI", "SBI", "Axis", "Kotak"]
METHODS = ["card", "upi", "netbanking"]

# Base failure rate per method under normal conditions
NORMAL_FAILURE_RATES = {
    "card": 0.045,
    "upi": 0.038,
    "netbanking": 0.055,
}

# Average transaction ticket size per channel in INR
AVG_AMOUNTS = {
    "card": 3200,
    "upi": 950,
    "netbanking": 8500,
}

# Injected ground truth outages for degradation agent validation
INJECTED_ANOMALIES = [
    {
        "id": "outage_hdfc_card_d8",
        "bank": "HDFC",
        "method": "card",
        "day": 8,
        "hours": list(range(14, 21)),  # 14 to 20 (7 hours)
        "target_failure_rate": 0.42,
        "description": "HDFC Issuer Card Gateway Latency Spike",
    },
    {
        "id": "outage_sbi_netbanking_d15",
        "bank": "SBI",
        "method": "netbanking",
        "day": 15,
        "hours": list(range(2, 7)),  # 2 to 6 (5 hours)
        "target_failure_rate": 0.55,
        "description": "SBI Core Banking Nightly Maintenance Timeout",
    },
    {
        "id": "outage_icici_upi_d22",
        "bank": "ICICI",
        "method": "upi",
        "day": 22,
        "hours": list(range(10, 14)),  # 10 to 13 (4 hours)
        "target_failure_rate": 0.30,
        "description": "ICICI UPI PSP Server Error Surge",
    },
]


def is_injected(bank, method, day, hour):
    for a in INJECTED_ANOMALIES:
        if a["bank"] == bank and a["method"] == method and a["day"] == day and hour in a["hours"]:
            return a
    return None


def generate_timeseries(days=30):
    records = []
    
    for day in range(1, days + 1):
        day_of_week = (day - 1) % 7  # 0=Mon, ..., 5=Sat, 6=Sun
        is_weekend = day_of_week in (5, 6)
        weekend_multiplier = 0.75 if is_weekend else 1.0

        for hour in range(24):
            # Diurnal multiplier: peak daytime (9am - 9pm), low at 2am-5am
            if 9 <= hour <= 21:
                diurnal_mult = 1.0 + 0.6 * np.sin((hour - 9) / 12 * np.pi)
            else:
                diurnal_mult = 0.25 + 0.2 * np.cos((hour - 3) / 6 * np.pi)

            for bank in BANKS:
                for method in METHODS:
                    # Skip non-sensical combos if any
                    base_rate = NORMAL_FAILURE_RATES[method]
                    avg_amt = AVG_AMOUNTS[method] * (1.0 + random.uniform(-0.1, 0.1))

                    # Channel baseline traffic volume
                    base_volume = 300 if method == "upi" else (200 if method == "card" else 80)
                    volume = int(base_volume * diurnal_mult * weekend_multiplier * random.uniform(0.85, 1.15))
                    volume = max(15, volume)

                    # Check for injected anomaly
                    anomaly_meta = is_injected(bank, method, day, hour)
                    if anomaly_meta:
                        failure_rate = anomaly_meta["target_failure_rate"] + random.uniform(-0.03, 0.03)
                        is_anomaly = True
                        anomaly_desc = anomaly_meta["description"]
                    else:
                        # Normal noise around baseline
                        failure_rate = base_rate + random.gauss(0, 0.008)
                        failure_rate = max(0.01, min(0.12, failure_rate))
                        is_anomaly = False
                        anomaly_desc = None

                    failed_count = int(round(volume * failure_rate))
                    failed_count = min(volume, max(0, failed_count))
                    actual_rate = round(failed_count / volume, 4)

                    record = {
                        "day": day,
                        "day_of_week": day_of_week,
                        "hour": hour,
                        "timestamp_hour_index": (day - 1) * 24 + hour,
                        "bank": bank,
                        "method": method,
                        "total_transactions": volume,
                        "failed_transactions": failed_count,
                        "failure_rate": actual_rate,
                        "avg_amount": round(avg_amt, 2),
                        "is_injected_anomaly": is_anomaly,
                        "anomaly_description": anomaly_desc,
                    }
                    records.append(record)

    return records


if __name__ == "__main__":
    records = generate_timeseries(days=30)
    os.makedirs(os.path.dirname(os.path.abspath(OUTPUT_PATH)), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(records, f, indent=2)

    total_records = len(records)
    total_anomalies = sum(1 for r in records if r["is_injected_anomaly"])
    print(f"Generated {total_records} hourly timeseries records ({30} days) -> {OUTPUT_PATH}")
    print(f"Injected anomaly windows: {total_anomalies} hours across 3 distinct outage scenarios.")
