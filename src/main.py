"""Main CLI entry point for PHPcallGraph."""

import logging
import sys
from pathlib import Path

from .analyzer import ProjectAnalyzer
from .config import parse_arguments
from .errors import PHPcallGraphError
from .exporters.dot import DOTExporter
from .exporters.html import HTMLExporter
from .exporters.json_exporter import JSONExporter
from .logging_config import configure_logging

logger = logging.getLogger(__name__)


def main(args: list[str] | None = None) -> int:
    """Main entry point.

    Args:
        args: Command-line arguments (defaults to sys.argv[1:])

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Parse arguments
        config = parse_arguments(args)

        # Configure logging
        configure_logging(
            verbose=config.verbose,
            log_file=None,
        )

        logger.info(f"PHPcallGraph v0.2.0")
        logger.info(f"Project directory: {config.project_dir}")
        logger.info(f"Output directory: {config.output_dir}")

        # Create output directory
        config.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory created: {config.output_dir}")

        # Run analysis
        analyzer = ProjectAnalyzer(config)
        call_graph = analyzer.analyze()

        # Report results
        logger.info(f"\nAnalysis Results:")
        logger.info(f"  Symbols: {len(call_graph.nodes)}")
        logger.info(f"  Calls: {len(call_graph.edges)}")
        logger.info(f"  Unresolved calls: {len(call_graph.unresolved_calls)}")
        logger.info(f"  External calls: {len(call_graph.external_calls)}")

        if analyzer.errors:
            logger.warning(f"\nEncountered {len(analyzer.errors)} errors during analysis:")
            for file_path, error in analyzer.errors[:5]:
                logger.warning(f"  {file_path}: {error}")
            if len(analyzer.errors) > 5:
                logger.warning(f"  ... and {len(analyzer.errors) - 5} more")

        # Export results
        logger.info(f"\nExporting results to {config.output_dir}")
        _export_results(call_graph, config.output_dir)

        logger.info("Analysis complete.")
        return 0

    except KeyboardInterrupt:
        logger.error("Interrupted by user.")
        return 130
    except PHPcallGraphError as e:
        logger.error(f"Error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


def _export_results(call_graph, output_dir: Path) -> None:
    """Export call graph in multiple formats.

    Args:
        call_graph: The call graph to export
        output_dir: Directory to export to
    """
    # Export as DOT
    dot_file = output_dir / "callgraph.dot"
    with open(dot_file, "w") as f:
        DOTExporter().export(call_graph, f)
    logger.info(f"Exported DOT: {dot_file}")

    # Export as JSON
    json_file = output_dir / "callgraph.json"
    with open(json_file, "w") as f:
        JSONExporter().export(call_graph, f)
    logger.info(f"Exported JSON: {json_file}")

    # Export as HTML
    html_file = output_dir / "callgraph.html"
    with open(html_file, "w") as f:
        HTMLExporter().export(call_graph, f)
    logger.info(f"Exported HTML: {html_file}")


if __name__ == "__main__":
    sys.exit(main())
