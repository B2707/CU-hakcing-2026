"""Tests for the Hamming hardware-PWM data-collection transmitter."""

from pathlib import Path
import itertools
import sys
import unittest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "transmitter"))

import hamming_sweep as sweep  # noqa: E402


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


class HammingTests(unittest.TestCase):
    def test_standard_layout_and_known_group(self):
        # d=1011: p1=0, p2=1, p4=0 -> [p1,p2,d1,p4,d2,d3,d4]
        self.assertEqual(sweep.hamming_group("1011"), "0110011")

    def test_code_has_minimum_distance_three(self):
        words = [sweep.hamming_group(f"{value:04b}") for value in range(16)]
        distance = min(
            sum(a != b for a, b in zip(left, right))
            for left, right in itertools.combinations(words, 2)
        )
        self.assertEqual(distance, 3)

    def test_message_remains_28_bits(self):
        self.assertEqual(len(sweep.build_message("A")), 28)
        with self.assertRaises(ValueError):
            sweep.build_message("a1")


class ScheduleTests(unittest.TestCase):
    def test_training_has_every_letter_at_every_level(self):
        schedule = sweep.training_schedule()
        self.assertEqual(len(schedule), 30)
        self.assertEqual(
            {(trial.letter, trial.requested_duty) for trial in schedule},
            {(letter, duty) for letter in "ABCDE" for duty in sweep.DUTY_LEVELS},
        )
        self.assertEqual(schedule, sweep.training_schedule())

    def test_test_letters_are_held_out(self):
        self.assertEqual([trial.letter for trial in sweep.test_schedule()], list("FGHIJ"))
        self.assertTrue(all(trial.requested_duty == .1 for trial in sweep.test_schedule()))

    def test_duration_estimates(self):
        self.assertEqual(sweep.estimated_seconds(sweep.training_schedule()), 2115)
        self.assertEqual(sweep.estimated_seconds(sweep.test_schedule()), 340)
        self.assertEqual(
            sweep.estimated_seconds(sweep.requested_schedule("all")), 2470
        )

    def test_hardware_pwm_quantization_is_reported(self):
        expected = {
            100: 100.0,
            18: 17.96875,
            5: 4.98046875,
            1.3: 1.26953125,
            .36: .390625,
            .1: .09765625,
        }
        for requested, actual in expected.items():
            with self.subTest(requested=requested):
                self.assertAlmostEqual(sweep.actual_duty(requested), actual)


class FrameTests(unittest.TestCase):
    def test_half_baud_frame_timing_and_safe_off(self):
        clock = FakeClock()
        coil = sweep.SimCoil()
        transmitter = sweep.FrameTransmitter(
            coil, monotonic=clock.monotonic, sleep=clock.sleep
        )
        transmitter.transmit("1", 5)
        self.assertAlmostEqual(clock.now, 2.0)
        # One second of tone has 16 polarity half-cycles at 8 Hz.
        self.assertEqual(len(coil.polarities), 16)
        self.assertEqual(coil.polarities[:4], [True, False, True, False])
        self.assertEqual(coil.duties[-1], 0.0)


if __name__ == "__main__":
    unittest.main()
