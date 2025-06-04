import operator as op
import pytest

from sweetpea._internal.primitive import Factor, DerivedLevel, WithinTrial, Transition, Window, SimpleLevel, ContinuousFactor, ContinuousFactorWindow
from sweetpea import synthesize_trials, RandomGen, MinimumTrials, CrossBlock
from sweetpea._internal.constraint import ContinuousConstraint
import random
import numpy as np
from typing import cast
import math

from sweetpea._internal.distribution import (
    UniformDistribution, GaussianDistribution, 
    ExponentialDistribution, LogNormalDistribution, CustomDistribution
)

def test_basic_window_output():

    # Create a ContinuousFactor with 1 input window (required by sample() signature)
    dummy_window = ContinuousFactorWindow([], width=3, stride=1)  
    cf = ContinuousFactor("cf", distribution=CustomDistribution(lambda x: 0.0, [dummy_window]))

    # Runtime data to simulate window access
    values = {"cf": [1.0, 2.0, 3.0, 4.0]}
    
    # Real window test with the same factor
    window = ContinuousFactorWindow([cf], width=3, stride=1)
    result = window.get_window_val(3, values)

    assert result == {0: 4.0, -1: 3.0, -2: 2.0}

def test_window_nan_padding_at_start():
    # Create a minimal valid ContinuousFactor for window construction
    dummy_window = ContinuousFactorWindow([], width=3, stride=1)
    cf = ContinuousFactor("cf", distribution=CustomDistribution(lambda x: 0.0, [dummy_window]))

    # Provide fewer values than needed for a full window
    values = {"cf": [5.0, 6.0]}  # Only 2 values, insufficient for width=3
    window = ContinuousFactorWindow([cf], width=3, stride=1)

    # This index is before the window is valid (start = width - 1 = 2)
    result = window.get_window_val(1, values)

    # Should return a dict of NaNs
    assert isinstance(result, dict)
    assert set(result.keys()) == {0, -1, -2}
    assert all(math.isnan(v) for v in result.values())

def test_window_multiple_factors():
    # Create two minimal ContinuousFactors
    dummy_window1 = ContinuousFactorWindow([], width=2, stride=1)
    dummy_window2 = ContinuousFactorWindow([], width=2, stride=1)

    f1 = ContinuousFactor("f1", distribution=CustomDistribution(lambda x: 0.0, [dummy_window1]))
    f2 = ContinuousFactor("f2", distribution=CustomDistribution(lambda x: 0.0, [dummy_window2]))

    # Simulated runtime values
    values = {
        "f1": [10.0, 20.0, 30.0],
        "f2": [1.0, 2.0, 3.0]
    }

    # Create a window that includes both factors
    window = ContinuousFactorWindow([f1, f2], width=2, stride=1)

    # idx = 2 → valid for width=2
    result = window.get_window_val(2, values)

    assert isinstance(result, list)
    assert len(result) == 2

    expected_f1 = {0: 30.0, -1: 20.0}
    expected_f2 = {0: 3.0, -1: 2.0}

    assert result[0] == expected_f1
    assert result[1] == expected_f2


def test_window_stride_behavior():
    # Dummy ContinuousFactor setup
    dummy_window = ContinuousFactorWindow([], width=3, stride=2)
    f = ContinuousFactor("cf", distribution=CustomDistribution(lambda x: 0.0, [dummy_window]))

    values = {"cf": [1.0, 2.0, 3.0, 4.0, 5.0]}

    # Create a window with stride=2
    window = ContinuousFactorWindow([f], width=3, stride=2)

    # Aligned index (start = width - 1 = 2, stride = 2 → valid indices = 2, 4, ...)
    result_aligned = window.get_window_val(4, values)
    assert isinstance(result_aligned, dict)
    assert result_aligned == {0: 5.0, -1: 4.0, -2: 3.0}

    # Non-aligned index (e.g., 3 is not 2 + n * stride)
    result_unaligned = window.get_window_val(3, values)
    assert isinstance(result_unaligned, dict)
    assert all(math.isnan(v) for v in result_unaligned.values())


def test_window_default_start():
    dummy_window = ContinuousFactorWindow([], width=4, stride=1)
    f = ContinuousFactor("cf", distribution=CustomDistribution(lambda x: 0.0, [dummy_window]))

    # Create a window without explicitly setting `start`
    window = ContinuousFactorWindow([f], width=4)  # No start provided
    assert window.start == 3  # width - 1

def test_window_invalid_factor_type():
    color = Factor("color", ["red", "blue"])
    # Attempt to create a window with an invalid factor type
    with pytest.raises(TypeError) as exc_info:
        ContinuousFactorWindow([color], width=3)

    assert "ContinuousFactorWindow can only be constructed on ContinuousFactor" in str(exc_info.value)


def test_window_nan_on_negative_index_access():
    # Set up a dummy ContinuousFactor
    dummy_window = ContinuousFactorWindow([], width=3)
    f = ContinuousFactor("cf", distribution=CustomDistribution(lambda x: 0.0, [dummy_window]))

    # Only a few values available
    values = {"cf": [9.0, 8.0]}
    window = ContinuousFactorWindow([f], width=3)

    # Index 1 → window attempts to access idx-2 (=-1), which is invalid
    result = window.get_window_val(1, values)

    assert isinstance(result, dict)
    assert set(result.keys()) == {0, -1, -2}

    # Value at offset -2 should be NaN due to idx-2 < 0
    assert math.isnan(result[-2])


