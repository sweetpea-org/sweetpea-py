import operator as op
import pytest

from sweetpea._internal.primitive import Factor, DerivedLevel, WithinTrial, Transition, Window, SimpleLevel, ContinuousFactor
from sweetpea import synthesize_trials, RandomGen, MinimumTrials, CrossBlock
from sweetpea._internal.constraint import ConstinuousConstraint
import random
import numpy as np
from typing import cast

color = Factor("color", ["red", "blue", "green", "brown"])

def sample_continuous():
    return random.uniform(0.5, 1.5)
time_sample_function = ContinuousFactor("time_sample_function", [], sampling_function=sample_continuous)

# Different sampling methods
time_uniform = ContinuousFactor("time_uniform", [], sampling_method='uniform', sampling_range=[0,10])
time_gaussian = ContinuousFactor("time_gaussian", [], sampling_method='gaussian', sampling_range=[0,1])
time_exponential = ContinuousFactor("time_exponential", [], sampling_method='exponential', sampling_range=[1,])
time_lognormal = ContinuousFactor("time_lognormal", [], sampling_method='lognormal', sampling_range=[0,1])

# Derived Factors
def difference(t1, t2):
    return t1-t2

difference_time = ContinuousFactor("difference_time", [
    time_uniform, time_gaussian], sampling_function=difference)

difference_time1 = ContinuousFactor("difference_time1", [
    difference_time, time_exponential], sampling_function=difference)

def color2time(color):
    if color == "red":
        return random.uniform(0, 1)
    elif color == "blue":
        return random.uniform(1, 2)
    elif color == "green":
        return random.uniform(2, 3)
    else:
        return random.uniform(3, 4)

color_time = ContinuousFactor("color_time", [
    color], sampling_function=color2time)

# Constraints
def greater_than_2(a, b):
    return (a+b>2)
cc = ConstinuousConstraint([time_gaussian, time_exponential], greater_than_2)


# Factor Tests
def test_factor_type():
    assert isinstance(time_sample_function, ContinuousFactor) == True
    assert isinstance(time_uniform, ContinuousFactor) == True
    assert isinstance(time_gaussian, ContinuousFactor) == True
    assert isinstance(time_exponential, ContinuousFactor) == True
    assert isinstance(time_lognormal, ContinuousFactor) == True

def test_sampling_range():
    t1 = []
    t2 = []
    t3 = []
    for i in range(1000):
        result = time_sample_function.generate()
        result1 = time_uniform.generate()
        t1.append(time_gaussian.generate())
        t2.append(time_exponential.generate())
        t3.append(time_lognormal.generate())
        # Check if the value is between 0 and 1
        assert 0.5<= result <= 1.5
        assert 0<= result1 <= 10

    mean = 0
    std_dev = 1
    tolerance = 0.1
    sample_mean = np.mean(t1)
    sample_std = np.std(t1)
    
    assert abs(sample_mean - mean) < tolerance, f"Expected mean {mean}, got {sample_mean}"
    assert abs(sample_std - std_dev) < tolerance, f"Expected std {std_dev}, got {sample_std}"

    rate = 1
    sample_mean = np.mean(t2)
    assert abs(sample_mean - (1 / rate)) < tolerance, f"Mean is off by more than {tolerance}: {sample_mean}"

    tolerance = 0.2
    sample_mean = np.mean(t3)
    expected_mean = np.exp(mean + (std_dev ** 2) / 2)
    assert abs(sample_mean - expected_mean) < tolerance, f"Mean is off by more than {tolerance}: {sample_mean}"


def test_factor_validation():
    # This will use a default sampling function
    ContinuousFactor("name", [], sampling_method=None)

    # Incorrect sampling method name
    with pytest.raises(ValueError):
        ContinuousFactor('response_time', [], sampling_method="random")

    # Incorrect sampling method name
    with pytest.raises(ValueError):
        ContinuousFactor('response_time', [], sampling_function="random")

    with pytest.raises(ValueError):
        ContinuousFactor('response_time', [], sampling_function=1)


