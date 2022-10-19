import pytest

import torch
import vap_turn_taking.functional as VF
from vap_turn_taking.utils import vad_list_to_onehot

# @ 50hz
FRAME_HZ: int = 50
PRE_COND_FRAMES: int = 50
POST_COND_FRAMES: int = 50
PREDICTION_REGION_FRAMES: int = 25  # 0.5s
PREDICTION_REGION_ON_ACTIVE: bool = True
MIN_CONTEXT_FRAMES: int = 150
MIN_SILENCE_FRAMES: int = 10  # 0.2s
MAX_BC_FRAMES: int = 50
MAX_FRAME: int = 500


@pytest.fixture
def data():
    data = torch.load("example/vap_data.pt")
    return data


@pytest.mark.functional
def test_dialog_state(data):
    vad = data["shift"]["vad"]  # (1, 600, 2)
    B, N_FRAMES, _ = vad.shape
    ds = VF.get_dialog_states(vad)
    assert ds.shape == (
        B,
        N_FRAMES,
    ), f"get_dialog_states expected shape {(B, N_FRAMES)} got {(tuple(ds.shape))}."


@pytest.mark.functional
def test_find_island_idx_len(data):
    vad = data["shift"]["vad"]  # (1, 600, 2)
    B, N_FRAMES, _ = vad.shape

    # get dialog states
    ds = VF.get_dialog_states(vad)
    assert ds.shape == (
        B,
        N_FRAMES,
    ), f"get_dialog_states expected shape {(B, N_FRAMES)} got {(tuple(ds.shape))}."

    idx, dur, values = VF.find_island_idx_len(ds[0])
    assert (
        len(idx) == len(dur) == len(values)
    ), f"lengths does not match: idx != dur != values"
    assert len(idx) == 14, f"IDX length does not match, {len(idx)} != 14"


@pytest.mark.functional
def test_fill_pauses(data):
    vad = data["shift"]["vad"]  # (1, 600, 2)
    vad = vad[0]  # (600, 2)

    ds = VF.get_dialog_states(vad)
    filled_vad = VF.fill_pauses(vad, ds)
    # import matplotlib.pyplot as plt
    # from vap_turn_taking.plot_utils import plot_vad_oh
    # fig, ax = plt.subplots(2, 1, figsize=(9,6))
    # _ = plot_vad_oh(vad, ax=ax[0])
    # _ = plot_vad_oh(filled_vad, ax=ax[1])
    # plt.show()
    assert (
        vad.shape == filled_vad.shape
    ), f"shaps don't match. vad: {vad.shape} != filled_vad: {filled_vad.shape}"


@pytest.mark.functional
def test_shift_hold_simple(data):
    vad = data["shift"]["vad"]  # (1, 600, 2)
    vad = vad[0]  # (600, 2)
    ds = VF.get_dialog_states(vad)

    shifts, shift_overlap, holds = VF.hold_shift_regions_simple(ds)
    assert len(shifts) == 2, f"Number of shifts are not correct {len(shifts)} != 2"
    assert len(holds) == 4, f"Number of holds are not correct {len(holds)} != 4"
    assert len(shift_overlap) == 0, f"Number of holds are not correct {len(holds)} != 0"

    vad = data["bc"]["vad"]  # (1, 600, 2)
    vad = vad[0]  # (600, 2)
    ds = VF.get_dialog_states(vad)

    shifts, shift_overlap, holds = VF.hold_shift_regions_simple(ds)
    # import matplotlib.pyplot as plt
    # from vap_turn_taking.plot_utils import plot_vad_oh
    # fig, ax = plt.subplots(1, 1, figsize=(9, 6))
    # _ = plot_vad_oh(vad, ax=ax)
    # for start, end in shifts:
    #     ax.axvline(start, linewidth=2, color="g")
    #     ax.axvline(end, linewidth=2, color="r")
    # for start, end in holds:
    #     ax.axvline(start, linewidth=2, linestyle="dashed", color="g")
    #     ax.axvline(end, linewidth=2, linestyle="dashed", color="r")
    # plt.pause(0.1)
    assert len(shifts) == 1, f"Number of shifts are not correct {len(shifts)} != 1"
    assert len(holds) == 5, f"Number of holds are not correct {len(holds)} != 4"
    assert len(shift_overlap) == 0, f"Number of holds are not correct {len(holds)} != 0"