def test_window_stride_and_start_combination():
    # Dummy continuous factor
    dummy_window = ContinuousFactorWindow([], width=3, stride=2)
    f = ContinuousFactor("cf", distribution=CustomDistribution(lambda x: 0.0, [dummy_window]))

    values = {"cf": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]}

    # Explicitly set start to 2 (could also rely on default = width - 1)
    window = ContinuousFactorWindow([f], width=3, stride=2, start=2)

    # Index 2 — valid start, stride-aligned → expect real values
    result_2 = window.get_window_val(2, values)
    assert result_2 == {0: 3.0, -1: 2.0, -2: 1.0}

    # Index 3 — after start, but NOT aligned with stride=2 → expect NaNs
    result_3 = window.get_window_val(3, values)
    assert all(math.isnan(v) for v in result_3.values())

    # Index 4 — aligned again (start=2, stride=2 → 2, 4, 6...) → expect real values
    result_4 = window.get_window_val(4, values)
    assert result_4 == {0: 5.0, -1: 4.0, -2: 3.0}

def test_custom_distribution_integration_with_window():
    # Distribution function: difference between current and previous value
    def diff_func(window_data):
        return window_data[0] - window_data[-1]

    # Dummy values passed via get_window_val
    values = {"cf": [1.0, 2.0, 3.0, 4.0]}

    # Create the factor and window
    window = ContinuousFactorWindow([], width=2)
    cf = ContinuousFactor("cf", distribution=CustomDistribution(diff_func, [window]))

    # Simulate windowing
    real_window = ContinuousFactorWindow([cf], width=2)
    window_vals = real_window.get_window_val(3, values)

    # Run the custom function as a stand-in for .sample()
    result = diff_func(window_vals)

    assert result == 4.0 - 3.0


def test_cumulative_custom_distribution_with_window():
    # Function to compute difference in window (current - previous)
    def delta(window_data):
        return window_data[0] - window_data[-1]

    # Set up window and distribution with cumulative=True
    window = ContinuousFactorWindow([], width=2)
    distribution = CustomDistribution(delta, [window], cumulative=True)

    cf = ContinuousFactor("cf", distribution=distribution)

    # Simulate multiple windowed evaluations across trials
    real_window = ContinuousFactorWindow([cf], width=2)

    # Input values for cf across time
    values = {"cf": [10.0, 12.0, 15.0, 18.0]}  # deltas: 2, 3, 3 → cumulative: 2, 5, 8

    cumulative_results = []
    distribution.reset()  # start fresh

    for idx in range(1, len(values["cf"])):
        window_vals = real_window.get_window_val(idx, values)
        result = distribution.sample([window_vals])
        cumulative_results.append(result)

    assert cumulative_results == [2.0, 5.0, 8.0]

def test_combined_windows_across_factors():
    def compute_sum(window_a, window_b):
        return window_a[-1] + window_b[-2]

    # Two dummy continuous factors
    factor_a = ContinuousFactor("factor_a", distribution=CustomDistribution(lambda: 0.0))
    factor_b = ContinuousFactor("factor_b", distribution=CustomDistribution(lambda: 0.0))

    # Corresponding windows
    window_a = ContinuousFactorWindow([factor_a], width=2)
    window_b = ContinuousFactorWindow([factor_b], width=3)

    # Simulated runtime values
    values = {
        "factor_a": [1.1, 1.5],        # idx=1: -1 = 1.1,  0 = 1.5
        "factor_b": [2.0, 2.3, 2.9]    # idx=2: -2 = 2.0, -1 = 2.3, 0 = 2.9
    }

    a_vals = window_a.get_window_val(1, values)
    b_vals = window_b.get_window_val(2, values)

    result = compute_sum(a_vals, b_vals)

    assert result == 1.1 + 2.0  


def test_multi_factor_window_input_unpacking():
    def custom_add(factor_windows, other_window):
        # factor_windows: [dict from factor_a, dict from factor_b]
        vals_a = factor_windows[0]
        vals_b = factor_windows[1]
        return vals_a[-1] + vals_b[-1] + other_window[-2]

    # Dummy continuous factors
    factor_a = ContinuousFactor("factor_a", distribution=CustomDistribution(lambda: 0.0))
    factor_b = ContinuousFactor("factor_b", distribution=CustomDistribution(lambda: 0.0))
    factor_c = ContinuousFactor("factor_c", distribution=CustomDistribution(lambda: 0.0))

    # Window for multiple input factors (A and B)
    multi_window = ContinuousFactorWindow([factor_a, factor_b], width=2)
    other_window = ContinuousFactorWindow([factor_c], width=3)

    # Simulated trial data
    values = {
        "factor_a": [1.0, 1.1],       # idx = 1
        "factor_b": [2.0, 2.1],       # idx = 1
        "factor_c": [0.0, 0.0, 4.0]   # idx = 2
    }

    multi_input = multi_window.get_window_val(1, values)  # Returns: [dict for a, dict for b]
    other_input = other_window.get_window_val(2, values)  # Returns: dict for c

    result = custom_add(multi_input, other_input)

    assert result == 1.0 + 2.0 + 0.0  

