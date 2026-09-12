"""Validate MQTT readings and write trusted data to local InfluxDB."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Any

import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from dotenv import load_dotenv

from validation import validate_reading


load_dotenv()
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "dac/plant/readings")
INFLUX_URL = os.getenv("INFLUX_URL", "http://localhost:8086")
INFLUX_TOKEN = os.getenv("INFLUXDB_TOKEN")
INFLUX_ORG = os.getenv("INFLUXDB_ORG", "dac-learning")
INFLUX_BUCKET = os.getenv("INFLUXDB_BUCKET", "plant_readings")
REJECTED_LOG = Path("output/rejected_stream_records.csv")


def log_rejected(row: dict[str, Any], reasons: list[str]) -> None:
    REJECTED_LOG.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [*row.keys(), "rejection_reason"]
    is_new = not REJECTED_LOG.exists()
    with REJECTED_LOG.open("a", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        if is_new:
            writer.writeheader()
        writer.writerow({**row, "rejection_reason": "; ".join(reasons)})


def make_point(row: dict[str, Any]) -> Point:
    return (
        Point("plant_readings")
        .tag("plant_id", str(row["plant_id"]))
        .field("temperature_c", float(row["temperature_c"]))
        .field("pressure_kpa", float(row["pressure_kpa"]))
        .field("airflow_m3_h", float(row["airflow_m3_h"]))
        .field("co2_in_ppm", float(row["co2_in_ppm"]))
        .field("co2_out_ppm", float(row["co2_out_ppm"]))
        .field("fan_power_kw", float(row["fan_power_kw"]))
        .field("capture_rate_kg_h", float(row["capture_rate_kg_h"]))
        .field("co2_removed_ppm", float(row["co2_in_ppm"]) - float(row["co2_out_ppm"]))
        .time(str(row["timestamp_utc"]))
    )


def main() -> None:
    if not INFLUX_TOKEN:
        raise SystemExit("INFLUXDB_TOKEN is missing. Copy .env.example to .env.")
    influx_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    write_api = influx_client.write_api(write_options=SYNCHRONOUS)

    def on_message(_client, _userdata, message) -> None:
        try:
            row = json.loads(message.payload.decode("utf-8"))
            reasons = validate_reading(row)
            if reasons:
                log_rejected(row, reasons)
                print("REJECTED", reasons)
                return
            write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=make_point(row))
            print("STORED", row["timestamp_utc"])
        except (json.JSONDecodeError, UnicodeDecodeError, KeyError, TypeError, ValueError) as error:
            print("MESSAGE ERROR", error)

    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqtt_client.on_message = on_message
    mqtt_client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    mqtt_client.subscribe(MQTT_TOPIC, qos=1)
    print(f"Listening on {MQTT_TOPIC}. Press Ctrl+C to stop.")
    try:
        mqtt_client.loop_forever()
    except KeyboardInterrupt:
        print("Stopped.")
    finally:
        influx_client.close()


if __name__ == "__main__":
    main()
