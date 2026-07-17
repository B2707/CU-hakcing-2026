# Temporal-Whitening Benchmark — 2026-07-17

## Question

Can a causal temporal noise predictor improve the coherent-LLR/group-codebook
receiver beyond no whitening or static ZCA?

## Data and split

Noise models used only:

```text
raw/static_noise_20260716_175304.csv
```

The ten-minute transmitter-off capture was split chronologically:

- first 70% (420 s, 84,000 samples): model fitting;
- next 15% (90 s): reserved validation segment;
- final 15% (90 s, 18,001 samples): H0/whiteness evaluation.

The physical signal test remained the 30-frame descending-duty capture. No
signal labels were used to train or select the temporal models. That capture
contains unlabelled human-motion interference.

## Common pipeline

```text
7.25-8.75 Hz bandpass
→ Hilbert analytic sensors
→ complex 8 Hz baseband
→ causal temporal predictor/innovation
→ remodulate analytic channels
→ tilde peak search
→ covariance-aware coherent LLR
→ four 16-word Hamming group decisions
→ header/payload validation
```

The models are blind prediction-error filters. They receive the observed
signal while a frame is active, so they can cancel predictable beacon energy.
That risk is part of this experiment.

## Models

- **VAR:** 20 lags (0.1 s), four inputs/outputs, ridge regression, residual
  covariance normalization.
- **Kalman:** learned four-dimensional AR(1) transition and process covariance;
  observation covariance fixed to 0.1 of training covariance.
- **GRU:** one causal layer with 16 hidden units and four-output prediction
  head; eight epochs, 256-sample sequences, MSE objective.
- **TCN:** four causal tanh convolution layers, 16 channels, kernel size three,
  dilations 1/2/4/8, 31-sample (0.155 s) receptive field; eight epochs.
- **ZCA:** static instantaneous covariance baseline.

## End-to-end results

`Sync correct` uses a local ±3-second tilde peak. `Legacy >=0.8` additionally
requires the preamble score to meet the old common threshold. Model-specific
H0 thresholds were the maximum scores across 12,402 windows in the untouched
90-second noise segment; those short estimates are exploratory, not final
false-alarm calibration.

| Front end | Known-start correct | Sync correct | Legacy >=0.8 | Model-H0 accepted |
|---|---:|---:|---:|---:|
| None | 18/30 | 18/30 | 12/30 | 18/30 |
| Static ZCA | 18/30 | 18/30 | 17/30 | 18/30 |
| VAR(20) | 11/30 | 13/30 | 9/30 | 13/30 |
| Kalman | 14/30 | 15/30 | 13/30 | 15/30 |
| GRU | 18/30 | 18/30 | 17/30 | 18/30 |
| TCN | 18/30 | 18/30 | 13/30 | 18/30 |

None recovered a 10% or 1% frame. GRU and TCN retained 6/6 at 100%, 50%, and
25%; VAR fell to 5/6, 5/6, and 3/6, while Kalman reached 6/6, 4/6, and 5/6.

## Held-out H0 noise behavior

| Front end | Mean absolute temporal correlation, lags 1-40 | Max spatial correlation | Covariance condition | H0 max preamble |
|---|---:|---:|---:|---:|
| None | 0.956 | 0.093 | 2.52 | 0.193 |
| Static ZCA | 0.961 | 0.817 | 30.37 | 0.347 |
| VAR(20) | **0.393** | 0.938 | 59.31 | **0.112** |
| Kalman | 0.943 | 0.704 | 7.23 | 0.357 |
| GRU | 0.962 | 0.910 | 32.13 | 0.238 |
| TCN | 0.961 | 0.856 | 687.28 | 0.545 |

The noise distribution changed strongly between the fitting and test portions
of the single recording. Consequently, training-set residual normalization
became mismatched and created large held-out spatial correlations for every
learned/static transform.

## Interpretation

- VAR performed the only substantial temporal decorrelation, but it also
  removed useful beacon structure and reduced decoding to 13/30.
- Kalman filtering similarly reduced decoding to 15/30.
- GRU matched the 18/30 decoder and the best legacy-threshold count, but it did
  not whiten temporal correlation on held-out noise. Its result is therefore
  equivalent to useful static weighting, not demonstrated temporal learning.
- TCN preserved decoding but produced an ill-conditioned held-out residual and
  did not improve temporal independence.
- Static ZCA remains simpler and matches the best observed end-to-end result.

No temporal model demonstrated an advantage over static ZCA. Strong temporal
prediction appears dangerous because the 8 Hz Manchester beacon is itself
predictable. Future work should model candidate-subtracted residual likelihoods
or transform the matched signal template consistently, and must use independent
noise sessions rather than adjacent splits of one recording.

## Artifacts

```text
derived/final_descending_dataset_20260716_144129.temporal-whitening.csv
derived/final_descending_dataset_20260716_144129.temporal-whitening-summary.json
models/temporal-whitening/temporal_var20.npz
models/temporal-whitening/temporal_kalman.npz
models/temporal-whitening/temporal_gru.pt
models/temporal-whitening/temporal_tcn.pt
```
