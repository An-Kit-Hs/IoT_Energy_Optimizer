# Air Quality Module

## Overview

The Air Quality Module processes environmental sensor data to evaluate indoor air quality and decide whether ventilation is required.

It provides:

- AQI score
- Air quality trend (rising / stable)
- Ventilation recommendation

---

## Usage

```python
from air_quality_module import AirQualityModule

air = AirQualityModule()

result = air.update(sensor_data)
```

---

## Output

```python
{
    "score": float,
    "trend_rising": bool,
    "ventilate": bool
}
```

---

## Components

### IAQScorer

Calculates overall air quality score based on:

- PM2.5
- VOC index
- NOx index

#### Scoring Logic

```python
AQI = PM * 0.5 + VOC * 0.3 + NOx * 0.2
```

- PM2.5 uses threshold-based scoring
- VOC and NOx are normalized

---

### AirTrendDetector

Detects whether air quality is deteriorating over time.

- Maintains a sliding window (default: 6 samples)
- Computes trend:

```python
trend = latest - oldest
```

- Rising trend if:

```python
trend > threshold (default: 15)
```

---

### VentilationPredictor

Determines when to activate ventilation.

#### Rules

```python
if score > 75:
    ventilate = True
```

```python
if trend_rising and score > 55:
    ventilate = True
```

Otherwise:

```python
ventilate = False
```

---

## Behavior

| Condition          | Output               |
| ------------------ | -------------------- |
| Poor air quality   | ventilate = True     |
| Rising pollution   | ventilate = True     |
| Stable & clean air | ventilate = False    |
| Insufficient data  | trend_rising = False |

---

## Pipeline

```text
Sensor Data → AQI Scoring → Trend Detection → Ventilation Decision
```

---

## Notes

- Designed for real-time processing on low-power devices
- Uses lightweight logic (no heavy models)
- Works well with noisy sensor input when combined with smoothing
- Can be extended to include CO₂ or humidity

---

## Integration

Used inside `EnvironmentController`:

```python
aq = air.update(data)

if aq["ventilate"]:
    exhaust.turn_on()
```

---

## Future Improvements

- Add CO₂-based scoring
- Apply exponential smoothing to AQI
- Adaptive thresholds based on occupancy
- Learning-based ventilation prediction
