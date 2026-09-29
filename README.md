# PHPcallGraph

Static call-graph analysis for PHP projects.

PHPcallGraph parses PHP source files with the [`ast`](https://www.php.net/manual/en/book.ast.php) extension, extracts classes, functions, methods, and calls, and exports the result as Graphviz DOT, JSON, and HTML.

## Requirements

- Python 3.10 or newer
- PHP CLI
- PHP `ast` extension
- Graphviz is optional and is only required when rendering DOT files to SVG

Install the PHP AST extension with PECL when it is not already installed:

```bash
pecl install ast
```

## Usage

The recommended entry point is:

```bash
python3 phpcallgraph.py /path/to/php-project
```

Specify an output directory:

```bash
python3 phpcallgraph.py /path/to/php-project --output-dir ./output
```

Skip directories and enable detailed logging:

```bash
python3 phpcallgraph.py /path/to/php-project \
  --skip-dir vendor \
  --skip-dir tests \
  --verbose
```

Use a custom PHP executable or parser script:

```bash
python3 phpcallgraph.py /path/to/php-project \
  --php /usr/bin/php \
  --php-parser ./parse_ast.php
```

The legacy command remains available for compatibility:

```bash
python3 astTree.py /path/to/php-project
```

## Output

The default output directory is `data/`. The refactored analyzer writes:

- `callgraph.dot` — Graphviz representation
- `callgraph.json` — machine-readable graph data and statistics
- `callgraph.html` — an HTML summary of symbols and unresolved calls

Render a DOT graph with Graphviz:

```bash
dot -Tsvg data/callgraph.dot -o data/callgraph.svg
```

## Project structure

```text
├── astTree.py                 # Backward-compatible CLI wrapper
├── phpcallgraph.py            # Recommended CLI entry point
├── parse_ast.php              # PHP AST to JSON parser
├── src/
│   ├── analyzer.py            # Project-level orchestration
│   ├── ast_visitor.py         # AST traversal and extraction
│   ├── config.py              # CLI and configuration
│   ├── models.py              # Symbols, calls, and graph models
│   ├── php_parser.py          # Safe PHP subprocess wrapper
│   └── exporters/             # DOT, JSON, and HTML exporters
└── docs/
    └── ARCHITECTURE.md        # Design and extension notes
```

## How it works

1. Python discovers PHP files under the project directory.
2. `parse_ast.php` parses each file using `php-ast`.
3. The AST visitor extracts symbols and calls.
4. The analyzer builds a project-wide graph.
5. Exporters write DOT, JSON, and HTML results.

Static analysis cannot resolve every dynamic PHP call. Calls that cannot be matched to a discovered symbol are retained as unresolved or external calls rather than silently discarded.

## Error handling

By default, analysis continues when an individual file cannot be parsed. Use `--strict` to fail on the first analysis error:

```bash
python3 phpcallgraph.py /path/to/php-project --strict
```

Parser errors are written to stderr and the parser returns a non-zero exit code. The Python wrapper also validates the PHP executable, parser script, source files, and JSON output.

## Development

Run the CLI from the repository root so that the `src` package is importable:

```bash
python3 phpcallgraph.py --help
```

The project is being migrated incrementally from the original monolithic `astTree.py` implementation. The modular components are designed to make parser, visitor, graph, and exporter behavior independently testable.

## License

No license has currently been declared for this repository.
