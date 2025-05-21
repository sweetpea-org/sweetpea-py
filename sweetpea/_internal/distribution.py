from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union, cast, Literal

import random
from abc import ABC, abstractmethod

class Distribution(ABC):
    """Base class for different  distributions."""
    
    @abstractmethod
    def sample(self, factor_values: List[Any] = []) -> float:
        pass  # Must be implemented by subclasses

    def get_init(self) ->List[Any]:
        return []

    def reset(self) -> None:
        """Optional reset hook."""
        pass

class UniformDistribution(Distribution):
    def __init__(self, low: float, high: float):
        self.low = low
        self.high = high

    def sample(self, factor_values: List[Any] = []) -> float:
        return random.uniform(self.low, self.high)

class GaussianDistribution(Distribution):
    def __init__(self, mean: float, sigma: float):
        self.mean = mean
        self.sigma = sigma

    def sample(self, factor_values: List[Any] = []) -> float:
        return random.gauss(self.mean, self.sigma)

class ExponentialDistribution(Distribution):
    def __init__(self, rate: float):
        self.rate = rate

    def sample(self, factor_values: List[Any] = []) -> float:
        return random.expovariate(self.rate)

class LogNormalDistribution(Distribution):
    def __init__(self, mean: float, sigma: float):
        self.mean = mean
        self.sigma = sigma

    def sample(self, factor_values: List[Any] = []) -> float:
        return random.lognormvariate(self.mean, self.sigma)

class CustomDistribution(Distribution):
    """Allows users to provide a custom distribution with any parameters."""
    
    def __init__(self, func: Callable[..., float], *args: Any, **kwargs: Any):
        """
        :param func: A callable function that generates a float sample.
        :param args: Positional arguments for the function.
        :param kwargs: Keyword arguments for the function.
        """
        # Currently it does not receive any position or keyword argument
        if not callable(func):
            raise TypeError("Wrong custom distribution type for CustomDistribution: required Callable, Got {}".format(type(func)))
        
        self.func = func
        self.dependents = []
        self.sum = 0.
        self.cumulative = False

        if len(args)>0:
            for k in args[0]:
                self.dependents.append(k)
        if 'cumulative' in kwargs:           
            self.cumulative = kwargs['cumulative']


    def sample(self, factor_values: List[Any] = []) -> float:
        if factor_values and (not isinstance(factor_values, list)):
            raise RuntimeError(f"factor_values must be a list, got {type(factor_values)}")
        if len(factor_values)!= len(self.dependents):
            raise RuntimeError(f"Mismatched input length: {len(factor_values)} values vs {len(self.dependents)} dependents")
        if not self.cumulative:
            return self.func(*factor_values)
        else:
            self.sum+= self.func(*factor_values)
            return self.sum

    def get_init(self) ->List[Any]:
        return self.dependents

    def reset(self):
        self.sum = 0.
