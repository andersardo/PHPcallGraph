"""Configuration and CLI argument handling."""

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Config:
    """Application configuration."""

    project_dir: Path
    output_dir: Path = field(default_factory=lambda: Path("data"))
    skip_dirs: list[str] = field(default_factory=lambda: [])
    php_executable: str = "php"
    php_parser: Optional[str] = None
    include_stdlib: bool = False
    verbose: bool = False
    strict: bool = False

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        self.project_dir = Path(self.project_dir).resolve()
        self.output_dir = Path(self.output_dir).resolve()

        if not self.project_dir.is_dir():
            raise ValueError(f"Project directory does not exist: {self.project_dir}")


def parse_arguments(args: Optional[list[str]] = None) -> Config:
    """Parse command-line arguments and return a Config object.

    Args:
        args: Command-line arguments (defaults to sys.argv[1:])

    Returns:
        Config object with parsed arguments

    Raises:
        ValueError: If arguments are invalid
        SystemExit: If help is requested or arguments are invalid
    """
    parser = argparse.ArgumentParser(
        prog="phpcallgraph",
        description="Create call graphs for PHP projects.",
    )

    parser.add_argument(
        "project_dir",
        help="Path to PHP project directory",
    )

    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("data"),
        help="Output directory (default: data)",
    )

    parser.add_argument(
        "--skip-dir",
        action="append",
        default=[],
        help="Directory pattern to skip (can be repeated)",
    )

    parser.add_argument(
        "--php",
        default="php",
        help="PHP executable path (default: php)",
    )

    parser.add_argument(
        "--php-parser",
        help="Path to PHP AST parser script",
    )

    parser.add_argument(
        "--include-stdlib",
        action="store_true",
        help="Include standard PHP functions in output",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed progress",
    )

    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on parse errors",
    )

    parsed = parser.parse_args(args)

    try:
        config = Config(
            project_dir=Path(parsed.project_dir),
            output_dir=parsed.output_dir,
            skip_dirs=parsed.skip_dir,
            php_executable=parsed.php,
            php_parser=parsed.php_parser,
            include_stdlib=parsed.include_stdlib,
            verbose=parsed.verbose,
            strict=parsed.strict,
        )
    except ValueError as e:
        parser.error(str(e))
        sys.exit(1)

    return config
