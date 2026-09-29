<?php declare(strict_types=1);

/**
 * PHP AST Parser - Extract abstract syntax tree from PHP files as JSON.
 *
 * Usage: php parse_ast.php <file>
 *
 * Output: JSON on stdout (or error message on stderr)
 * Exit codes:
 *   0: Success
 *   1: Usage error (missing or invalid arguments)
 *   2: Environment error (PHP AST extension not available)
 *   3: File error (file not found or not readable)
 *   4: Parse error (PHP syntax error)
 *   5: JSON encoding error (internal error)
 */

use ast\flags;

// Constants for AST dump options
const AST_DUMP_LINENOS = 1;
const AST_DUMP_EXCLUDE_DOC_COMMENT = 2;

/**
 * Validate command-line arguments.
 *
 * @throws RuntimeException if arguments are invalid
 * @return string Absolute path to the PHP file to parse
 */
function validate_arguments(): string
{
    global $argc, $argv;

    if ($argc !== 2) {
        throw new RuntimeException("Usage: php parse_ast.php <file>");
    }

    $file = $argv[1];

    if (!file_exists($file)) {
        throw new RuntimeException("File not found: {$file}");
    }

    if (!is_file($file)) {
        throw new RuntimeException("Not a file: {$file}");
    }

    if (!is_readable($file)) {
        throw new RuntimeException("File is not readable: {$file}");
    }

    return realpath($file) ?: $file;
}

/**
 * Check that the PHP AST extension is available.
 *
 * @throws RuntimeException if the extension is not loaded
 */
function check_ast_extension(): void
{
    if (!extension_loaded('ast')) {
        throw new RuntimeException(
            "PHP AST extension not available. Install with: pecl install ast"
        );
    }
}

/**
 * Get metadata about AST node flags.
 *
 * @return array Array of [exclusive flags, combinable flags]
 */
function get_flag_info(): array
{
    static $info = null;

    if ($info !== null) {
        return $info;
    }

    $info = [[], []];

    foreach (ast\get_metadata() as $data) {
        if (empty($data->flags)) {
            continue;
        }

        $flagMap = [];
        foreach ($data->flags as $fullName) {
            $shortName = substr($fullName, strrpos($fullName, '\\') + 1);
            $flagMap[constant($fullName)] = $shortName;
        }

        $combinable = (int) $data->flagsCombinable;
        $info[$combinable][$data->kind] = $flagMap;
    }

    return $info;
}

/**
 * Check if a given AST node kind uses combinable flags.
 *
 * @param int $kind AST node kind
 * @return bool
 */
function is_combinable_flag(int $kind): bool
{
    [, $combinable] = get_flag_info();
    return isset($combinable[$kind]);
}

/**
 * Format AST node flags as a human-readable string.
 *
 * @param int $kind AST node kind
 * @param int $flags Flag value(s)
 * @return string Formatted flag string
 */
function format_flags(int $kind, int $flags): string
{
    [$exclusive, $combinable] = get_flag_info();

    if (isset($exclusive[$kind])) {
        $flagInfo = $exclusive[$kind];
        if (isset($flagInfo[$flags])) {
            return "{$flagInfo[$flags]} ($flags)";
        }
    } elseif (isset($combinable[$kind])) {
        $flagInfo = $combinable[$kind];
        $names = [];
        foreach ($flagInfo as $flag => $name) {
            if ($flags & $flag) {
                $names[] = $name;
            }
        }
        if (!empty($names)) {
            return implode(" | ", $names) . " ($flags)";
        }
    }

    return (string) $flags;
}

/**
 * Convert an AST node to a structured associative array.
 *
 * @param mixed $ast AST node, list, or scalar value
 * @param int $options Dump options (bitmask)
 * @return mixed Structured representation
 */
function ast_to_struct($ast, int $options = 0)
{
    if ($ast instanceof ast\Node) {
        $kind = ast\get_kind_name($ast->kind);
        $result = [$kind => []];

        if ($options & AST_DUMP_LINENOS) {
            $linenos = "{$ast->lineno}";
            if (isset($ast->endLineno)) {
                $linenos .= "-{$ast->endLineno}";
            }
            $result[$kind]['linenos'] = $linenos;
        }

        // Add flags if present
        if ((ast\kind_uses_flags($ast->kind) && !is_combinable_flag($ast->kind)) || $ast->flags != 0) {
            $result[$kind]['flags'] = format_flags($ast->kind, $ast->flags);
        }

        // Process children
        foreach ($ast->children as $name => $child) {
            // Skip doc comments if requested
            if (($options & AST_DUMP_EXCLUDE_DOC_COMMENT) && $name === 'docComment') {
                continue;
            }

            $result[$kind][$name] = ast_to_struct($child, $options);
        }

        return $result;
    } elseif ($ast === null) {
        return null;
    } elseif (is_string($ast)) {
        return '"' . $ast . '"';
    } else {
        return $ast;
    }
}

/**
 * Parse a PHP file and return its AST as structured JSON.
 *
 * @param string $file Path to PHP file
 * @return string JSON-encoded structured AST
 * @throws RuntimeException on parse error
 */
function parse_php_file(string $file): string
{
    try {
        // $astTree = ast\parse_file($file, ast\version\LATEST);
        $astTree = ast\parse_file($file, 110);
    } catch (ParseError $e) {
        throw new RuntimeException(
            "Parse error in {$file} at line {$e->getLine()}: {$e->getMessage()}"
        );
    } catch (Throwable $e) {
        throw new RuntimeException(
            "Error parsing {$file}: {$e->getMessage()}"
        );
    }

    $structured = ast_to_struct($astTree, AST_DUMP_EXCLUDE_DOC_COMMENT);

    try {
        return json_encode($structured, JSON_THROW_ON_ERROR | JSON_UNESCAPED_SLASHES);
    } catch (JsonException $e) {
        throw new RuntimeException(
            "JSON encoding error: {$e->getMessage()}"
        );
    }
}

/**
 * Main entry point.
 */
function main(): int
{
    try {
        check_ast_extension();
        $file = validate_arguments();
        $json = parse_php_file($file);
        echo $json;
        return 0;
    } catch (RuntimeException $e) {
        fwrite(STDERR, "Error: {$e->getMessage()}\n");
        return 1;
    } catch (Throwable $e) {
        fwrite(STDERR, "Fatal error: {$e->getMessage()}\n");
        fwrite(STDERR, $e->getTraceAsString() . "\n");
        return 5;
    }
}

exit(main());
