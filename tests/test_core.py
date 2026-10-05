# SPDX-License-Identifier: MIT
"""Tests for decimal_time.core.

These tests deliberately avoid floats and wall clocks. Every conversion is
checked against integer second counts so results are reproducible.
"""

import unittest

from decimal_time.core import (
    DecimalTime,
    InvalidTimeError,
    seconds_in_day,
    to_decimal,
    from_decimal,
)


class TestDecimalTimeDataclass(unittest.TestCase):
    def test_normalizes_overflow_in_minutes(self):
        # 100 decimal minutes should carry into the next decimal hour.
        dt = DecimalTime(0, 100, 0)
        self.assertEqual((dt.hour, dt.minute, dt.second), (1, 0, 0))

    def test_normalizes_overflow_in_seconds(self):
        dt = DecimalTime(0, 0, 100)
        self.assertEqual((dt.hour, dt.minute, dt.second), (0, 1, 0))

    def test_rejects_negative_hour(self):
        with self.assertRaises(InvalidTimeError):
            DecimalTime(-1, 0, 0)

    def test_rejects_non_integer_fields(self):
        with self.assertRaises(InvalidTimeError):
            DecimalTime(0, 0.5, 0)  # type: ignore[arg-type]

    def test_rejects_out_of_range_total(self):
        # 10 decimal hours would be the next day.
        with self.assertRaises(InvalidTimeError):
            DecimalTime(10, 0, 0)

    def test_from_decimal_seconds_rejects_bool(self):
        # bool is a subclass of int; accepting it is a common source of bugs.
        with self.assertRaises(InvalidTimeError):
            DecimalTime.from_decimal_seconds(True)  # type: ignore[arg-type]

    def test_str_format(self):
        self.assertEqual(str(DecimalTime(1, 2, 3)), "1:02:03")


class TestToDecimal(unittest.TestCase):
    def test_midnight(self):
        self.assertEqual(to_decimal(0, 0, 0), DecimalTime(0, 0, 0))

    def test_six_am_is_two_decimal_five(self):
        # 6 std hours = 0.25 of a day = 2.5 decimal hours = 2h 50m 0s.
        self.assertEqual(to_decimal(6, 0, 0), DecimalTime(2, 50, 0))

    def test_noon_is_five_decimal_hours(self):
        self.assertEqual(to_decimal(12, 0, 0), DecimalTime(5, 0, 0))

    def test_eighteen_h_is_seven_decimal_five(self):
        self.assertEqual(to_decimal(18, 0, 0), DecimalTime(7, 50, 0))

    def test_end_of_day_truncates_to_last_decimal_second(self):
        # 23:59:59 = 86399 SI seconds. 86399 * 100000 // 86400 = 99998.
        self.assertEqual(to_decimal(23, 59, 59), DecimalTime(9, 99, 98))

    def test_minute_carry_is_accepted(self):
        # 1h 60m 0s is the same as 2h 0m 0s, i.e. 7200 SI seconds.
        self.assertEqual(to_decimal(1, 60, 0), to_decimal(2, 0, 0))

    def test_rejects_24_hours(self):
        with self.assertRaises(InvalidTimeError):
            to_decimal(24, 0, 0)

    def test_rejects_negative_minute(self):
        with self.assertRaises(InvalidTimeError):
            to_decimal(0, -1, 0)

    def test_rejects_bool_hour(self):
        with self.assertRaises(InvalidTimeError):
            to_decimal(True, 0, 0)  # type: ignore[arg-type]

    def test_float_seconds_truncated_toward_zero(self):
        # 86399.9 SI seconds should truncate to 86399, the same as 23:59:59.
        self.assertEqual(to_decimal(23, 59, 59.9), to_decimal(23, 59, 59))


class TestFromDecimal(unittest.TestCase):
    def test_midnight(self):
        self.assertEqual(from_decimal(0, 0, 0), (0, 0, 0))

    def test_five_decimal_hours_is_noon(self):
        self.assertEqual(from_decimal(5, 0, 0), (12, 0, 0))

    def test_two_fifty_is_six_am(self):
        self.assertEqual(from_decimal(2, 50, 0), (6, 0, 0))

    def test_last_decimal_second_is_end_of_day_minus_one(self):
        # 99999 decimal seconds -> 86399 SI seconds (truncation loses <1s).
        self.assertEqual(from_decimal(9, 99, 99), (23, 59, 59))

    def test_rejects_negative_decimal_minute(self):
        with self.assertRaises(InvalidTimeError):
            from_decimal(0, -1, 0)

    def test_returns_tuple_of_ints(self):
        result = from_decimal(1, 0, 0)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3)
        for component in result:
            self.assertIsInstance(component, int)
            self.assertGreaterEqual(component, 0)


class TestRoundTrip(unittest.TestCase):
    """Verify the documented loss: round-trip may drop up to ~1 SI second."""

    def test_round_trip_noon_exact(self):
        dec = to_decimal(12, 0, 0)
        self.assertEqual(from_decimal(dec.hour, dec.minute, dec.second), (12, 0, 0))

    def test_round_trip_end_of_day_within_one_second(self):
        original = (23, 59, 59)
        dec = to_decimal(*original)
        back = from_decimal(dec.hour, dec.minute, dec.second)
        # The result is an integer-second triple; it should be within 1s.
        delta = abs(
            (back[0] * 3600 + back[1] * 60 + back[2])
            - (original[0] * 3600 + original[1] * 60 + original[2])
        )
        self.assertLessEqual(delta, 1)


class TestConstants(unittest.TestCase):
    def test_seconds_in_day_value(self):
        self.assertEqual(seconds_in_day, 86400)


if __name__ == "__main__":
    unittest.main()
