"""Export call graph as Graphviz DOT format."""

import logging
from pathlib import Path
from typing import TextIO

from ..models import CallGraph

logger = logging.getLogger(__name__)


class DOTExporter:
    """Export call graph to Graphviz DOT format."""

    @staticmethod
    def escape_label(text: str) -> str:
        """Escape a string for use as a DOT label.

        Args:
            text: Text to escape

        Returns:
            Escaped text safe for DOT labels
        """
        text = text.replace("\\", "\\\\\\\\")
        text = text.replace('"', '\\\\"')
        text = text.replace("\n", "\\\\n")
        return text

    @staticmethod
    def node_id(name: str) -> str:
        """Generate a safe node identifier from a name.

        Args:
            name: Symbol name

        Returns:
            Safe node identifier
        """
        safe_id = name.replace("::", "_").replace("\\", "_")
        if safe_id and safe_id[0].isdigit():
            safe_id = f"__{safe_id}"
        return safe_id

    def export(self, graph: CallGraph, output: TextIO) -> None:
        """Export the call graph to DOT format.

        Args:
            graph: The call graph to export
            output: File-like object to write to
        """
        output.write("digraph CallGraph {\n")
        output.write("  rankdir=LR;\n")
        output.write("  nodesep=0.3;\n")
        output.write("  ranksep=0.25;\n")
        output.write("  overlap=False;\n\n")

        output.write("  // Nodes\n")
        for node_name in sorted(graph.nodes):
            node_id = self.node_id(node_name)
            label = self.escape_label(node_name)
            output.write(
                f'  {node_id} [label="{label}", style=filled, '
                f'fillcolor=cornflowerblue, shape=box];\n'
            )

        output.write("\n  // Edges\n")
        for edge in sorted(graph.edges, key=lambda e: (e.source, e.target)):
            source_id = self.node_id(edge.source)
            target_id = self.node_id(edge.target)
            output.write(f"  {source_id} -> {target_id};\n")

        output.write("\n  // Unresolved/External calls\n")
        for unresolved in sorted(graph.unresolved_calls):
            node_id = self.node_id(unresolved)
            label = self.escape_label(unresolved)
            output.write(
                f'  {node_id} [label="{label}", style=filled, '
                f'fillcolor=coral, shape=box];\n'
            )

        output.write("}\n")
