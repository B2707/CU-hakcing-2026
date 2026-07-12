# Raspberry Pi L298N Manchester transmitter

One-shot transmitter for the binary message `0111111010101011`. It uses regular
Manchester encoding (`0 -> OFF/ON`, `1 -> ON/OFF`) and an 8 Hz sine carrier.

## Wiring (BCM numbering)

| Raspberry Pi | L298N |
|---|---|
| GPIO22 | IN3 |
| GPIO17 | IN4 |
| GPIO27 | ENB |
| GND | GND |

Connect the transmit coil to `OUT3` and `OUT4`. Remove the ENB jumper because
GPIO27 controls ENB. The Pi and bridge must share ground. Do not power the coil
or L298N motor supply from the Pi.

## Install

```bash
sudo apt update
sudo apt install python3-pigpio pigpio
sudo systemctl enable --now pigpiod
```

`pigpio` is intended for Raspberry Pi models supported by the `pigpiod` daemon.
Verify daemon support for the specific Pi model and OS image before connecting
the powered bridge.

## Run

```bash
python3 transmitter/transmitter.py
```

Defaults:

- message: `0111111010101011`
- carrier: 8 Hz
- Manchester half-symbol rate: 0.5/s (two seconds per half)
- PWM carrier: 20 kHz
- maximum duty: 98%

The default 16-bit transmission takes 64 seconds. When complete—or if the
program is interrupted—the program sets ENB, IN3, and IN4 low.

Override settings if needed:

```bash
python3 transmitter/transmitter.py 0111111010101011 \
  --carrier 8 --half-rate 0.5 --power 98
```

## Safety

The L298N can dissipate substantial heat at high current. Use suitable cooling,
a current-limited supply, and a coil rated for the applied voltage and duty
cycle. Test with the motor supply disabled before energizing the bridge.
