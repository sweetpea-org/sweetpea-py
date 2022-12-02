import networkx as nx
import operator as op

from sweetpea._internal.primitive import Factor, DerivedLevel, WithinTrial, Transition
from sweetpea._internal.design_graph import DesignGraph


# Setup
color_list = ["red", "blue"]
color = Factor("color", color_list)
text  = Factor("text",  color_list)

# Congruent factor
congruent = Factor("congruent?", [
    DerivedLevel("con", WithinTrial(op.eq, [color, text])),
    DerivedLevel("inc", WithinTrial(op.ne, [color, text]))
])

# Repeated color factor
repeated_color_factor = Factor("repeated color?", [
    DerivedLevel("yes", Transition(lambda colors: colors[0] == colors[-1], [color])),
    DerivedLevel("no",  Transition(lambda colors: colors[0] != colors[-1], [color]))
])

# Repeated text factor
repeated_text_factor = Factor("repeated text?", [
    DerivedLevel("yes", Transition(lambda texts: texts[0] == texts[-1], [text])),
    DerivedLevel("no",  Transition(lambda texts: texts[0] != texts[-1], [text]))
])


def test_basic_graph():
    dg = DesignGraph([color, text, congruent])

    assert len(dg.graph.nodes()) == 3
    assert dg.graph.has_node("color")
    assert dg.graph.has_node("text")
    assert dg.graph.has_node("congruent?")

    assert len(dg.graph.edges()) == 2
    assert dg.graph.has_edge("congruent?", "color")
    assert dg.graph.has_edge("congruent?", "text")

    # Graph is directed, so these should not exist.
    assert not dg.graph.has_edge("color", "congruent?")
    assert not dg.graph.has_edge("text", "congruent?")


def test_graph_paths():
    dg = DesignGraph([color, text, congruent, repeated_color_factor, repeated_text_factor])

    assert nx.has_path(dg.graph, "congruent?", "color")
    assert nx.has_path(dg.graph, "congruent?", "text")

    assert nx.has_path(dg.graph, "repeated color?", "color")
    assert nx.has_path(dg.graph, "repeated text?", "text")

    assert not nx.has_path(dg.graph, "repeated color?", "text")
    assert not nx.has_path(dg.graph, "repeated text?", "color")
