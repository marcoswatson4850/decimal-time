# SPDX-License-Identifier: MIT
"""Core conversion logic for French decimal time.

Interpretation fixed by this module
-----------------------------------
French Republican decimal time divides one mean solar day into 10 decimal
hours (``h``), 100 decimal minutes (``m``), and 100 decimal seconds (``s``).
Thus ``1 h = 2.4 std hours``, ``1 m = 1.44 std minutes``, and
``1 s = 0.864 std seconds``. The day begins at midnight.

We deliberately work in integer *seconds since midnight* rather than in
floating point. Conversions between bases whose ratios are non-terminating
in binary (here 86400 / 100000 = 0.864) accumulate rounding error once you
represent results as ``float``. By staying on integers and only rounding at
the final presentation step, we avoid float ``==`` comparisons entirely and
remain deterministic across platforms.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Union

# One day in SI seconds. The French decimal clock partitions exactly this
# span into 100000 decimal seconds.
seconds_in_day: int = 86400

# The denominator of a decimal second expressed in SI seconds:
# 1 decimal second = 86400 / 100000 = 0.864 SI seconds. We keep the ratio
# as a pair of integers and reduce once, rather than as a float, so that
# rounding is exact integer arithmetic.
_DECIMAL_SECONDS_PER_DAY: int = 100_000


class InvalidTimeError(ValueError):
    """Raised when a time value is outside ``[0, 86400)`` or malformed."""


@dataclass(frozen=True)
class DecimalTime:
    """A point within a day expressed in French decimal time.

    Attributes
    ----------
    hour:
        Decimal hour, ``0`` through ``9``.
    minute:
        Decimal minute, ``0`` through ``99``.
    second:
        Decimal second, ``0`` through ``99``.

    The triple ``(hour, minute, second)`` always satisfies
    ``0 <= hour < 10``, ``0 <= minute < 100``, ``0 <= second < 100``;
    the constructor normalizes any overflow so that e.g. ``(0, 100, 0)``
    becomes ``(1, 0, 0)``. This lets callers add intervals without worrying
    about carry, and keeps the representation canonical for equality.
    """

    hour: int
    minute: int
    second: int

    def __post_init__(self) -> None:
        if not all(isinstance(v, int) for v in (self.hour, self.minute, self.second)):
            raise InvalidTimeError("DecimalTime fields must be integers")
        # Convert to a total count of decimal seconds, then split back. This
        # performs the carry in one pass and rejects negative input cleanly.
        total = (
            self.hour * 10_000 + self.minute * 100 + self.second
        )
        if total < 0 or total >= _DECIMAL_SECONDS_PER_DAY:
            raise InvalidTimeError(
                f"decimal time out of range: ({self.hour}, {self.minute}, {self.second})"
            )
        object.__setattr__(self, "hour", total // 10_000)
        object.__setattr__(self, "minute", (total % 10_000) // 100)
        object.__setattr__(self, "second", total % 100)

    @classmethod
    def from_decimal_seconds(cls, total: int) -> "DecimalTime":
        """Build from a count of decimal seconds since midnight.

        ``total`` must be an integer in ``[0, 100000)``.
        """
        if not isinstance(total, int) or isinstance(total, bool):
            raise InvalidTimeError("decimal seconds must be an int")
        if total < 0 or total >= _DECIMAL_SECONDS_PER_DAY:
            raise InvalidTimeError(f"decimal seconds out of range: {total}")
        return cls(total // 10_000, (total % 10_000) // 100, total % 100)

    def to_decimal_seconds(self) -> int:
        """Return the count of decimal seconds since midnight (0..99999)."""
        return self.hour * 10_000 + self.minute * 100 + self.second

    def __str__(self) -> str:
        return f"{self.hour:d}:{self.minute:02d}:{self.second:02d}"


def _to_int(value: Union[int, float]) -> int:
    """Coerce ``value`` to an integer second count, rejecting negatives.

    ``value`` may be an ``int`` or a ``float``; fractional seconds are
    truncated toward zero, matching the behavior of the rest of the library
    (which never rounds sub-second quantities). Booleans are rejected even
    though they are technically ``int`` subclasses, because accepting them
    is almost always a caller bug.
    """
    if isinstance(value, bool):
        raise InvalidTimeError("boolean is not a valid time component")
    if isinstance(value, int):
        if value < 0:
            raise InvalidTimeError(f"negative time component: {value}")
        return value
    if isinstance(value, float):
        if value != value:  # NaN
            raise InvalidTimeError("NaN is not a valid time component")
        if value < 0:
            raise InvalidTimeError(f"negative time component: {value}")
        # int() truncates toward zero for positive floats, which is what we
        # want: 86399.999 -> 86399, the last representable second of the day.
        return int(value)
    raise InvalidTimeError(f"unsupported type for time component: {type(value).__name__}")


def to_decimal(
    hour: int,
    minute: int,
    second: int = 0,
) -> DecimalTime:
    """Convert a standard 24-hour triple to French decimal time.

    Parameters
    ----------
    hour:
        Standard hour, ``0`` through ``23``.
    minute:
        Standard minute, ``0`` through ``59``. Carries are normalized, so
        ``hour=1, minute=60`` is accepted and equals ``hour=2, minute=0``.
    second:
        Standard second, ``0`` through ``59``. Fractional values are
        truncated toward zero, and carries are normalized.

    The conversion is exact: we compute the integer number of SI seconds
    since midnight and scale by the rational factor
    ``100000 / 86400``. Because both factors are integers, the intermediate
    product never leaves integer arithmetic, so the result is the same on
    every platform. The final truncation is toward zero, which means the
    last decimal second of the day (``9:99:99``) maps back from the range
    ``[86313.6, 86400)`` of SI seconds.
    """
    h = _to_int(hour)
    m = _to_int(minute)
    s = _to_int(second)

    total_std_seconds = h * 3600 + m * 60 + s
    if total_std_seconds >= seconds_in_day:
        raise InvalidTimeError(
            f"standard time out of range: {total_std_seconds} seconds"
        )

    # total_std_seconds * 100000 fits comfortably in a Python int (arbitrary
    # precision), so there is no overflow concern. Floor division gives the
    # truncated decimal-second count.
    dec_seconds = (total_std_seconds * _DECIMAL_SECONDS_PER_DAY) // seconds_in_day
    return DecimalTime.from_decimal_seconds(dec_seconds)


def from_decimal(
    hour: int,
    minute: int,
    second: int = 0,
) -> tuple:
    """Convert a French decimal triple to standard 24-hour time.

    Returns
    -------
    tuple of (int, int, int)
        ``(std_hour, std_minute, std_second)`` where each component is an
        integer, ``std_hour`` in ``0..23``, the others in ``0..59``.

    Notes
    -----
    The inverse of :func:`to_decimal` is not, in general, lossless: 100000
    decimal seconds map onto 86400 SI seconds, so each decimal second
    corresponds to a band of 0.864 SI seconds. We truncate toward zero, so
    ``to_decimal(23, 59, 59)`` and ``from_decimal`` of that result may
    differ by up to one SI second. This is the fundamental trade-off of
    decimal time and cannot be removed without switching to a fractional
    representation of seconds.
    """
    dec = DecimalTime(hour, minute, second)
    dec_seconds = dec.to_decimal_seconds()

    # 1 decimal second = 86400/100000 SI seconds. Multiply first, then floor.
    std_seconds = (dec_seconds * seconds_in_day) // _DECIMAL_SECONDS_PER_DAY
    if std_seconds >= seconds_in_day:
        # The largest dec_seconds is 99999, which gives 86399 SI seconds
        # after truncation, so this branch is unreachable. It is kept as a
        # guard against future changes to the constants.
        std_seconds = seconds_in_day - 1
    return (std_seconds // 3600, (std_seconds % 3600) // 60, std_seconds % 60)
