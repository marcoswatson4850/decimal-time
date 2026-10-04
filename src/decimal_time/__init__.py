# SPDX-License-Identifier: MIT
"""Decimal Time: convert between standard 24-hour time and French decimal time.

French decimal time divides the day into 10 decimal hours, each into 100
decimal minutes, each into 100 decimal seconds. This package provides a
small, dependency-free converter. See :mod:`decimal_time.core` for the
contract.
"""

from decimal_time.core import (
    DecimalTime,
    InvalidTimeError,
    seconds_in_day,
    to_decimal,
    from_decimal,
)

__all__ = [
    "DecimalTime",
    "InvalidTimeError",
    "seconds_in_day",
    "to_decimal",
    "from_decimal",
]

__version__ = "1.0.0"
