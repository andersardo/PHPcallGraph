"""Project analysis orchestration."""

import logging
from pathlib import Path
from typing import Optional

from .ast_visitor import ASTVisitor
from .config import Config
from .errors import AnalysisError, PHPParserError
from .models import CallGraph, FileAnalysis, GraphEdge
from .php_parser import PHPParser

logger = logging.getLogger(__name__)


class ProjectAnalyzer:
    """Analyze a PHP project and build a call graph."""

    def __init__(self, config: Config):
        """Initialize the analyzer.

        Args:
            config: Application configuration

        Raises:
            AnalysisError: If initialization fails
        """
        self.config = config
        self.php_parser = PHPParser(
            php_executable=config.php_executable,
            parser_script=config.php_parser,
        )
        self.file_analyses: dict[Path, FileAnalysis] = {}
        self.errors: list[tuple[Path, str]] = []

    def analyze(self) -> CallGraph:
        """Analyze the project and return the call graph.

        Returns:
            CallGraph containing symbols and calls for the project
        """
        php_files = self._find_php_files()
        logger.info(f"Found {len(php_files)} PHP files to analyze")

        for php_file in php_files:
            self._analyze_file(php_file)

        call_graph = self._build_graph()
        logger.info(
            f"Analysis complete: {len(call_graph.nodes)} nodes, "
            f"{len(call_graph.edges)} edges"
        )

        return call_graph

    def _find_php_files(self) -> list[Path]:
        """Find all PHP files in the project.

        Returns:
            List of paths to PHP files
        """
        php_files = []
        for php_file in self.config.project_dir.rglob("*.php"):
            if self._should_skip(php_file):
                continue
            php_files.append(php_file)

        return sorted(php_files)

    def _should_skip(self, file_path: Path) -> bool:
        """Check if a file should be skipped.

        Args:
            file_path: Path to check

        Returns:
            True if the file should be skipped
        """
        if not self.config.skip_dirs:
            return False

        file_str = str(file_path)
        for skip_pattern in self.config.skip_dirs:
            if skip_pattern in file_str:
                return True

        return False

    def _analyze_file(self, php_file: Path) -> None:
        """Analyze a single PHP file.

        Args:
            php_file: Path to the PHP file
        """
        if self.config.verbose:
            logger.info(f"Analyzing {php_file}")

        try:
            ast_data = self.php_parser.parse(php_file)
            visitor = ASTVisitor(php_file, ast_data)
            analysis = visitor.visit()
            self.file_analyses[php_file] = analysis

            if not analysis.success:
                logger.warning(
                    f"File had errors: {php_file} "
                    f"({len(analysis.parse_errors)} errors)"
                )

        except PHPParserError as e:
            error_msg = f"Parse error: {e}"
            logger.error(f"Failed to analyze {php_file}: {error_msg}")
            self.errors.append((php_file, error_msg))

            if self.config.strict:
                raise AnalysisError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            logger.error(f"Failed to analyze {php_file}: {error_msg}")
            self.errors.append((php_file, error_msg))

            if self.config.strict:
                raise AnalysisError(error_msg) from e

    def _build_graph(self) -> CallGraph:
        """Build the call graph from analyzed files.

        Returns:
            CallGraph with all symbols and calls
        """
        graph = CallGraph()

        for analysis in self.file_analyses.values():
            for symbol in analysis.symbols:
                graph.nodes.add(symbol.qualified_name)
                graph.symbols[symbol.qualified_name] = symbol

        for analysis in self.file_analyses.values():
            for call in analysis.calls:
                graph.edges.add(
                    GraphEdge(
                        source=call.caller,
                        target=call.callee,
                        kind=call.kind,
                    )
                )

                if call.callee not in graph.symbols:
                    graph.unresolved_calls.add(call.callee)
                    if not self.config.include_stdlib:
                        graph.external_calls.add(call.callee)

        return graph
