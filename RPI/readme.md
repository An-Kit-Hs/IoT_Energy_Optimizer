# Index

1. System overview
2. Architecture
3. Data flow
4. Module-by-module documentation
5. Controller decision logic
6. MQTT integration
7. Configuration
8. Deployment & tuning
9. Future extensions

---

# 1. System Overview

This project implements an **intelligent indoor environment controller** that uses:

- **SEN55 environmental sensor data**
- **Computer vision occupancy detection**
- **MQTT messaging**
- **Predictive ventilation**
- **Occupancy-aware cooling**

The system automatically controls:

- **Air Conditioner**
- **Exhaust fan**

to maintain:

- good air quality
- human thermal comfort
- energy efficiency

---

# 2. High-Level Architecture

The architecture follows a layered model.

```
Sensors
   │
   │  (MQTT)
   ▼
Input Processing
   │
   ▼
Environmental Intelligence
   │
   ▼
Decision Controller
   │
   ▼
Device Controllers
   │
   ▼
AC / Exhaust
```

Each layer is isolated so that changes do not propagate across the entire system.

---

# 3. Data Flow

Example flow of one sensor update:

```
SEN55 → MQTT → main.py
             │
             ▼
      EnvironmentData
             │
             ▼
      SensorSmoother
             │
             ▼
        AQI Scorer
             │
             ▼
     Air Trend Detector
             │
             ▼
   Ventilation Predictor
             │
             ▼
      Comfort Calculator
             │
             ▼
     Occupancy Controller
             │
             ▼
   Environment Controller
             │
             ▼
        AC / Exhaust
```

---

# 4. Folder Structure

```
smart_hvac/
│
├── main.py
├── config.py
│
├── mqtt/
│   └── mqtt_client.py
│
├── sensors/
│   ├── environment_data.py
│   └── sensor_smoother.py
│
├── air_quality/
│   ├── aqi_scorer.py
│   ├── air_trend_detector.py
│   └── ventilation_predictor.py
│
├── comfort/
│   └── comfort_calculator.py
│
├── occupancy/
│   ├── occupancy_controller.py
│   ├── occupancy_state.py
│   ├── occupancy_pattern_model.py
│   └── occupancy_predictor.py
│
├── controllers/
│   ├── ac_controller.py
│   ├── exhaust_controller.py
│   ├── compressor_protection.py
│   └── environment_controller.py
│
└── utils/
    ├── moving_average.py
    └── time_utils.py
```

---

# 5. Core Modules

---

# sensors/environment_data.py

## Purpose

Represents environmental readings from the SEN55 sensor.

## Class

```python
EnvironmentData
```

## Fields

| Field       | Type  | Description                      |
| ----------- | ----- | -------------------------------- |
| temperature | float | air temperature (°C)             |
| humidity    | float | relative humidity (%)            |
| nox_index   | float | NOx air quality index            |
| voc_index   | float | VOC index                        |
| pm2_5       | float | particulate matter concentration |

## Example

```
temperature = 29.2°C
humidity = 68%
pm2_5 = 12 µg/m³
```

---

# sensors/sensor_smoother.py

## Purpose

Removes noise from sensor readings using **moving averages**.

Environmental sensors fluctuate frequently, and raw values cause unstable control decisions.

## Algorithm

Rolling mean:

```
smoothed_value = average(last N samples)
```

Default window size = **5 samples**

## Example

Raw:

```
29.0
29.4
30.1
29.3
28.9
```

Smoothed:

```
29.34
```

---

# utils/moving_average.py

Generic utility for rolling average.

Used by:

- temperature smoothing
- humidity smoothing
- pollutant smoothing

Implementation uses:

```
collections.deque
```

which keeps fixed memory.

---

# air_quality/aqi_scorer.py

## Purpose

Combines multiple pollutants into a **single air quality score**.

Pollutants considered:

- PM2.5
- VOC
- NOx

## Scoring formula

```
AQI = PM25*0.5 + VOC*0.3 + NOX*0.2
```

PM2.5 receives the highest weight because it has the largest health impact.

## AQI Interpretation

| Score | Meaning   |
| ----- | --------- |
| 0–25  | Excellent |
| 25–50 | Moderate  |
| 50–75 | Poor      |
| 75+   | Dangerous |

---

# air_quality/air_trend_detector.py

## Purpose

Detects **rapid air quality deterioration**.

Uses a sliding window of **6 AQI samples**.

```
trend = newest_score - oldest_score
```

If trend > 15 → pollution increasing.

This allows **predictive ventilation** before air becomes hazardous.

---

