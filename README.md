# VAP: Voice Activity Projection


Voice Activity Projection module


## VAP


The Voice Acticity Projection module extract model ('discrete', 'independent',
'comparative') VA-labels and given voice activity and model logits-outputs,
extracts turn-taking ("zero-shot") probabilities.

```python
from vap_turn_taking.config.example_data import example
from vap_turn_taking import VAP


vapper = VAP(type="discrete")

# example of voice activity for 2 speakers
va = example['va']  # Voice Activity (Batch, N_Frames, 2)


# Extract labels: Voice Acticity Projection windows
#   Discrete:       (B, N_frames), class indices
#   Independent:    (B, N_frames, 2, N_bins), binary vap_bins
#   Comaparative:   (B, N_frames), float scalar
y = vapper.extract_label(va)

# Associated logits (discrete/independent/comparative)
logits = model(INPUTS)  # same shape as the labels


# Get "zero-shot" probabilites
turn_taking_probs = vapper(logits, va)  # keys: "p", "p_bc"
# turn_taking_probs['p'], (B, N_frames, 2) -> probability of next speaker
# turn_taking_probs['p_bc'], (B, N_frames, 2) -> probability of backchannel prediction
```


## Events

The module which extract events from a Voice Activity representation used to
calculate scores over particular frames of interest.

```python
from vap_turn_taking.config.example_data import example, event_conf
from vap_turn_taking import TurnTakingEvents


# example of voice activity for 2 speakers
va = example['va']  # Voice Activity (Batch, N_Frames, 2)


# Class to extract turn-taking events
eventer = TurnTakingEvents(
    hs_kwargs=event_conf["hs"],
    bc_kwargs=event_conf["bc"],
    metric_kwargs=event_conf["metric"],
    frame_hz=100,
)


# extract events from binary voice activity features
events = eventer(va, max_frame=None)

# all events are binary representations of size (B, N_frames, 2)
# where 1 indicates an event relevant frame.
# events.keys(): [
#   'shift', 
#   'hold', 
#   'short', 
#   'long', 
#   'predict_shift_pos', 
#   'predict_shift_neg', 
#   'predict_bc_pos', 
#   'predict_bc_neg'
# ]
```


## Metrics

Calculates metrics during training/evaluation given the `turn_taking_probs`
from the `VAP`+model-output and the events from `TurnTakingEvents`.

```python
from vap_turn_taking import TurnTakingMetrics
from vap_turn_taking.config.example_data import example, event_conf


va = example['va']  # Voice Activity (Batch, N_Frames, 2)


metric = TurnTakingMetrics(
    hs_kwargs=event_conf["hs"],
    bc_kwargs=event_conf["bc"],
    metric_kwargs=event_conf["metric"],
    bc_pred_pr_curve=True,
    shift_pred_pr_curve=True,
    long_short_pr_curve=True,
    frame_hz=100,
)

events = eventer(va, max_frame=None)
turn_taking_probs = vapper(logits, va)  # keys: "p", "p_bc"

# Update
metric.update(
    p=turn_taking_probs["p"],
    bc_pred_probs=turn_taking_probs.get("bc_prediction", None),
    events=events,
)

# Compute
result = metric.compute()
```
