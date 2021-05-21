SweetPea
========

| Build Status                                                                                                               |
|----------------------------------------------------------------------------------------------------------------------------|
| [![typecheck](../../actions/workflows/typecheck.yml/badge.svg)](../../actions/workflows/typecheck.yml)                     |
| [![acceptance (fast)](../../actions/workflows/acceptance-fast.yml/badge.svg)](../../actions/workflows/acceptance-fast.yml) |
| [![acceptance (slow)](../../actions/workflows/acceptance-slow.yml/badge.svg)](../../actions/workflows/acceptance-slow.yml) |
| [![package](../../actions/workflows/test.yml/badge.svg)](../../actions/workflows/test.yml)                                 |

SweetPea is a domain-specific language for specifying factorial experimental
designs and synthesizing trial sequences from those design specifications. An
explanation of factorial experimental designs and how to build and manipulate
them in SweetPea can be found in [the SweetPea
Guide](https://sweetpea-org.github.io).

SweetPea includes a synthesizer to generate unbiased sequences of trials that
satisfy the design's constraints. In the most general case, SweetPea compiles an
experimental design into a boolean satisfiability formula that is passed to a
SAT sampler.

Currently, SweetPea uses the [Unigen SAT
sampler](https://bitbucket.org/kuldeepmeel/unigen). Unigen provides statistical
guarantees that the solutions it finds are approximately uniformly probable in
the space of all valid solutions. Unfortunately, sampling this way is not
tractable for all designs that can be expressed with SweetPea, and improving
sampling strategies is a primary direction for ongoing work.


## Disclaimer

SweetPea is still under active development, and therefore the interface and API
may change. Please use with caution!


## Dependencies

SweetPea requires Python 3.7.9 or later.


## Installation

There are two ways to install SweetPea: from [the Python Package
Index](https://pypi.org) (PyPI), or from source.


### Installing from PyPI

SweetPea can be installed from PyPI via `pip`:

    $ pip install sweetpea

This version may lag behind the current development version.


### Installing from Source

To get the most up-to-date version of SweetPea, clone this repository, install
SweetPea's dependencies, and install SweetPea itself:

    $ git clone https://github.com/sweetpea-org/sweetpea-py.git
    $ cd sweetpea-py
    $ pip install -r requirements.txt
    $ pip install .

---

> #### :exclamation: Important!
>
> The `pip install .` command installs SweetPea locally, but it will not
> automatically check for updates. If you intend to manually update your local
> copy of SweetPea, you should instead do `pip install -e .` to tell `pip` to
> use the source dynamically.

---


## Examples

There are example programs in the [`example_programs`](example_programs/)
directory, and there is a detailed explanation of how to use SweetPea in [the
SweetPea Guide](https://sweetpea-org.github.io).


## API Documentation

The SweetPea API is documented in [the API section of the SweetPea
Guide](https://sweetpea-org.github.io/api.html).


## Contributing

Information on how to contribute to SweetPea's development can be found in [the
Contributing section of the SweetPea
Guide](https://sweetpea-org.github.io/guide/contributing.html).
