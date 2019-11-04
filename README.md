SweetPea
========

[![Build Status](https://travis-ci.org/sweetpea-org/sweetpea-py.svg?branch=master)](https://travis-ci.org/sweetpea-org/sweetpea-py)

SweetPea is a language for declaratively specifying randomized experimental designs, and a runtime for synthesizing trial sequences generated from the design specification; this prototype that is targeted at psychology and neuroscience experiments.

An experimental design is a description of experimental factors, relationships between factors, sequential constraints, and how to map those factors onto a sequence of trials. The reliability and validity of experimental results heavily relies on rigorous experimental design.

SweetPea provides a high-level interface to declaratively describe an experimental design, and a low-level synthesizer to generate unbiased sequences of trials given satisfiable constraints. SweetPea samples sequences of trials by compiling experimental designs into Boolean logic, which are then passed to a SAT-sampler. The SAT-sampler [Unigen](https://bitbucket.org/kuldeepmeel/unigen) provides statistical guarantees that the solutions it finds are approximately uniformly probable in the space of all valid solutions. This means that while producing sequences of trials that are perfectly unbiased is intractable, we do the next best thing-- produce sequences that are approximately unbiased.

## Disclaimer!

This project is at an early stage, and likely to change: it isn't yet ready for real-world useage. Please don't rely on any of this code!

## Usage

SweetPea requires Python 3.5 or later. It also depends on [docker][1] being installed and running on your machine so that it can start a docker container for the backend server.

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
constraints = [AtMostKInARow(k, ("congruent?", "con"))]

block        = fully_cross_block(design, crossing, constraints)

experiments  = synthesize_trials(block)

print_experiments(block, experiments)
```

Additional examples can be found in the `example_programs` directory. 


## Contributing

### Setup

It is recommended to prepare a [virtual environment][venv] for SweetPea development. From within the `sweetpea-py` directory, create a new venv:

```
$ python3 -m venv sweetpea-py-env
```

Active the virtual environment:

```
$ source sweetpea-py-env/bin/activate
```

Once the virtual environment has been activated, pip install all dependencies and `sweetpea-py` itself:

```
# Dependencies
$ pip install -r requirements.txt

# SweetPea
$ pip install -e <path>/<to>/sweetpea-py
```

### Tests

Run unit tests with `make`. These should only take a few seconds to finish.

```
$ make test
```

SweetPea also has a set of end to end or 'acceptance' tests to test the full integration of all components. These are also run with `make`:

```
$ make acceptance
```

Or:

```
$ make full
```

The acceptance tests depend on the SweetPea server. By default, the tests will start and stop the server for each test. This is incredibly slow, and would make the acceptance tests take hours to complete.

To run the acceptance tests, it's recommended that you start the server container yourself:

```
$ docker run --rm -d -p 8080:8080 -p 6379:6379 sweetpea/server
```

Then set an environment variable to tell SweetPea that you are managing the server yourself:

```
$ export SWEETPEA_EXTERNAL_DOCKER_MGMT=true
```

When that environment variable is set, SweetPea will never try to start/stop the server container. Once that is done, the acceptance tests typically complete in 5-7 minutes.

[1]: https://www.docker.com/
[2]: https://docs.python.org/3/tutorial/venv.html

# Specify a Port
By default, SweetPea attempts to run its docker server using port 8080 on the host machine. If this port is not available, it can be changed by setting the SWEETPEA_DOCKER_PORT environment variable. For example, if SweetPea should instead run on port 5050, 
```
$ export SWEETPEA_DOCKER_PORT=5050
```
will then change the running port to 5050.