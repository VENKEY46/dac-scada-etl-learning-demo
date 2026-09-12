# Verified Live Demonstration

The live extension was tested locally with Docker Desktop.

## Confirmed flow

1. `simulate_plant_stream.py` published synthetic readings every five seconds.
2. Mosquitto carried the readings through the MQTT topic `dac/plant/readings`.
3. `ingest_stream.py` applied the shared validation rules.
4. Valid readings were stored in InfluxDB.
5. Deliberately injected temperature and CO2-logic faults were rejected and logged.
6. Grafana refreshed the accepted readings every five seconds.

The live data remains in the local InfluxDB Docker volume and can be recreated by rerunning the simulator. Generated database storage is not committed to Git.