# air_quality/ventilation_predictor.py

## Purpose

Determines when to activate ventilation.

### Rules

Ventilation activates when:

```
AQI > 75
```

OR

```
trend rising AND AQI > 55
```

This avoids waiting until air becomes unhealthy.

---

# comfort/comfort_calculator.py

## Purpose

Calculates **human perceived temperature**.

Uses the **heat index formula**.

Humidity increases perceived temperature significantly.

Example:

```
30°C @ 70% humidity
feels like ≈ 36°C
```

Used to determine cooling decisions.

---

# occupancy subsystem

This module manages room occupancy behaviour.

---

# occupancy_state.py

Tracks real-time room occupancy.

Problem solved:

People briefly leaving should not instantly disable AC.

Logic:

```
If no people detected:
   wait 5 minutes
   then mark room empty
```

---

# occupancy_pattern_model.py

Learns **daily occupancy habits**.

Example data structure:

```
hour → probability of occupancy
```

Example:

```
18:00 → 0.9
03:00 → 0.05
```

Used for **pre-cooling prediction**.

---

# occupancy_predictor.py

Uses learned patterns to decide if room should be cooled before occupancy.

Rule:

```
if occupancy_probability > 0.6
    precool room
```

---

# occupancy_controller.py

Central interface for occupancy logic.

Returns:

```
{
  occupied: bool,
  probability: float,
  precool: bool
}
```

---

# controllers/compressor_protection.py

Protects the AC compressor.

Short-cycling damages compressors.

Constraints enforced:

```
minimum OFF time = 3 minutes
minimum ON time = 3 minutes
```

---

# controllers/ac_controller.py

Handles AC commands.

Publishes MQTT commands:

```
home/ac/set
```

Example message:

```
{
 "power": "ON",
 "target_temp": 24
}
```

---

# controllers/exhaust_controller.py

Controls ventilation fan.

Topic:

```
home/exhaust/set
```

Message:

```
{
 "power": "ON"
}
```

---

# controllers/environment_controller.py

This is the **brain of the system**.

It integrates:

- air quality
- thermal comfort
- occupancy
- predictive ventilation

## Decision Priority

### 1 Air emergency

```
AQI > 75
```

Actions:

```
AC OFF
EXHAUST ON
```

---

### 2 Predictive ventilation

```
trend rising
```

Action:

```
Exhaust ON
```

---

### 3 Exhaust safety rule

If exhaust running:

```
AC OFF
```

to avoid energy waste.

---

### 4 Occupied comfort control

Maintain perceived temperature around:

```
24°C
```

with tolerance:

```
±1.5°C
```

---

### 5 Predicted occupancy

Room pre-cooled to:

```
27°C
```

---

### 6 Empty room

```
AC OFF
```

Energy saving mode.

---

# main.py

Main entry point.

Responsibilities:

- connect to MQTT
- subscribe to sensor topics
- route messages to controller

Topics subscribed:

```
home/sensors/sen55
cam/occupancy
```

---

# MQTT Data Format

## Sensor message

```
{
 "temperature": 29.3,
 "humidity": 72,
 "nox": 110,
 "voc": 80,
 "pm2_5": 15
}
```

---

## Occupancy message

```
{
 "payload": 2
}
```

---

# Configuration

All system parameters are stored in `config.py`.

Example:

```
COMFORT_TEMP = 24
ECO_TEMP = 27
TEMP_BAND = 1.5
```

This allows easy tuning.

---

# Deployment

Typical hardware:

```
Raspberry Pi / Jetson Nano
SEN55 sensor
MQTT broker (Mosquitto)
Camera occupancy detector
```

Steps:

1 install dependencies

```
pip install paho-mqtt numpy
```

2 start MQTT broker

```
mosquitto
```

3 run system

```
python main.py
```

---

# Tuning Guide

Recommended adjustments:

| Parameter            | Typical Value |
| -------------------- | ------------- |
| comfort temp         | 23–25°C       |
| eco temp             | 26–28°C       |
| AQI danger threshold | 75            |
| trend threshold      | 15            |

---

# Future Improvements

The system can be significantly enhanced with:

### Thermal room model

Predict how fast room heats/cools.

### CO₂ estimation

Use VOC + occupancy to approximate CO₂ levels.

### PID temperature control

Instead of binary AC switching.

### Reinforcement learning comfort tuning

Learn preferred temperature automatically.

### Weather integration

Precool based on outdoor heat.

---

# Summary

This system implements a **modular intelligent HVAC controller** combining:

- environmental sensing
- occupancy detection
- predictive air quality management
- comfort optimization
- compressor protection
