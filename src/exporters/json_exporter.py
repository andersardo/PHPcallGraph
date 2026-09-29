"""Export call graph as JSON."""

import json
import logging
from pathlib import Path
from typing import Any, TextIO

from ..models import CallGraph

logger = logging.getLogger(__name__)


class JSONExporter:
    """Export call graph to JSON format."""

    def export(self, graph: CallGraph, output: TextIO) -> None:
        """Export the call graph to JSON format.

        Args:
            graph: The call graph to export
            output: File-like object to write to
        """
        data = {
            "nodes": sorted(graph.nodes),
            "edges": [
                {
                    "source": edge.source,
                    "target": edge.target,
                    "kind": edge.kind.value,
                }
                for edge in sorted(graph.edges, key=lambda e: (e.source, e.target))
            ],
            "unresolved_calls": sorted(graph.unresolved_calls),
            "external_calls": sorted(graph.external_calls),
            "statistics": {
                "total_nodes": len(graph.nodes),
                "total_edges": len(graph.edges),
                "unresolved_calls": len(graph.unresolved_calls),
                "external_calls": len(graph.external_calls),
            },
        }

        json.dump(data, output, indent=2)
        output.write("\n")
