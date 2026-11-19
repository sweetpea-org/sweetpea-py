"""Example programs offered in the GUI's Examples menu."""

from pathlib import Path

REPO = Path(__file__).resolve().parents[3]

EXAMPLES = [
    ("Simple: color × size", "A derived 'volume' factor from color and size; 4 trials.",
     REPO / "example_programs" / "Simple.py"),
    ("Stroop", "Color × word with congruency, response and response transitions; 33 trials.",
     REPO / "example_programs" / "Stroop_simple.py"),
    ("Stroop, congruency balanced", "Crosses color with congruency instead of word; 17 trials.",
     REPO / "example_programs" / "Stroop_congruency_balanced.py"),
    ("Task switching", "Color and motion tasks with task and response transitions; 12 trials.",
     REPO / "example_programs" / "TaskSwitching_simple.py"),
    ("Nested sessions (Nest)", "Days hold sessions, which hold A × B trials; 16 trials.",
     REPO / "gui" / "examples" / "nested_sessions.py"),
    ("Stroop sessions (Nest, Repeat, Merge)", "Two sessions of repeated Stroop trials, merged with a balanced "
     "response hand; 16 trials.", REPO / "gui" / "examples" / "stroop_sessions.py"),
]


def list_examples() -> list:
    return [{"title": title, "description": description, "code": path.read_text(encoding="utf-8")}
            for title, description, path in EXAMPLES]
