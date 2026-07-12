# Cave Beacon coil transmitter (QNX 8 / Raspberry Pi 5)

Long-running beacon daemon that drives the L298N coil through the QNX
`rpi_gpio` resource manager (`/dev/gpio`). No pigpio, no Linux libraries.

- **Tone** = 8 Hz square wave made by flipping coil polarity on IN3/IN4
  (62.5 ms per half-cycle) with ENB high. **No tone** = ENB low.
- **Encoding**: regular Manchester per bit (`1 -> tone/no-tone`,
  `0 -> no-tone/tone`), bit time 1.0 s (0.5 s half-symbols = 4 carrier
  cycles per tone half).
- **Frame (12 bits, ~12 s)**: tilde preamble `01111110`, then 4 flag bits
  MSB-first — `bit3=fire  bit2=trapped  bit1=lost  bit0=injured`.
  `0000` = heartbeat, `1111` = SOS ("help" keyword override), combinations
  legal (`0101` = trapped+injured). Full table: `docs/equipment-codes.md`.
- **Behavior**: heartbeat frame every 120 s. Emergency triggers arrive via
  the spool file `/tmp/beacon_trigger` (class names or 4-bit flag strings,
  written by `TTS/live_listen_qnx.sh`). A frame mid-transmission is always
  finished first (~12 s worst wait), then the emergency frame goes out 3x
  with 3 s gaps, and the heartbeat schedule resumes. Multiple triggers
  while waiting OR-merge into one frame.

## Wiring (BCM numbering)

| Raspberry Pi | L298N |
|---|---|
| GPIO22 | IN3 |
| GPIO17 | IN4 |
| GPIO27 | ENB |
| GND | GND (shared with Pi) |

Coil on **OUT3/OUT4**. Remove the ENB jumper (GPIO27 controls ENB).
12 V pack only on the L298N motor supply — never on the Pi.

## Deploy (QNX Pi, `ssh qnxpi`)

```sh
scp transmitter/transmitter.py qnxpi:/data/home/qnxuser/transmitter/
ssh qnxpi 'python3 -m py_compile /data/home/qnxuser/transmitter/transmitter.py'
```

Python 3 comes from oss.qnx.com (`apk add python3`). The daemon needs the
`rpi_gpio` resource manager running (`pidin | grep -i gpio`).

**GPIO interface (verified on qnxpi 2026-07-12):** `rpi_gpio` mounts one text
node per pin under `/dev/gpio`; commands are written with no trailing newline
(`echo -n out|on|off > /dev/gpio/<pin>`). That is exactly what
`QnxGpioBackend` does. The nodes are `rw-rw---- uid gpio` — if writes are
denied, run as a user in the `gpio` group (or sudo).

## Run

```sh
# bench one-shot (single frame, then exit) - start here
python3 transmitter.py --send heartbeat
python3 transmitter.py --send injured
python3 transmitter.py --send trapped --send injured   # 0101 combo

# the real thing: daemon (heartbeat every 120 s + spool triggers)
python3 transmitter.py

# poke the running daemon
echo injured >> /tmp/beacon_trigger

# no-hardware dry run (works on the Mac too)
python3 transmitter.py --sim --send sos
```

Every frame is logged with timestamp+bits to `/tmp/beacon.log` (small,
rotating). A pidfile (`/tmp/beacon.pid`) guarantees a single instance —
two processes can never fight over the coil. On SIGINT/SIGTERM/crash the
coil is driven off and ENB pulled low, always.

All timing/pins/paths are constants in `Config` (no magic numbers);
`--heartbeat-interval`, `--bit-seconds`, `--carrier`, `--spool`,
`--pidfile`, `--log-file`, `--gpio-dev` override per run.

## Tests

```sh
python3 -m pytest tests/test_transmitter.py -q   # sim backend, no hardware
```

## Safety / first live test

1. Motor supply OFF, run `--send heartbeat`, scope the IN3/IN4/ENB pins.
2. Motor supply ON, `--send heartbeat` again, watch the surface scope
   (`bench/live_scope.py`) for the 12 s frame.
3. Only then start the daemon.

The L298N heats up at high current — cool it, current-limit the supply,
and use a coil rated for the voltage and duty cycle.
