#!/usr/bin/env python3
"""Transmit a regular-Manchester message through an L298N on a Raspberry Pi.

BCM wiring:
    GPIO22 -> IN3
    GPIO17 -> IN4
    GPIO27 -> ENB

ENB receives high-frequency PWM for amplitude control. IN3/IN4 select the
polarity of an 8 Hz sine carrier. Manchester OFF half-symbols disable ENB.
"""

from __future__ import annotations

import argparse
import math
import time
from dataclasses import dataclass
from typing import Callable, Sequence

try:
    import pigpio
except ImportError:  # Allow encoding/unit tests on non-Pi hosts.
    pigpio = None


DEFAULT_MESSAGE = "0111111010101011"


def regular_manchester(bits: str) -> list[int]:
    """Encode bits using 0 -> OFF/ON and 1 -> ON/OFF."""
    if not bits or any(bit not in "01" for bit in bits):
        raise ValueError("message must be a non-empty binary string")
    symbols: list[int] = []
    for bit in bits:
        symbols.extend((0, 1) if bit == "0" else (1, 0))
    return symbols


@dataclass(frozen=True)
class Config:
    in3_pin: int = 22
    in4_pin: int = 17
    enb_pin: int = 27
    carrier_hz: float = 8.0
    half_symbol_rate: float = 0.5
    pwm_hz: int = 20_000
    update_hz: float = 500.0
    power_percent: float = 98.0

    def validate(self) -> None:
        if len({self.in3_pin, self.in4_pin, self.enb_pin}) != 3:
            raise ValueError("IN3, IN4, and ENB must use different GPIO pins")
        if self.carrier_hz <= 0 or self.half_symbol_rate <= 0:
            raise ValueError("carrier and half-symbol rates must be positive")
        if self.pwm_hz <= 0 or self.update_hz <= 0:
            raise ValueError("PWM and update rates must be positive")
        if not 0 < self.power_percent <= 100:
            raise ValueError("power must be in the range (0, 100]")


class L298NManchesterTransmitter:
    """One-shot L298N transmitter using a pigpio-compatible connection."""

    def __init__(
        self,
        connection,
        config: Config = Config(),
        monotonic: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        config.validate()
        self.pi = connection
        self.config = config
        self.monotonic = monotonic
        self.sleep = sleep
        self._output = getattr(pigpio, "OUTPUT", 1) if pigpio else 1

    def setup(self) -> None:
        for pin in (self.config.in3_pin, self.config.in4_pin, self.config.enb_pin):
            self.pi.set_mode(pin, self._output)
            self.pi.write(pin, 0)
        self.pi.set_PWM_range(self.config.enb_pin, 10_000)
        self.pi.set_PWM_frequency(self.config.enb_pin, self.config.pwm_hz)
        self.pi.set_PWM_dutycycle(self.config.enb_pin, 0)

    def stop(self) -> None:
        self.pi.set_PWM_dutycycle(self.config.enb_pin, 0)
        self.pi.write(self.config.in3_pin, 0)
        self.pi.write(self.config.in4_pin, 0)

    def _drive(self, value: float) -> None:
        """Apply signed normalized bridge voltage in the range [-1, 1]."""
        if value > 0:
            self.pi.write(self.config.in3_pin, 1)
            self.pi.write(self.config.in4_pin, 0)
        elif value < 0:
            self.pi.write(self.config.in3_pin, 0)
            self.pi.write(self.config.in4_pin, 1)
        else:
            self.pi.write(self.config.in3_pin, 0)
            self.pi.write(self.config.in4_pin, 0)

        duty = round(abs(value) * self.config.power_percent * 100)
        self.pi.set_PWM_dutycycle(self.config.enb_pin, duty)

    def _active_symbol(self, start: float, deadline: float) -> None:
        update_period = 1.0 / self.config.update_hz
        next_update = self.monotonic()
        while next_update < deadline:
            phase = 2.0 * math.pi * self.config.carrier_hz * (next_update - start)
            self._drive(math.sin(phase))
            next_update += update_period
            self.sleep(max(0.0, next_update - self.monotonic()))

    def transmit(self, bits: str) -> None:
        symbols: Sequence[int] = regular_manchester(bits)
        half_period = 1.0 / self.config.half_symbol_rate
        transmission_start = self.monotonic()

        self.setup()
        try:
            for index, active in enumerate(symbols):
                deadline = transmission_start + (index + 1) * half_period
                if active:
                    self._active_symbol(transmission_start, deadline)
                else:
                    self.stop()
                    self.sleep(max(0.0, deadline - self.monotonic()))
        finally:
            self.stop()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("message", nargs="?", default=DEFAULT_MESSAGE)
    parser.add_argument("--carrier", type=float, default=8.0)
    parser.add_argument("--half-rate", type=float, default=0.5)
    parser.add_argument("--power", type=float, default=98.0)
    parser.add_argument("--pwm-frequency", type=int, default=20_000)
    parser.add_argument("--update-rate", type=float, default=500.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if pigpio is None:
        raise SystemExit("pigpio is not installed; see transmitter/README.md")

    config = Config(
        carrier_hz=args.carrier,
        half_symbol_rate=args.half_rate,
        power_percent=args.power,
        pwm_hz=args.pwm_frequency,
        update_hz=args.update_rate,
    )
    connection = pigpio.pi()
    if not connection.connected:
        raise SystemExit("cannot connect to pigpiod; start it with: sudo systemctl start pigpiod")

    try:
        print(
            f"Transmitting {args.message}: regular Manchester, "
            f"{config.carrier_hz:g} Hz carrier"
        )
        L298NManchesterTransmitter(connection, config).transmit(args.message)
        print("Transmission complete; L298N disabled")
    finally:
        connection.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
