"""Beacon transmitter tests - sim backend only, no hardware or QNX deps."""

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

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


def make_rig(config=None):
    """Sim backend + fake clock + transmitter, wired together."""
    clock = FakeClock()
    config = config or transmitter.Config()
    backend = transmitter.SimBackend(monotonic=clock.monotonic)
    driver = transmitter.CoilDriver(backend, config)
    tx = transmitter.FrameTransmitter(
        driver, config, monotonic=clock.monotonic, sleep=clock.sleep
    )
    return clock, backend, tx


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


class FrameTests(unittest.TestCase):
    def test_frame_bits_per_class(self):
        cases = {
            "heartbeat": "01111110" + "0000",
            "fire": "01111110" + "1000",
            "trapped": "01111110" + "0100",
            "lost": "01111110" + "0010",
            "injured": "01111110" + "0001",
            "sos": "01111110" + "1111",
            "help": "01111110" + "1111",
        }
        for name, bits in cases.items():
            flags, unknown = transmitter.parse_trigger_text(name)
            with self.subTest(name=name):
                self.assertEqual(unknown, [])
                self.assertEqual(transmitter.build_frame(flags), bits)

    def test_flag_combinations_or_together(self):
        flags, _ = transmitter.parse_trigger_text("trapped\ninjured\n")
        self.assertEqual(transmitter.build_frame(flags), "01111110" + "0101")

    def test_raw_flag_bits_accepted(self):
        flags, unknown = transmitter.parse_trigger_text("0101")
        self.assertEqual(unknown, [])
        self.assertEqual(transmitter.build_frame(flags), "01111110" + "0101")

    def test_none_and_unknown_tokens_never_crash(self):
        flags, unknown = transmitter.parse_trigger_text("none")
        self.assertIsNone(flags)
        self.assertEqual(unknown, [])
        flags, unknown = transmitter.parse_trigger_text("trapped trapp banana")
        self.assertEqual(flags, transmitter.FLAG_TRAPPED)
        self.assertEqual(unknown, ["trapp", "banana"])
        flags, unknown = transmitter.parse_trigger_text("")
        self.assertIsNone(flags)

    def test_flags_out_of_range_rejected(self):
        with self.assertRaises(ValueError):
            transmitter.build_frame(16)


class TimingTests(unittest.TestCase):
    def test_manchester_half_symbol_timing(self):
        clock, backend, tx = make_rig()
        config = tx.config
        tx.transmit_frame("10")  # halves: tone, off, off, tone

        enb = [(t, v) for t, pin, v in backend.events if pin == config.enb_gpio]
        self.assertEqual(enb[0], (0.0, 1))  # tone half starts at t=0
        self.assertIn((0.5, 0), enb)  # off at first half-symbol boundary
        self.assertIn((1.0, 0), enb)
        self.assertIn((1.5, 1), enb)  # tone again for the final half
        self.assertEqual(enb[-1], (2.0, 0))  # all_off at frame end
        self.assertEqual(clock.now, 2.0)  # 2 bits x 1.0 s

    def test_tone_is_8hz_polarity_flips(self):
        clock, backend, tx = make_rig()
        config = tx.config
        tx.transmit_frame("1")  # tone occupies [0, 0.5)

        in3 = [
            (t, v)
            for t, pin, v in backend.events
            if pin == config.in3_gpio and t < 0.5
        ]
        self.assertEqual([v for _, v in in3], [1, 0, 1, 0, 1, 0, 1, 0])
        expected_times = [round(i * 0.0625, 4) for i in range(8)]
        self.assertEqual([round(t, 4) for t, _ in in3], expected_times)

    def test_full_frame_takes_twelve_seconds(self):
        clock, _, tx = make_rig()
        tx.transmit_frame(transmitter.build_frame(transmitter.HEARTBEAT_FLAGS))
        self.assertEqual(clock.now, 12.0)

    def test_coil_left_safe_after_frame(self):
        _, backend, tx = make_rig()
        config = tx.config
        tx.transmit_frame(transmitter.build_frame(transmitter.SOS_FLAGS))
        for pin in (config.in3_gpio, config.in4_gpio, config.enb_gpio):
            self.assertEqual(backend.last_value(pin), 0)


class BeaconLoopTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.spool = os.path.join(self.tmp.name, "beacon_trigger")

    def make_beacon(self, sleep_hook=None, heartbeat_interval=30.0):
        config = transmitter.Config(
            spool_path=self.spool, heartbeat_interval_s=heartbeat_interval
        )
        clock = FakeClock()

        def sleep(duration):
            clock.sleep(duration)
            if sleep_hook:
                sleep_hook(clock)

        backend = transmitter.SimBackend(monotonic=clock.monotonic)
        driver = transmitter.CoilDriver(backend, config)
        tx = transmitter.FrameTransmitter(
            driver, config, monotonic=clock.monotonic, sleep=sleep
        )
        beacon = transmitter.Beacon(tx, config, monotonic=clock.monotonic, sleep=sleep)
        return clock, backend, beacon

    def test_heartbeat_schedule(self):
        clock, _, beacon = self.make_beacon(heartbeat_interval=30.0)
        beacon.run(max_frames=3)
        starts = [t for t, _, kind in beacon.frame_history]
        kinds = {kind for _, _, kind in beacon.frame_history}
        self.assertEqual(kinds, {"heartbeat"})
        self.assertEqual(starts, [0.0, 30.0, 60.0])

    def test_emergency_mid_frame_waits_then_repeats_three_times(self):
        state = {"written": False}

        def hook(clock):
            # trigger lands ~3 s into the first heartbeat frame
            if not state["written"] and clock.now >= 3.0:
                with open(self.spool, "a", encoding="ascii") as spool:
                    spool.write("trapped\n")
                    spool.write("injured\n")  # second trigger while waiting
                state["written"] = True

        clock, _, beacon = self.make_beacon(sleep_hook=hook)
        beacon.run(max_frames=4)

        kinds = [kind for _, _, kind in beacon.frame_history]
        self.assertEqual(kinds, ["heartbeat", "emergency", "emergency", "emergency"])

        starts = [t for t, _, _ in beacon.frame_history]
        self.assertEqual(starts[0], 0.0)
        self.assertGreaterEqual(starts[1], 12.0)  # heartbeat frame finished first
        # 12 s frame + 3 s gap between the emergency repeats
        self.assertEqual(starts[2] - starts[1], 15.0)
        self.assertEqual(starts[3] - starts[2], 15.0)

        emergency_bits = {bits for _, bits, kind in beacon.frame_history if kind == "emergency"}
        self.assertEqual(emergency_bits, {"01111110" + "0101"})  # flags OR-merged
        self.assertFalse(os.path.exists(self.spool))  # spool consumed+deleted

    def test_heartbeat_resumes_after_emergency(self):
        with open(self.spool, "w", encoding="ascii") as spool:
            spool.write("fire\n")
        clock, _, beacon = self.make_beacon(heartbeat_interval=30.0)
        beacon.run(max_frames=4)
        kinds = [kind for _, _, kind in beacon.frame_history]
        self.assertEqual(kinds, ["emergency", "emergency", "emergency", "heartbeat"])
        burst_end = beacon.frame_history[2][0] + 12.0  # last emergency frame end
        self.assertEqual(beacon.frame_history[3][0], burst_end + 30.0)

    def test_cleanup_on_interrupt_mid_frame(self):
        def hook(clock):
            if clock.now >= 5.0:
                raise KeyboardInterrupt

        clock, backend, beacon = self.make_beacon(sleep_hook=hook)
        with self.assertRaises(KeyboardInterrupt):
            beacon.run(max_frames=2)
        config = beacon.config
        for pin in (config.in3_gpio, config.in4_gpio, config.enb_gpio):
            self.assertEqual(backend.last_value(pin), 0)

    def test_signal_handler_raises_system_exit(self):
        import signal as signal_module

        with self.assertRaises(SystemExit) as ctx:
            transmitter._raise_exit(signal_module.SIGTERM, None)
        self.assertEqual(ctx.exception.code, 128 + signal_module.SIGTERM)


class LockAndConfigTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.pidfile = os.path.join(self.tmp.name, "beacon.pid")

    def test_second_instance_is_rejected(self):
        first = transmitter.SingleInstanceLock(self.pidfile)
        first.acquire()
        self.addCleanup(first.release)
        second = transmitter.SingleInstanceLock(self.pidfile)
        with self.assertRaises(transmitter.BeaconError):
            second.acquire()

    def test_stale_pidfile_is_reclaimed(self):
        # a finished subprocess pid is (almost certainly) not alive any more
        proc = subprocess.Popen([sys.executable, "-c", "pass"])
        proc.wait()
        with open(self.pidfile, "w", encoding="ascii") as pidfile:
            pidfile.write(str(proc.pid))
        lock = transmitter.SingleInstanceLock(self.pidfile)
        lock.acquire()
        self.addCleanup(lock.release)
        with open(self.pidfile, encoding="ascii") as pidfile:
            self.assertEqual(pidfile.read(), str(os.getpid()))

    def test_invalid_configs_rejected(self):
        with self.assertRaises(ValueError):
            transmitter.Config(in3_gpio=17, in4_gpio=17).validate()
        with self.assertRaises(ValueError):
            transmitter.Config(carrier_hz=3.0).validate()  # 1.5 cycles/half
        with self.assertRaises(ValueError):
            transmitter.Config(bit_seconds=0).validate()

    def test_cli_rejects_unknown_class(self):
        rc = transmitter.main(["--send", "banana", "--sim"])
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
