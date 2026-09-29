# Test fixtures

This directory contains small PHP projects used to manually exercise the refactored analyzer.

Run the sample from the repository root:

```bash
python3 phpcallgraph.py tests/fixtures/simple_project --output-dir /tmp/phpcallgraph-data
```

The fixture is intentionally small and includes global functions, classes, methods, a constructor, a static call, an instance call, and an unresolved external call.
