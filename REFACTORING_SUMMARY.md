# Refactoring summary

This branch refactors PHPcallGraph from a monolithic `astTree.py` script into a modular analysis pipeline while preserving the original command as a compatibility wrapper.

## Changes

### PHP parser

- Added `parse_ast.php` as the canonical PHP AST parser.
- Validates command-line arguments, input files, and the `php-ast` extension.
- Writes JSON only to stdout and diagnostics to stderr.
- Uses `JSON_THROW_ON_ERROR`.
- Removes unreachable code from the former `parse2text.php` implementation.
- Keeps `parse2data.php` as a deprecation shim.

### Python architecture

- `src/config.py` contains CLI parsing and validated configuration.
- `src/php_parser.py` invokes PHP safely without `shell=True`.
- `src/ast_visitor.py` extracts symbols and calls using AST-node dispatch.
- `src/models.py` defines symbols, calls, file analyses, and graph edges.
- `src/analyzer.py` orchestrates file discovery, parsing, traversal, and graph construction.
- `src/exporters/` provides DOT, JSON, and HTML output.
- `src/logging_config.py` centralizes logging behavior.

### Entry points

Recommended:

```bash
python3 phpcallgraph.py tests/fixtures/simple_project
```

Backward-compatible:

```bash
python3 astTree.py tests/fixtures/simple_project
```

## Expected fixture behavior

The sample fixture contains:

- A global function call: `entry()` calls `helper()`.
- A class and methods.
- An instance method call.
- A static method call.
- A constructor call.
- An unresolved/external function call.

Expected output files are written to `data/` by default:

```text
data/
├── callgraph.dot
├── callgraph.html
└── callgraph.json
```

## Known limitations

This is the first modular refactoring phase. Static PHP analysis remains conservative for:

- Dynamic function calls.
- Dynamic method calls.
- Runtime dependency injection.
- Trait composition.
- Namespace imports and aliases.
- Complete type inference for variables.

These should be addressed with focused visitor and name-resolution improvements rather than by reintroducing global state.

## Recommended next steps

1. Add automated Python tests for the models, parser wrapper, visitor, and exporters.
2. Add PHP parser integration tests when PHP and `php-ast` are available.
3. Preserve source line numbers in `Symbol` and `Call` records.
4. Improve qualified-name and namespace resolution.
5. Add optional Graphviz SVG generation.
6. Add a `pyproject.toml` and CI workflow for linting and tests.
