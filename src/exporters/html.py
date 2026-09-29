"""Export call graph as HTML."""

import logging
from pathlib import Path
from typing import TextIO

from ..models import CallGraph

logger = logging.getLogger(__name__)


class HTMLExporter:
    """Export call graph to HTML format."""

    @staticmethod
    def escape_html(text: str) -> str:
        """Escape text for HTML.

        Args:
            text: Text to escape

        Returns:
            Escaped text safe for HTML
        """
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
        )

    def export(self, graph: CallGraph, output: TextIO) -> None:
        """Export the call graph to HTML format.

        Args:
            graph: The call graph to export
            output: File-like object to write to
        """
        output.write(
            """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Call Graph Analysis</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        h2 { color: #666; margin-top: 30px; }
        table { border-collapse: collapse; width: 100%; margin-top: 10px; }
        th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
        th { background-color: #f5f5f5; font-weight: bold; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        .code { font-family: monospace; background-color: #f5f5f5; padding: 2px 4px; }
    </style>
</head>
<body>
"""
        )

        output.write("<h1>Call Graph Analysis</h1>\n")

        output.write("<h2>Statistics</h2>\n")
        output.write("<ul>\n")
        output.write(f"<li>Total symbols: {len(graph.nodes)}</li>\n")
        output.write(f"<li>Total calls: {len(graph.edges)}</li>\n")
        output.write(f"<li>Unresolved calls: {len(graph.unresolved_calls)}</li>\n")
        output.write(f"<li>External calls: {len(graph.external_calls)}</li>\n")
        output.write("</ul>\n")

        output.write("<h2>Symbols</h2>\n")
        output.write("<table>\n")
        output.write("<tr><th>Name</th><th>Kind</th></tr>\n")
        for node_name in sorted(graph.nodes):
            symbol = graph.symbols.get(node_name)
            kind = symbol.kind.value if symbol else "unknown"
            output.write(
                f"<tr><td><span class='code'>"
                f"{self.escape_html(node_name)}</span></td>"
                f"<td>{kind}</td></tr>\n"
            )
        output.write("</table>\n")

        if graph.unresolved_calls:
            output.write("<h2>Unresolved Calls</h2>\n")
            output.write("<table>\n")
            output.write("<tr><th>Call Name</th></tr>\n")
            for call_name in sorted(graph.unresolved_calls):
                output.write(
                    f"<tr><td><span class='code'>"
                    f"{self.escape_html(call_name)}</span></td></tr>\n"
                )
            output.write("</table>\n")

        output.write("</body>\n</html>\n")
