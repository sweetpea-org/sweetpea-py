.. _distribution:

Distributions
=============

.. class:: sweetpea.Distribution


           Abstract class for the input distribution for :class:`.ContinuousFactor`.
           A subclass of :class:`.Distribution` must be instantiated 
           to represent the distribution that the factor follows when 
           generating values dynamically. 

.. class:: sweetpea.UniformDistribution(low, high)

           Represents a uniform distribution for :class:`.ContinuousFactor`,
           where values are sampled evenly between the 
           specified `low` and `high` bounds.

           :param low: The lower bound of the uniform distribution.
           :type low: float
           :param high: The upper bound of the uniform distribution. Must be greater than lower bound.
           :type high: float
           :rtype: Distribution
    
.. class:: sweetpea.GaussianDistribution(mean, sigma)

           Represents a Gaussian (normal) distribution for 
           :class:`.ContinuousFactor`, where values are sampled according 
           to the specified mean and standard deviation.

           :param mean: The mean of the normal distribution.
           :type mean: float
           :param sigma: The standard deviation of the distribution. Must be greater than zero.
           :type sigma: float
           :rtype: Distribution

.. class:: sweetpea.ExponentialDistribution(rate)

           Represents an exponential distribution for :class:`.ContinuousFactor`,
           where values are sampled according to the specified `rate` parameter 
           (the inverse of the mean) of the exponential distribution.

           :param rate: The rate parameter of the exponential distribution. Must be greater than zero.
           :type rate: float
           :rtype: Distribution

.. class:: sweetpea.LogNormalDistribution(mean, sigma)

           Represents a log-normal distribution for :class:`.ContinuousFactor`,
           where values are sampled according to the specified `mean` and `sigma` parameters.

           :param mean: The mean of the underlying normal distribution.
           :type mean: float
           :param sigma: The standard deviation of the underlying normal distribution. Must be greater than zero.
           :type sigma: float
           :rtype: Distribution

.. class:: sweetpea.CustomDistribution(func, function_inputs=[])

           Represents a custom distribution for :class:`.ContinuousFactor`, 
           where values are sampled according to the specified custom sampling
           function, `func`. An optional input `function_inputs` can be also provided as 
           the input for `func`. When `function_inputs` contains a :class:`.Factor`
           or :class:`.ContinuousFactor`, the :class:`.ContinuousFactor` becomes 
           a *derived factor*. The factors in the `function_inputs` must be in the `design`
           of the experiment. The `func` will sample based on the values/levels of these
           factors during each trial. 

           :param func: A function that generates values based on the specified inputs.
           :type func: Callable
           :param function_inputs: A list of inputs to pass to the `func` when generating values. Defaults to an empty list.
           :type function_inputs: List[Any]
           :rtype: Distribution
           
