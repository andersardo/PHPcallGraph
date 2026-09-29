# Architecture

## Responsibilities

The refactored implementation separates the analysis pipeline into four stages:

```text
CLI configuration
       |
       v
PHP parser ---> AST visitor ---> Call graph ---> Exporters
```

### Configuration

`src/config.py` owns command-line parsing and creates a `Config` object. This keeps filesystem paths, PHP executable settings, skipped directories, and strict-mode behavior out of the analysis logic.

### PHP parsing

`parse_ast.php` is a small process boundary around `php-ast`. It writes JSON to stdout and diagnostics to stderr. `src/php_parser.py` invokes it with an argument list rather than a shell command, validates the result, and converts failures into `PHPParserError`.

### AST traversal

`src/ast_visitor.py` uses dispatch by AST node kind. It extracts `Symbol` and `Call` records while tracking the current namespace, class, and function context.

The visitor intentionally records unresolved names. PHP permits dynamic calls and runtime resolution, so static analysis should preserve uncertainty rather than inventing a target.

### Domain models

`src/models.py` contains the data exchanged between stages:

- `Symbol` — a class, function, or method definition
- `Call` — a call site and its resolution metadata
- `FileAnalysis` — results for one PHP file
- `CallGraph` — project-wide nodes, edges, and unresolved calls

### Exporters

Exporters consume `CallGraph` without re-parsing PHP:

- `DOTExporter` produces Graphviz DOT
- `JSONExporter` produces machine-readable output
- `HTMLExporter` produces a browsable summary

This makes adding another output format independent of parsing and analysis.

## Compatibility strategy

`astTree.py` remains as a compatibility wrapper and delegates to the new CLI. New integrations should use `phpcallgraph.py` or import `src.main.main` directly.

The original output names and behavior are not yet fully identical to the old implementation. The migration prioritizes safer subprocess execution, structured models, deterministic exports, and testability.

## Extension points

Future work should be added in these areas:

1. Add qualified-name resolution for namespace imports and aliases.
2. Improve instance method resolution using inferred variable types.
3. Add source line information to symbols and calls.
4. Add tests for representative PHP AST fixtures.
5. Add optional SVG rendering through a Graphviz exporter step.
6. Add caching keyed by source-file content and parser version.
