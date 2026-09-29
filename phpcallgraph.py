#!/usr/bin/env python3
"""PHPcallGraph - Static call graph analyzer for PHP projects.

Usage:
    python3 phpcallgraph.py <project-directory>
    python3 phpcallgraph.py <project-directory> --output-dir ./output
    python3 phpcallgraph.py <project-directory> --skip-dir vendor --skip-dir tests
"""

import sys

from src.main import main

if __name__ == "__main__":
    sys.exit(main())