@pytest.mark.functional
def test_shift_hold(data):
    """
    Test shift/hold extraction on a single sample
    """
    # Input
    vad = data["shift"]["vad"][0]  # (600,2)
    ds = VF.get_dialog_states(vad)
    sh = VF.hold_shift_regions(
        vad=vad,
        ds=ds,
        pre_cond_frames=PRE_COND_FRAMES,
        post_cond_frames=POST_COND_FRAMES,
        prediction_region_frames=PREDICTION_REGION_FRAMES,
        prediction_region_on_active=PREDICTION_REGION_ON_ACTIVE,
        min_silence_frames=MIN_SILENCE_FRAMES,
        min_context_frames=MIN_CONTEXT_FRAMES,
        max_frame=MAX_FRAME,
    )
    assert (
        len(sh["shift"]) == 1
    ), f"Number of shifts are incorrect {len(sh['shift'])} != 1"
    assert len(sh["hold"]) == 1, f"Number of holds are incorrect {len(sh['hold'])} != 1"

    # Input
    vad = data["only_hold"]["vad"][0]  # (600,2)
    ds = VF.get_dialog_states(vad)
    sh = VF.hold_shift_regions(
        vad=vad,
        ds=ds,
        pre_cond_frames=PRE_COND_FRAMES,
        post_cond_frames=POST_COND_FRAMES,
        prediction_region_frames=PREDICTION_REGION_FRAMES,
        prediction_region_on_active=PREDICTION_REGION_ON_ACTIVE,
        min_silence_frames=MIN_SILENCE_FRAMES,
        min_context_frames=MIN_CONTEXT_FRAMES,
        max_frame=MAX_FRAME,
    )
    assert (
        len(sh["shift"]) == 0
    ), f"Number of shifts are incorrect {len(sh['shift'])} != 0"
    assert len(sh["hold"]) == 2, f"Number of holds are incorrect {len(sh['hold'])} != 2"

    # Input
    vad = data["bc"]["vad"][0]  # (600,2)
    ds = VF.get_dialog_states(vad)
    sh = VF.hold_shift_regions(
        vad=vad,
        ds=ds,
        pre_cond_frames=PRE_COND_FRAMES,
        post_cond_frames=POST_COND_FRAMES,
        prediction_region_frames=PREDICTION_REGION_FRAMES,
        prediction_region_on_active=PREDICTION_REGION_ON_ACTIVE,
        min_silence_frames=MIN_SILENCE_FRAMES,
        min_context_frames=MIN_CONTEXT_FRAMES,
        max_frame=MAX_FRAME,
    )
    # import matplotlib.pyplot as plt
    # from vap_turn_taking.plot_utils import plot_vad_oh
    # fig, ax = plt.subplots(1, 1, figsize=(9, 6))
    # _ = plot_vad_oh(vad, ax=ax)
    # ax.axvline(min_context_frames, linewidth=4, color="k")
    # ax.axvline(max_frame, linewidth=4, color="k")
    # for start, end in shifts:
    #     ax.axvline(start, linewidth=2, color="g")
    #     ax.axvline(end, linewidth=2, color="r")
    # for start, end in holds:
    #     ax.axvline(start, linewidth=2, linestyle="dashed", color="g")
    #     ax.axvline(end, linewidth=2, linestyle="dashed", color="r")
    # plt.pause(0.1)
    assert (
        len(sh["shift"]) == 1
    ), f"Number of shifts are incorrect {len(sh['shift'])} != 1"
    assert len(sh["hold"]) == 1, f"Number of holds are incorrect {len(sh['hold'])} != 1"


@pytest.mark.functional
def test_shift_hold_batch(data):
    """
    Test shift/hold extraction on batched sample
    """
    vad = torch.cat(
        (
            data["shift"]["vad"],
            data["only_hold"]["vad"],
            data["bc"]["vad"],
        )
    )
    batch_size = vad.shape[0]

    shifts, holds = [], []
    for b in range(batch_size):
        ds = VF.get_dialog_states(vad[b])
        tmp_sh = VF.hold_shift_regions(
            vad=vad[b],
            ds=ds,
            pre_cond_frames=PRE_COND_FRAMES,
            post_cond_frames=POST_COND_FRAMES,
            prediction_region_frames=PREDICTION_REGION_FRAMES,
            prediction_region_on_active=PREDICTION_REGION_ON_ACTIVE,
            min_silence_frames=MIN_SILENCE_FRAMES,
            min_context_frames=MIN_CONTEXT_FRAMES,
            max_frame=MAX_FRAME,
        )
        shifts.append(tmp_sh["shift"])
        holds.append(tmp_sh["shift"])
    assert (
        len(shifts) == batch_size
    ), f"not all SHIFT samples are included batch_size is off"
    assert (
        len(holds) == batch_size
    ), f"not all HOLD samples are included batch_size is off"


