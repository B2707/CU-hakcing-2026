# Hamming-coded alphabet link protocol

The QNX transmitter sends two MSB-first bytes: header `~` (`01111110`) and a
capital letter `A` through `Z`.

Each four data bits use standard even-parity Hamming(7,4):

```text
[p1, p2, d1, p4, d2, d3, d4]
p1 = d1 XOR d2 XOR d4
p2 = d1 XOR d3 XOR d4
p4 = d2 XOR d3 XOR d4
```

Thus 16 data bits become four Hamming codewords, or 28 coded bits. The code has
minimum Hamming distance 3 and corrects one hard-bit error per group under the
usual bounded-distance assumptions.

Every coded bit uses regular OOK Manchester at two seconds per bit:

```text
1 -> 8 Hz tone for 1 s, then no tone for 1 s
0 -> no tone for 1 s, then 8 Hz tone for 1 s
```

A complete transmission lasts 56 seconds. The coil is disabled for 15 seconds
between messages.

The receiver applies a fourth-order 7.25–8.75 Hz Butterworth bandpass and a
Hilbert transform, synchronizes against the Hamming-encoded tilde, and evaluates
naive-max and Gaussian-Bayes layers L1/L2/L3 plus hybrid L4. Experimental
coherent-GNB-SLNN decoding additionally phase-aligns both sensors, estimates
Manchester bit LLRs, and scores complete legal codewords.

A layer succeeds only when it recovers header `~`, an uppercase ASCII letter,
and a valid Hamming codeword. The analyzer displays every layer and identifies
the selected successful layer.
