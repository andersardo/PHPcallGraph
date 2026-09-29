# Contributing

## Development workflow

1. Create a branch for the change.
2. Keep parser, visitor, graph, and exporter changes separate where practical.
3. Preserve the JSON contract between `parse_ast.php` and `src/php_parser.py`.
4. Add regression coverage for new AST node types or resolution behavior.
5. Run the CLI against a small PHP fixture before opening a pull request.

## Design guidelines

- Do not use `shell=True` for subprocesses.
- Do not add mutable module-level analysis state.
- Use specific exceptions instead of bare `except` blocks.
- Keep stdout machine-readable where a command promises structured output.
- Escape labels and HTML output at the export boundary.
- Keep output ordering deterministic.
- Treat dynamic or unresolved PHP calls explicitly.

## Suggested test fixtures

A minimal fixture should cover:

```php
<?php
function entry(): void
{
    helper();
}

function helper(): void
{
}
```

Additional fixtures should cover namespaces, classes, instance calls, static calls, constructors, duplicate method names, invalid PHP, and paths containing spaces.
