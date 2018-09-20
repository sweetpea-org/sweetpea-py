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

TODO

[1]: https://www.docker.com/

