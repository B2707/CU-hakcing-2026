# Rocko receiver (surface station)

Runs locally on the surface laptop, wired **MDT sensor → Pico → USB serial**.
It captures the coil signal, shows a live dashboard, and decodes the beacon
frame against the frozen contract in [`ALGORITHM.md`](ALGORITHM.md) and
`docs/equipment-codes.md`. Silence is the alarm.

## One command

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r receiver/requirements.txt

python3 receiver/rocko_receiver.py            # auto-detects the Pico serial port
```

- No port? It lists candidates; pass `-p /dev/cu.usbmodemXXXX`.
- No hardware? Replay a real recording: `python3 receiver/rocko_receiver.py --replay captures/trial.csv`
- One `Ctrl+C` (or closing the window) stops everything and flushes the capture.

The dashboard shows three panes — **both sensors raw**, **both sensors at the
8 Hz bandpass**, and **combined carrier amplitude + adaptive tone threshold** —
plus an expanded numbered event panel with receiver health, sample count,
threshold and signal state. The live decoder locks the tilde preamble, then
prints each flag decision with its Manchester-0 and Manchester-1 correlation
scores as soon as that bit arrives. The event log is scrollable with the mouse
wheel. Panes start empty; nothing is drawn until a real signal arrives. Each
decoded frame is marked with a large star at its start. Use the Matplotlib
toolbar to zoom/pan, or press `Q`/`Esc` to close cleanly.

## Data contract

The receiver appears as a USB serial device and emits one sample per line:

```text
t,x,y
0.000000,812,1571
```

- `t`: receiver time in seconds (evenly spaced at the sample rate)
- `x`: sensor 1 raw ADC (0–65535)
- `y`: sensor 2 raw ADC (0–65535)
- sample rate: 200 Hz, 115200 baud

Captured files use the same header + rows.

## Pico wiring (`pico_main.py`)

Copy [`pico_main.py`](pico_main.py) onto the Pico as `main.py`. It streams the
`t,x,y` format above from two ADC channels:

| Pico pin | ADC | Channel | Notes |
|---|---|---|---|
| GP26 | ADC0 | sensor 1 (`x`) | 0–3.3 V only |
| GP27 | ADC1 | sensor 2 (`y`) | tie to GND for a one-channel front-end |
| GND | — | sensor ground | shared |
| USB | — | — | to the laptop, 115200 baud |

## The frame it decodes

The current protocol is documented in [`docs/alphabet-protocol.md`](../docs/alphabet-protocol.md):
encoded tilde header plus one capital letter, four Hamming(7,4) groups, 28
regular-Manchester bits at 0.5 coded bit/s on an 8 Hz carrier, followed by a
15-second gap.
The analyzer runs naive-max and Gaussian-Bayes layers L1/L2/L3 plus hybrid L4,
and displays the header, letter, and successful selected layer.

## Individual tools

```bash
# capture only (no viz)
python3 receiver/capture.py -p /dev/cu.usbmodem1201 -o captures/trial.csv

# offline static review of a saved capture, with the decoded event
python3 receiver/plot_receiver.py captures/trial.csv --save review.png

# offline decode of a saved capture
python3 receiver/decode_tilde_message.py captures/trial.csv
```

## Layout

- `rocko_receiver.py` — the one-command launcher (port auto-detect, banner).
- `live_receiver.py` — live dashboard + causal tone detector + in-process decode.
- `decoder.py` — pure DSP + decode + synthetic waveform generator (no hardware).
- `protocol.py` — frozen frame constants and flag↔event mapping.
- `serial_source.py` — serial + CSV-replay sources (the only serial code).
- `eventlog.py` — numbered event log (file + on-screen).
- `capture.py` / `plot_receiver.py` / `decode_tilde_message.py` — offline tools.
- `pico_main.py` — MicroPython firmware for the Pico.
- `../tests/test_receiver.py` — decode synthetic waveforms, zero hardware.

## Tests

```bash
python3 -m pytest tests/            # or: python3 -m unittest discover tests
```
