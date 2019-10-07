import matplotlib.pyplot as plt
import networkx as nx

from typing import List

from sweetpea.primitives import Factor


"""
Builds a directed graph representing the relationship between all factors in the design.
Primary intent is to facilitate preventing invalid crossings.
"""
class DesignGraph():
    def __init__(self, design: List[Factor]) -> None:
        self.design = design
        self.graph = self.__build_graph(design)

    def __build_graph(self, design: List[Factor]) -> nx.DiGraph:
        g = nx.DiGraph()

        for f in design:
            # Add the factor as a node.
            g.add_node(f.factor_name)

            # Simple factors (not derived) are the leaves.
            if not f.is_derived():
                continue

            # Add directed edges between this factor and all factors that it depends on.
            for l in f.levels:
                for depended_on_factor in l.window.args:
                    g.add_edge(f.factor_name, depended_on_factor.factor_name)

        return g

    def draw(self):
        nx.draw(self.graph, with_labels=True)
        plt.show()

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)
