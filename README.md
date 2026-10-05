# decimal-time

Convert between standard 24-hour time and French Republican decimal time. The day is divided into 10 decimal hours of 100 decimal minutes of 100 decimal seconds, so one decimal second equals 0.864 SI seconds.

```python
from decimal_time import to_decimal, from_decimal, DecimalTime

noon = to_decimal(12, 0, 0)        # DecimalTime(hour=5, minute=0, second=0)
back = from_decimal(5, 0, 0)       # (12, 0, 0)
print(str(noon))                   # "5:00:00"
```

## Why this exists

The French Republican calendar defined decimal time for a few years after 1792. It is a clean base-10 partition of the mean solar day and still turns up in horology demos, fiction, and the occasional scheduling experiment. This library is a single-purpose converter with no dependencies; it does not track the Republican calendar's months or leap-year rules, only the daily clock.

The one trade-off worth stating plainly: 100000 decimal seconds do not divide 86400 SI seconds evenly, so the conversion is lossy by design. We truncate toward zero on integer second counts. `to_decimal(23, 59, 59)` returns `DecimalTime(9, 99, 98)` — the last full decimal second of the day — and converting it back gives `(23, 59, 59)`, one SI second short of midnight in the worst case. If you need sub-second precision, keep SI seconds and convert only for display.

## Exported names

- `to_decimal(hour, minute, second=0) -> DecimalTime` — standard 24h to decimal. Accepts `int` or `float` seconds; floats are truncated toward zero. Carries are normalized, so `to_decimal(1, 60, 0)` equals `to_decimal(2, 0, 0)`.
- `from_decimal(hour, minute, second=0) -> tuple[int, int, int]` — decimal to standard. Returns `(std_hour, std_minute, std_second)`.
- `DecimalTime` — frozen dataclass with `hour` (0–9), `minute` (0–99), `second` (0–99). Constructor normalizes overflow and rejects negatives.
- `InvalidTimeError` — subclass of `ValueError`, raised on out-of-range or mistyped input (including `bool`, which is rejected even though it is technically an `int`).
- `seconds_in_day` — the integer `86400`.

## Tests

```
PYTHONPATH=src python -m unittest discover -s tests
```

## Edge you will hit

Boolean values are rejected as time components. `to_decimal(True, 0, 0)` raises `InvalidTimeError` rather than silently treating `True` as `1`. If you are passing values from a source that uses booleans, convert them explicitly.
