SweetPea
========

| Build Status                                                                                                      |
|-------------------------------------------------------------------------------------------------------------------|
| ![typecheck](https://github.com/sweetpea-org/sweetpea-py/actions/workflows/typecheck.yml/badge.svg)               |
| ![acceptance (fast)](https://github.com/sweetpea-org/sweetpea-py/actions/workflows/acceptance-fast.yml/badge.svg) |
| ![acceptance (slow)](https://github.com/sweetpea-org/sweetpea-py/actions/workflows/acceptance-slow.yml/badge.svg) |
| ![package](https://github.com/sweetpea-org/sweetpea-py/actions/workflows/test.yml/badge.svg)                      |

SweetPea is a language for declaratively specifying randomized experimental designs and synthesizing trial sequences generated from the design specification.
An experimental design is a description of experimental factors, relationships between factors, sequential constraints, and how to map those factors onto a sequence of trials. Such a design is constructed by calling SweetPea functions such as `fully_cross_block`, `factor`, `derived_level`, and `at_most_k_in_a_row`.

SweetPea includes a synthesizer to generate unbiased sequences of trials that satisfy the design's constraints. In the most general case, SweetPea compiles an experimental design into a boolean formula that is passed to a SAT sampler; the SAT sampler [Unigen](https://bitbucket.org/kuldeepmeel/unigen) provides statistical guarantees that the solutions it finds are approximately uniformly probable in the space of all valid solutions. Unfortunately, sampling this way is not tractable for all designs that can be expressed with SweetPea, and improving sampling strategies is a primary direction for ongoing work.

## Disclaimer

While the SweetPea language (as an API) is relatively stable, its interface is still likely to evolve for now. Use with caution.

## Usage

SweetPea requires Python 3.5 or later. It also depends on [Docker][1] being installed and running on your machine so that it can start a container for the backend server.

Intstall SweetPea with `pip`:

```
pip install sweetpea
```

Example:

```python
import operator as op

from sweetpea import *

color = factor("color", ["red", "blue"])
text  = factor("text",  ["red", "blue"])

con_level  = derived_level("con", within_trial(op.eq, [color, text]))
inc_level  = derived_level("inc", within_trial(op.ne, [color, text]))
con_factor = factor("congruent?", [con_level, inc_level])

design       = [color, text, con_factor]
crossing     = [color, text]

k = 1
constraints = [at_most_k_in_a_row(k, (con_factor, con_level))]

block        = fully_cross_block(design, crossing, constraints)

experiments  = synthesize_trials(block)

print_experiments(block, experiments)
```

Additional examples can be found in the `example_programs` directory.

## Full Documentation

See [https://sweetpea-org.github.io/](https://sweetpea-org.github.io/).

## Contributing

### Setup

It is recommended to prepare a [virtual environment][2] for SweetPea development. From within the `sweetpea-py` directory, create a new venv:

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

The acceptance tests depend on the SweetPea server. By default, the tests will start and stop the server for each test. It can be 2-3 times faster to start the server container yourself:

```
$ docker run --rm -d -p 8080:8080 -p 6379:6379 sweetpea/server
```

and then set an environment variable to tell SweetPea that you are managing the server yourself:

```
$ export SWEETPEA_EXTERNAL_DOCKER_MGMT=true
```

When that environment variable is set, SweetPea will never try to start/stop the server container, and the acceptance tests typically complete in 5-7 minutes.

[1]: https://www.docker.com/
[2]: https://docs.python.org/3/tutorial/venv.html

# Specify a Port
By default, SweetPea attempts to run its docker server using port 8080 on the host machine. If this port is not available, it can be changed by setting the `SWEETPEA_DOCKER_PORT` environment variable. For example, if SweetPea should instead run on port 5050,
```
$ export SWEETPEA_DOCKER_PORT=5050
```
will then change the running port to 5050.
