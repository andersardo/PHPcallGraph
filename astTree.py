#!/usr/bin/env python3
"""Backward compatibility wrapper for astTree.py.

NOTE: This file is deprecated and provided for backward compatibility only.
      New code should use: python3 phpcallgraph.py <project-directory>

The original astTree.py has been refactored into a modular architecture:
  - src/main.py: Main entry point
  - src/analyzer.py: Project analysis orchestration
  - src/config.py: Configuration management
  - src/models.py: Data models
  - src/ast_visitor.py: AST traversal
  - src/php_parser.py: PHP parser wrapper
  - src/exporters/: Multiple export formats

All original functionality is preserved and improved:
  - Better error handling
  - Cleaner CLI interface
  - Multiple output formats (DOT, JSON, HTML)
  - Modular and testable code
"""

import sys

from src.main import main

if __name__ == "__main__":
    sys.exit(main())