@pytest.mark.functional
def test_backchannel():
    # vad = data["bc"]["vad"][0]  # (n_frames, 2)

    # import matplotlib.pyplot as plt
    # from vap_turn_taking.plot_utils import plot_vad_oh

    vad_lists = [
        [[[2, 4], [7, 9]], [[4.6, 5.5]]],
        [[[2, 4]], [[4.6, 5.5], [7, 9]]],  # not bc with filleed vad
        [[[2, 4]], [[4.6, 5.5]]],  # no activity after (can still be bc)
        [[[2, 4], [6.8, 7.1]], [[4.6, 5.5], [7, 9]]],  # not bc with filleed vad
    ]
    n_bc = [1, 0, 1, 2]

    for vad_list, N in zip(vad_lists, n_bc):
        vad = vad_list_to_onehot(
            vad_list, hop_time=0.02, duration=11.99, channel_last=True
        )
        bc = VF.backchannel_regions(
            vad,
            pre_cond_frames=PRE_COND_FRAMES,
            post_cond_frames=POST_COND_FRAMES,
            prediction_region_frames=PREDICTION_REGION_FRAMES,
            min_context_frames=MIN_CONTEXT_FRAMES,
            max_bc_frames=MAX_BC_FRAMES,
            max_frame=MAX_FRAME,
        )
        # ds = VF.get_dialog_states(vad)
        # filled_vad = VF.fill_pauses(vad, ds)
        # fig, [ax, ax1] = plt.subplots(2, 1, figsize=(9, 6))
        # _ = plot_vad_oh(vad, ax=ax)
        # _ = plot_vad_oh(filled_vad, ax=ax1)
        # ax.axvline(MIN_CONTEXT_FRAMES, linewidth=4, color="k")
        # ax.axvline(MAX_FRAME, linewidth=4, color="k")
        # # for bc_start, bc_end, speaker in backchannels['backchannel']:
        # for bc_start, bc_end, speaker in bc["pred_backchannel"]:
        #     ymin = 0
        #     ymax = 1
        #     if speaker == 1:
        #         ymin = -1
        #         ymax = 0
        #     ax.vlines(bc_start, ymin=ymin, ymax=ymax, linewidth=4, color="g")
        #     ax.vlines(bc_end, ymin=ymin, ymax=ymax, linewidth=4, color="r")
        # plt.show()
        assert len(bc["backchannel"]) == N, "Wrong number of backchannels found"
        assert len(bc["pred_backchannel"]) == N, "Wrong number of backchannels found"

    vad_list = vad_lists[0]
    vad = vad_list_to_onehot(vad_list, hop_time=0.02, duration=11.99, channel_last=True)
    bc = VF.backchannel_regions(
        vad,
        pre_cond_frames=PRE_COND_FRAMES,
        post_cond_frames=POST_COND_FRAMES,
        prediction_region_frames=100,
        min_context_frames=MIN_CONTEXT_FRAMES,
        max_bc_frames=MAX_BC_FRAMES,
        max_frame=MAX_FRAME,
    )
    assert len(bc["backchannel"]) == 1, "Wrong number of backchannels found"
    assert len(bc["pred_backchannel"]) == 0, "Wrong number of backchannels found"

    vad_list = vad_lists[-1]
    vad = vad_list_to_onehot(vad_list, hop_time=0.02, duration=11.99, channel_last=True)
    bc = VF.backchannel_regions(
        vad,
        pre_cond_frames=PRE_COND_FRAMES,
        post_cond_frames=POST_COND_FRAMES,
        prediction_region_frames=100,
        min_context_frames=MIN_CONTEXT_FRAMES,
        max_bc_frames=MAX_BC_FRAMES,
        max_frame=MAX_FRAME,
    )
    # fig, [ax, ax1] = plt.subplots(2, 1, figsize=(9, 6))
    # _ = plot_vad_oh(vad, ax=ax)
    # ax.axvline(MIN_CONTEXT_FRAMES, linewidth=4, color="k")
    # ax.axvline(MAX_FRAME, linewidth=4, color="k")
    # # for bc_start, bc_end, speaker in backchannels['backchannel']:
    # for bc_start, bc_end, speaker in bc['backchannel']:
    #     ymin = 0
    #     ymax = 1
    #     if speaker == 1:
    #         ymin = -1
    #         ymax = 0
    #     ax.vlines(bc_start, ymin=ymin, ymax=ymax, linewidth=2, color="g")
    #     ax.vlines(bc_end, ymin=ymin, ymax=ymax, linewidth=2, color="r")
    # for bc_start, bc_end, speaker in bc['pred_backchannel']:
    #     ymin = 0
    #     ymax = 1
    #     if speaker == 1:
    #         ymin = -1
    #         ymax = 0
    #     ax.vlines(bc_start, ymin=ymin, ymax=ymax, linewidth=4, linestyle='dashed', color="g")
    #     ax.vlines(bc_end, ymin=ymin, ymax=ymax, linewidth=4, linestyle='dashed', color="r")
    # plt.show()
    assert len(bc["backchannel"]) == 2, "Wrong number of backchannels found"
    assert len(bc["pred_backchannel"]) == 1, "Wrong number of backchannels found"


