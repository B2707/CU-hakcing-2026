import importlib.util
from pathlib import Path
import sys
import unittest


MODULE_PATH = Path(__file__).parents[1] / "transmitter" / "transmitter.py"
SPEC = importlib.util.spec_from_file_location("transmitter", MODULE_PATH)
transmitter = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = transmitter
assert SPEC.loader is not None
SPEC.loader.exec_module(transmitter)


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def monotonic(self):
        return self.now

    def sleep(self, duration):
        self.now += max(0.0, duration)


class FakePigpio:
    def __init__(self):
        self.modes = []
        self.writes = []
        self.ranges = []
        self.frequencies = []
        self.duties = []

    def set_mode(self, pin, mode):
        self.modes.append((pin, mode))

    def write(self, pin, value):
        self.writes.append((pin, value))

    def set_PWM_range(self, pin, pwm_range):
        self.ranges.append((pin, pwm_range))

    def set_PWM_frequency(self, pin, frequency):
        self.frequencies.append((pin, frequency))
        return frequency

    def set_PWM_dutycycle(self, pin, duty):
        self.duties.append((pin, duty))


class ManchesterTests(unittest.TestCase):
    def test_regular_manchester_encoding(self):
        self.assertEqual(
            transmitter.regular_manchester("01111110"),
            [0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 1],
        )

    def test_rejects_non_binary_message(self):
        for value in ("", "012", "hello"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                transmitter.regular_manchester(value)


class TransmitterTests(unittest.TestCase):
    def test_uses_requested_l298n_gpio_mapping_and_stops(self):
        gpio = FakePigpio()
        clock = FakeClock()
        config = transmitter.Config(update_hz=32.0, half_symbol_rate=8.0)
        tx = transmitter.L298NManchesterTransmitter(
            gpio, config, monotonic=clock.monotonic, sleep=clock.sleep
        )

        tx.transmit("01")

        self.assertEqual({pin for pin, _ in gpio.modes}, {22, 17, 27})
        self.assertEqual(gpio.ranges, [(27, 10_000)])
        self.assertEqual(gpio.frequencies, [(27, 20_000)])
        self.assertTrue(any(pin == 22 and value == 1 for pin, value in gpio.writes))
        self.assertTrue(any(pin == 17 and value == 1 for pin, value in gpio.writes))
        self.assertTrue(any(duty > 0 for _, duty in gpio.duties))
        self.assertEqual(gpio.duties[-1], (27, 0))
        self.assertEqual(gpio.writes[-2:], [(22, 0), (17, 0)])

    def test_default_message_duration_is_64_seconds(self):
        symbols = transmitter.regular_manchester(transmitter.DEFAULT_MESSAGE)
        duration = len(symbols) / transmitter.Config().half_symbol_rate
        self.assertEqual(duration, 64.0)

    def test_invalid_duplicate_pins_are_rejected(self):
        with self.assertRaises(ValueError):
            transmitter.Config(in3_pin=17, in4_pin=17).validate()


if __name__ == "__main__":
    unittest.main()
