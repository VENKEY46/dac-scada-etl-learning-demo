"""Publish synthetic DAC plant readings to a local MQTT broker."""

from __future__ import annotations

import json
import os
import random
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt


MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "dac/plant/readings")
INTERVAL_SECONDS = float(os.getenv("STREAM_INTERVAL_SECONDS", "5"))


def make_reading(inject_fault: bool = False) -> dict[str, object]:
    co2_in = round(random.uniform(400, 480), 1)
    co2_out = round(co2_in * random.uniform(0.55, 0.75), 1)
    temperature = round(random.uniform(15, 35), 1)
    if inject_fault:
        if random.choice(("temperature", "co2_logic")) == "temperature":
            temperature = round(random.uniform(150, 250), 1)
        else:
            co2_out = co2_in + 20
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "plant_id": "DAC-DEMO-01",
        "temperature_c": temperature,
        "pressure_kpa": round(random.uniform(98, 103), 1),
        "airflow_m3_h": round(random.uniform(3000, 7000), 1),
        "co2_in_ppm": co2_in,
        "co2_out_ppm": co2_out,
        "fan_power_kw": round(random.uniform(5, 20), 2),
        "capture_rate_kg_h": round(random.uniform(2, 10), 2),
    }


def main() -> None:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    client.loop_start()
    print(f"Publishing synthetic readings to {MQTT_TOPIC}. Press Ctrl+C to stop.")
    try:
        while True:
            reading = make_reading(inject_fault=random.random() < 0.15)
            result = client.publish(MQTT_TOPIC, json.dumps(reading), qos=1)
            result.wait_for_publish()
            print("SENT", reading)
            time.sleep(INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("Stopped.")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()

