"""This module provides functionality for building graphs representing the
relationships between factors in a given design.
"""


from typing import List

import networkx as nx

from sweetpea.primitives import DerivedFactor, Factor


class DesignGraph():
    """Builds a directed graph representing the relationship between all
    factors in the design. Primary intent is to facilitate preventing invalid
    crossings.
    """

    def __init__(self, design: List[Factor]) -> None:
        self.design = design
        self.graph = self.__build_graph(design)

    def __build_graph(self, design: List[Factor]) -> nx.DiGraph:
        g = nx.DiGraph()

        for f in design:
            # Add the factor as a node.
            g.add_node(f.name)

            # Simple factors (not derived) are the leaves.
            if not isinstance(f, DerivedFactor):
                continue

            # Add directed edges between this factor and all factors that it depends on.
            for l in f.levels:
                for depended_on_factor in l.window.factors:
                    g.add_edge(f.name, depended_on_factor.name)

        return g

    def draw(self):
        import matplotlib as plt
        nx.draw(self.graph, with_labels=True)
        plt.show()

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)