@pytest.mark.functional
def test_prediction_regions(data):
    vad = data["shift"]["vad"][0]  # (600,2)
    ds = VF.get_dialog_states(vad)

    sh = VF.hold_shift_regions(
        vad=vad,
        ds=ds,
        pre_cond_frames=PRE_COND_FRAMES,
        post_cond_frames=POST_COND_FRAMES,
        prediction_region_frames=PREDICTION_REGION_FRAMES,
        prediction_region_on_active=PREDICTION_REGION_ON_ACTIVE,
        min_silence_frames=MIN_SILENCE_FRAMES,
        min_context_frames=MIN_CONTEXT_FRAMES,
        max_frame=MAX_FRAME,
    )
    assert (
        len(sh["shift"]) == 1
    ), f"Number of shifts are incorrect {len(sh['shift'])} != 1"
    assert len(sh["hold"]) == 1, f"Number of holds are incorrect {len(sh['hold'])} != 1"
    assert (
        len(sh["pred_shift"]) == 1
    ), f"Number of pred-shifts are incorrect {len(sh['pred_shift'])} != 1"
    assert (
        len(sh["pred_hold"]) == 1
    ), f"Number of pred-holds are incorrect {len(sh['pred_hold'])} != 1"

    sh = VF.hold_shift_regions(
        vad=vad,
        ds=ds,
        pre_cond_frames=PRE_COND_FRAMES,
        post_cond_frames=POST_COND_FRAMES,
        prediction_region_frames=100,
        prediction_region_on_active=False,
        min_silence_frames=MIN_SILENCE_FRAMES,
        min_context_frames=MIN_CONTEXT_FRAMES,
        max_frame=MAX_FRAME,
    )
    assert (
        len(sh["shift"]) == 1
    ), f"Number of shifts are incorrect {len(sh['shift'])} != 1"
    assert len(sh["hold"]) == 1, f"Number of holds are incorrect {len(sh['hold'])} != 1"
    assert (
        len(sh["pred_shift"]) == 0
    ), f"Number of pred-shifts are incorrect {len(sh['pred_shift'])} != 0"
    assert (
        len(sh["pred_hold"]) == 1
    ), f"Number of pred-holds are incorrect {len(sh['pred_hold'])} != 1"

    sh = VF.hold_shift_regions(
        vad=vad,
        ds=ds,
        pre_cond_frames=PRE_COND_FRAMES,
        post_cond_frames=POST_COND_FRAMES,
        prediction_region_frames=100,
        prediction_region_on_active=True,
        min_silence_frames=MIN_SILENCE_FRAMES,
        min_context_frames=MIN_CONTEXT_FRAMES,
        max_frame=MAX_FRAME,
    )
    # import matplotlib.pyplot as plt
    # from vap_turn_taking.plot_utils import plot_vad_oh
    # fig, [ax, ax1] = plt.subplots(2, 1, figsize=(9, 6))
    # _ = plot_vad_oh(vad, ax=ax)
    # # _ = plot_vad_oh(filled_vad, ax=ax1)
    # ax.axvline(MIN_CONTEXT_FRAMES, linewidth=4, color="k")
    # ax.axvline(MAX_FRAME, linewidth=4, color="k")
    # for start, end, speaker in sh["pred_shift"]:
    #     ax.axvline(start, linewidth=4, color="g")
    #     ax.axvline(end, linewidth=4, color="r")
    # for start, end, speaker in sh["pred_hold"]:
    #     ax.axvline(start, linewidth=4, linestyle="dashed", color="g")
    #     ax.axvline(end, linewidth=4, linestyle="dashed", color="r")
    # for start, end, speaker in sh["shift"]:
    #     ax.axvline(start, linewidth=4, color="g")
    #     ax.axvline(end, linewidth=4, color="r")
    # for start, end, speaker in sh["hold"]:
    #     ax.axvline(start, linewidth=4, linestyle="dashed", color="g")
    #     ax.axvline(end, linewidth=4, linestyle="dashed", color="r")
    # plt.show()
    assert (
        len(sh["shift"]) == 1
    ), f"Number of shifts are incorrect {len(sh['shift'])} != 1"
    assert len(sh["hold"]) == 1, f"Number of holds are incorrect {len(sh['hold'])} != 1"
    assert (
        len(sh["pred_shift"]) == 0
    ), f"Number of pred-shifts are incorrect {len(sh['pred_shift'])} != 0"
    assert (
        len(sh["pred_hold"]) == 0
    ), f"Number of pred-holds are incorrect {len(sh['pred_hold'])} != 0"