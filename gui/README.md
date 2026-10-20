# SweetPea Designer

A browser-based editor for SweetPea designs, aimed at researchers who don't
write Python. The design is built in four steps (Factors → Design →
Constraints → Generate), and a Python pane beside the steps shows the same
design as a SweetPea program. Editing either one updates the other.

## Running

The server needs FastAPI and uvicorn in the environment that has SweetPea:

```bash
pip install -r gui/backend/requirements.txt
```

Build the front end once (Node 18+):

```bash
cd gui/frontend && npm install && npm run build
```

Then start the server, which serves the built front end and opens a browser:

```bash
cd gui/backend && python -m sweetpea_gui
```

For front-end development, run `npm run dev` in `gui/frontend` while the
server is running; Vite forwards `/api` calls to it.

Backend tests: `cd gui/backend && python -m pytest tests`.

## How code and GUI stay in sync

The GUI's state is a JSON *design* (below). The server turns a design into a
program (`codegen.py`) and reads a program back into a design (`parse.py`).

- An edit in the GUI renders the design into the code pane. This rewrites the
  whole program in a standard layout, so comments and formatting in the pane
  are not kept.
- An edit in the code pane is read back into a design after a short pause.
  `parse.py` interprets the program rather than running it, and accepts only
  what the GUI can show. Anything else is reported with its line number, and
  the GUI is locked until the code can be read again.
- Generating trials runs the program that `codegen.py` produces for the
  design (`run.py`), so the GUI samples exactly the code it shows.

`parse.py` reads programs written by hand as well as generated ones: predicate
functions defined with `def` or `lambda`, `if ...: return True else: return
False` bodies, calls from one predicate to another, `in` tests, and
variables for levels, constants, and lists.

The GUI cannot yet show `Window` derivations, `ContinuousFactor`,
`MultiCrossBlock`, `Merge`/`Nest`/`Repeat`, `Relax`, sampler objects such as
`RandomGen(acceptable_error=3)`, or code that uses the generated trials.

## Design JSON

```jsonc
{
  "factors": [
    {"name": "color", "kind": "basic",
     "levels": [{"name": "red", "weight": 1}, {"name": "blue", "weight": 1}]},
    {"name": "congruency", "kind": "within",          // or "transition"
     "inputs": ["color", "word"],
     "levels": [
       {"name": "con", "weight": 1,
        "rule": {"cmp": "==", "left": {"factor": "color", "at": 0},
                               "right": {"factor": "word", "at": 0}}},
       {"name": "other", "weight": 1, "rule": null}      // ElseLevel
     ]}
  ],
  "crossing": ["color", "word"],
  "constraints": [{"type": "AtMostKInARow", "k": 3, "factor": "color", "level": null}],
  "requireCompleteCrossing": true,
  "samples": 5,
  "sampler": "CMSGen"
}
```

Factors appear in definition order; every factor is in the block's design.

A **rule** is one of:

- `{"cmp": "==" | "!=", "left": term, "right": term}`
- `{"all": [rule, ...]}`, `{"any": [rule, ...]}`, `{"not": rule}`

A **term** is `{"factor": name, "at": 0 | -1}` (in a transition, `-1` is the
previous trial; within a trial `at` is `0`) or `{"level": value}`.

**Constraints** carry a `type` and the fields of that constraint:
`k` (`AtMostKInARow`, `AtLeastKInARow`, `ExactlyKInARow`, `ExactlyK`),
`factor` and `level` (`level: null` means the whole factor), `index` (`Pin`),
`trials` (`MinimumTrials`), `factors` (`LatinSquare`, `CoverAllCombinations`),
and `optional` (`CoverAllCombinations`).
