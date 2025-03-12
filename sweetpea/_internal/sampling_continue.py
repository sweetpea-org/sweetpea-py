from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union, cast, Literal

import random
from abc import ABC, abstractmethod

class SamplingMethod(ABC):
    """Base class for different sampling methods."""
    
    @abstractmethod
    def sample(self, sample_input: List[Any] = []) -> float:
        pass  # Must be implemented by subclasses

    def get_init(self) ->List[Any]:
        return []

class UniformSampling(SamplingMethod):
    def __init__(self, low: float, high: float):
        self.low = low
        self.high = high

    def sample(self, sample_input: List[Any] = []) -> float:
        return random.uniform(self.low, self.high)

class GaussianSampling(SamplingMethod):
    def __init__(self, mean: float, sigma: float):
        self.mean = mean
        self.sigma = sigma

    def sample(self, sample_input: List[Any] = []) -> float:
        return random.gauss(self.mean, self.sigma)

class ExponentialSampling(SamplingMethod):
    def __init__(self, rate: float):
        self.rate = rate

    def sample(self, sample_input: List[Any] = []) -> float:
        return random.expovariate(self.rate)

class LogNormalSampling(SamplingMethod):
    def __init__(self, mean: float, sigma: float):
        self.mean = mean
        self.sigma = sigma

    def sample(self, sample_input: List[Any] = []) -> float:
        return random.lognormvariate(self.mean, self.sigma)

class CustomSampling(SamplingMethod):
    """Allows users to provide a custom sampling function with any parameters."""
    
    def __init__(self, func: Callable[..., float], *args: Any):
        """
        :param func: A callable function that generates a float sample.
        :param args: Positional arguments for the function.
        :param kwargs: Keyword arguments for the function.
        """
        # Currently it does not receive any position or keyword argument
        if not callable(func):
            raise TypeError("Wrong custom function type for CustomSampling: required Callable, Got {}".format(type(func)))
        
        self.func = func
        self.dependents = []
        
        if len(args)>0:
            for k in args[0]:
                self.dependents.append(k)


    def sample(self, sample_inputs: List[Any] = []) -> float:
        return self.func(*sample_inputs)

    def get_init(self) ->List[Any]:
        return self.dependents
