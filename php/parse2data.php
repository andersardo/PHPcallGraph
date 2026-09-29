<?php
/**
 * DEPRECATED: This file has been superseded by parse_ast.php
 *
 * parse_ast.php provides:
 * - Cleaner CLI interface
 * - Proper error handling and exit codes
 * - Better input validation
 * - Reliable JSON output
 *
 * Use parse_ast.php instead:
 *   php parse_ast.php <file>
 */

fwrite(STDERR, "Warning: parse2data.php is deprecated. Use parse_ast.php instead.\n");

// Fallback: include and run parse_ast.php
require __DIR__ . '/parse_ast.php';