def test_factor_get_level():
    assert time_sample_function.get_level("red") is None
    assert time_sample_function.get_level(1) is None
    assert time_sample_function.get_levels() == []
    assert time_sample_function.initial_levels == []
    assert difference_time.get_level(1) is None
    assert difference_time.get_levels() == [time_uniform, time_gaussian]
    assert difference_time.initial_levels == [time_uniform, time_gaussian]

def test_factor_has_complex_window():
	assert time_sample_function.has_complex_window == False    
	assert difference_time.has_complex_window == False

def test_factor_applies_to_trial():
    assert difference_time.applies_to_trial(1) == True
    assert difference_time.applies_to_trial(2) == True
    assert time_sample_function.applies_to_trial(1) == True
    assert time_sample_function.applies_to_trial(2) == True

    with pytest.raises(ValueError):
        time_sample_function.applies_to_trial(0)


# Block Tests
def test_block_creation():
    block = CrossBlock([color, time_sample_function], [color], [])

    with pytest.raises(RuntimeError):
        CrossBlock([color, time_sample_function], [color, time_sample_function], [])

    with pytest.raises(RuntimeError):
        CrossBlock([color, time_sample_function], [time_sample_function], [])

def test_has_factor():
    block = CrossBlock([color, time_sample_function], [color], [])
    assert block.has_factor(time_sample_function) == time_sample_function
    assert block.has_factor(difference_time) == cast(Factor, None)

def test_block_size():
    block = CrossBlock([color, time_sample_function], [color], [])
    assert block.crossing_size() == 4

# Trial Factor Dependency Tests
def test_trial_factor_dependence():
    design = [color, time_uniform, time_gaussian, time_exponential, difference_time, difference_time1]
    crossing = [color]
    block = CrossBlock(design, crossing, [MinimumTrials(40)])
    experiments  = synthesize_trials(block, 5)

    for ind in range(len(experiments)):
        time_uniform_sample = np.array(experiments[ind][time_uniform.name])
        time_gaussian_sample = np.array(experiments[ind][time_gaussian.name])
        time_exponential_sample = np.array(experiments[ind][time_exponential.name])
        difference_time_sample = np.array(experiments[ind][difference_time.name])
        difference_time1_sample = np.array(experiments[ind][difference_time1.name])
        # print(time_gaussian_sample, time_exponential_sample)
        assert np.array_equal(time_uniform_sample - time_gaussian_sample, difference_time_sample)
        assert np.array_equal(difference_time_sample - time_exponential_sample, difference_time1_sample)

    design = [color, color_time]
    crossing = [color]
    block = CrossBlock(design, crossing, [MinimumTrials(40)])
    experiments  = synthesize_trials(block, 5)

    for ind in range(len(experiments)):
        color_trial = experiments[ind][color.name]
        color_time_trial = experiments[ind][color_time.name]
        
        for i in range(len(color_trial)):
            if color_trial[i] == "red":
                assert 0 <= color_time_trial[i]<=1
            if color_trial[i] == "blue":
                assert 1 <= color_time_trial[i]<=2
            if color_trial[i] == "green":
                assert 2 <= color_time_trial[i]<=3
            if color_trial[i] == "brown":
                assert 3 <= color_time_trial[i]<=4

# Continuous Constraint Tests
def test_continuous_constraint():
    design = [color, time_gaussian, time_exponential]
    crossing = [color]
    block = CrossBlock(design, crossing, [cc])
    experiments  = synthesize_trials(block, 5)

    for ind in range(len(experiments)):
        time_gaussian_sample = np.array(experiments[ind][time_gaussian.name])
        time_exponential_sample = np.array(experiments[ind][time_exponential.name])
        sum_sample = time_gaussian_sample+time_exponential_sample
        assert np.all(sum_sample > 2)