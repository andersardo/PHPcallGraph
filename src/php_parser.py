"""PHP file parsing and AST extraction."""

import json
import logging
import subprocess
from pathlib import Path
from typing import Any, Optional

from .errors import PHPParserError

logger = logging.getLogger(__name__)


class PHPParser:
    """Wrapper for the PHP AST parser."""

    def __init__(
        self,
        php_executable: str = "php",
        parser_script: Optional[str] = None,
    ):
        """Initialize the PHP parser.

        Args:
            php_executable: Path to the PHP executable
            parser_script: Path to the PHP AST parser script.
                          If not provided, assumes parse_ast.php in same directory as this module.

        Raises:
            PHPParserError: If PHP executable or parser script is not found
        """
        self.php_executable = php_executable
        self.parser_script = parser_script

        if not self.parser_script:
            module_dir = Path(__file__).parent
            self.parser_script = str(module_dir.parent / "parse_ast.php")

        if not self._check_php_available():
            raise PHPParserError(
                f"PHP executable not found: {php_executable}\n"
                "Install PHP or set --php to the correct path."
            )

        if not Path(self.parser_script).exists():
            raise PHPParserError(
                f"PHP AST parser script not found: {self.parser_script}"
            )

    def _check_php_available(self) -> bool:
        """Check if PHP is available and executable."""
        try:
            result = subprocess.run(
                [self.php_executable, "-v"],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def parse(self, source_file: Path) -> dict[str, Any]:
        """Parse a PHP file and return its AST.

        Args:
            source_file: Path to the PHP file to parse

        Returns:
            Dictionary containing the structured AST

        Raises:
            PHPParserError: If parsing fails
        """
        source_file = Path(source_file).resolve()

        if not source_file.exists():
            raise PHPParserError(f"File not found: {source_file}")

        if not source_file.is_file():
            raise PHPParserError(f"Not a file: {source_file}")

        logger.debug(f"Parsing {source_file}")

        try:
            result = subprocess.run(
                [self.php_executable, self.parser_script, str(source_file)],
                capture_output=True,
                text=True,
                timeout=30,
            )
        except subprocess.TimeoutExpired:
            raise PHPParserError(f"Parser timeout for {source_file}")
        except Exception as e:
            raise PHPParserError(f"Failed to run parser for {source_file}: {e}")

        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip()
            raise PHPParserError(f"Parse error in {source_file}: {error_msg}")

        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raise PHPParserError(
                f"Invalid JSON output from parser for {source_file}: {e}"
            )
