SweetPea
========

SweetPea is a language for declaratively specifying randomized experimental designs, and a runtime for synthesizing trial sequences generated from the design specification; this prototype that is targeted at psychology and neuroscience experiments. 

An experimental design is a description of experimental factors, relationships between factors, sequential constraints, and how to map those factors onto a sequence of trials. The reliability and validity of experimental results heavily relies on rigorous experimental design.

SweetPea provides a high-level interface to declaratively describe an experimental design, and a low-level synthesizer to generate unbiased sequences of trials given satisfiable constraints. SweetPea samples sequences of trials by compiling experimental designs into Boolean logic, which are then passed to a SAT-sampler. The SAT-sampler [Unigen](https://bitbucket.org/kuldeepmeel/unigen) provides statistical guarantees that the solutions it finds are approximately uniformly probable in the space of all valid solutions. This means that while producing sequences of trials that are perfectly unbiased is intractable, we do the next best thing-- produce sequences that are approximately unbiased.


## Disclaimer!

This project is at an early stage, and likely to change: it isn't yet ready for real-world useage. Please don't rely on any of this code!


## Usage

SweetPea also depends on [Docker][1] being installed and running on your machine. 

Intstall with `pip`:

```
pip install sweetpea
```

Example:

```python
import operator as op

from sweetpea import *

color = Factor("color", ["red", "blue"])
text  = Factor("text",  ["red", "blue"])

conLevel  = DerivedLevel("con", WithinTrial(op.eq, [color, text]))
incLevel  = DerivedLevel("inc", WithinTrial(op.ne, [color, text]))
conFactor = Factor("congruent?", [conLevel, incLevel])

design       = [color, text, conFactor]
crossing     = [color, text]

k = 1
constraints = [NoMoreThanKInARow(k, ("congruent?", "con"))]

block        = fully_cross_block(design, crossing, constraints)

experiments  = synthesize_trials(block)

print_experiments(block, experiments)
```

[1]: https://www.docker.com/

