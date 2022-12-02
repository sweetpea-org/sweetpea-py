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
them in SweetPea can be found in [the SweetPea Guide](https://sweetpea-org.github.io).

> See also the [paper](https://link.springer.com/article/10.3758/s13428-021-01598-2)
> describing SweetPea, but beware that the API has changed. The main changes are
> replacing most functions with classes, changing some function names, and
> simplifying the organization to just a `sweetpea` module that exports everything.

SweetPea includes a synthesizer to generate sequences of trials that
satisfy the design's constraints. The goal is to generate sequences
that are unbiased: every possible sequence of trials that satifies the
design constraints is equally likely to be generated, which avoids
correlations that are not part of the experiment's definition. With
current technologies, SweetPea achieves that goal for designs with
either simple constraints or a small number of combinations. SweetPea
can also generate samples that seem uniform in practice for
medium-sized designs, although without a formal guarantee. Generating
unbiased samples for large designs remains an area of active research
and development.

For designs that do not involve constraints that span trials within a
sequence, SweetPea can directly sample with combinatoric techniques.
Realistic designs often involve transition constraints or other
cross-trial constraints, however. For those cases, SweetPea's primary
sampling strategy compiles an experiment design into a boolean
formula; compilation ensures a 1-to-1 correspondence between distinct
satisfying assignments to the boolean formula and distinct trial
sequences, so that uniformly sampling solutions to the boolean formula
imples a unform sample of trial sequences. SweetPea uses
[CMSGen](https://github.com/kuldeepmeel/cmsgen) and
[UniGen](https://github.com/kuldeepmeel/unigen) to sample solutions to
the boolean formula. CMSGen generates samples that appear to be well
distributed in practice, but CMSGen lacks a formal guarantee of
uniformity. UniGen provides statistical guarantees that the solutions
it finds are approximately uniformly probable, but its approach is
tractable only for the smallest designs that are expressed with
SweetPea.


## Dependencies

SweetPea requires Python 3.7.9 or later.


## Installation

There are two ways to install SweetPea: from [the Python Package
Index](https://pypi.org) (PyPI), or from source.


### Installing from PyPI

SweetPea can be installed from PyPI via `pip`:

    $ pip install sweetpea


### Installing from Source

Clone this repository, install SweetPea's dependencies, and install
SweetPea itself:

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
