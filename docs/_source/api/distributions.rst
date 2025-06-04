.. _distribution:

Distributions
=============

.. class:: sweetpea.Distribution


           Abstract class for the input distribution for :class:`.ContinuousFactor`.
           A subclass of :class:`.Distribution` must be instantiated 
           to represent the distribution that the factor follows when 
           generating values dynamically. When a :class:`.Distribution` is used
           to initialize a :class:`.ContinuousFactor`, a corresponding 
           `distribution` object is created for the factor.

           .. method:: sample()

               Generate values based on the input distribution

               :returns: a value sampled from the input distribution
               :rtype: Any

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

.. class:: sweetpea.CustomDistribution(func, dependents=[], cumulative=False)

           Represents a custom distribution for :class:`.ContinuousFactor`, 
           where values are generated through calling a custom function, `func`. 
           
           :class:`.CustomDistribution` can also accept an optional argument 
           `dependents`, which is the list of factors the current 
           :class:`.ContinuousFactor` depends on. `dependents` can only contain
           :class:`.DiscreteFactor` or :class:`.ContinuousFactor` in the design.

           When `dependents` is empty, the :class:`.ContinuousFactor` is 
           a *non-derived factor* and `func` should not require additional 
           inputs to generate values. 

           When `dependents` is not empty, the :class:`.ContinuousFactor` becomes 
           a *derived factor*. In such cases, `func` requires additional inputs 
           to generate values. Since the values of the dependent factors are not known
           when intializing :class:`.CustomDistribution`, the values of these factors,  
           `factor_values`, need to be passed to `func` at runtime. See 
           :meth:`.CustomDistribution.sample` for more details.
        
           Optionally, the argument `cumulative` can be set to `True` to enable accumulation.
           In this mode, the return value of each `func` call is added to a running sum,
           and that sum is returned instead of the raw result. The running sum can be
           reset between experiments or blocks by calling :meth:`.reset`.

           :param func: A custom function to generate values.
           :type func: Callable
           :param dependents: A list of factors that :class:`.ContinuousFactor` depends on.
           :type dependents: List[Factor]
           :param cumulative: Whether the distribution should return cumulative results.
           :type cumulative: bool
           :rtype: Distribution

           .. method:: sample(factor_values: List[Any]=[])

               Generate values using the custom `func`. 

               :param factor_values: optional factor values when `dependents` is not empty
                                     for :class:`.CustomDistribution`. The size of 
                                     `factor_values` must be the same as `dependents`.
                                     `factor_values` contains values for factors in 
                                     `dependents` at runtime. 
               :type factor_values: List[Any]
               :returns: a value generated by calling `func`
               :rtype: Any

           .. method:: reset()

               Resets the cumulative sum used when `cumulative=True`.
               This is typically called at the start of a new experiment
               or trial sequence to prevent carryover.
