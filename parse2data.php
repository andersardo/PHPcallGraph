<?php declare(strict_types=1);

use ast\flags;

const AST_DUMP_LINENOS = 1;
const AST_DUMP_EXCLUDE_DOC_COMMENT = 2;

function get_flag_info() : array {
    static $info;
    if ($info !== null) {
        return $info;
    }

    foreach (ast\get_metadata() as $data) {
        if (empty($data->flags)) {
            continue;
        }

        $flagMap = [];
        foreach ($data->flags as $fullName) {
            $shortName = substr($fullName, strrpos($fullName, '\\') + 1);
            $flagMap[constant($fullName)] = $shortName;
        }

        $info[(int) $data->flagsCombinable][$data->kind] = $flagMap;
    }

    return $info;
}
function is_combinable_flag(int $kind) : bool {
    return isset(get_flag_info()[1][$kind]);
}

function format_flags(int $kind, int $flags) : string {
    list($exclusive, $combinable) = get_flag_info();
    if (isset($exclusive[$kind])) {
        $flagInfo = $exclusive[$kind];
        if (isset($flagInfo[$flags])) {
            return "{$flagInfo[$flags]} ($flags)";
        }
    } else if (isset($combinable[$kind])) {
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

/** Dumps abstract syntax tree */
function ast_dump($ast, int $options = 0) : string {
    if ($ast instanceof ast\Node) {
        $result = ast\get_kind_name($ast->kind);

        if ($options & AST_DUMP_LINENOS) {
            $result .= " @ $ast->lineno";
            if (isset($ast->endLineno)) {
                $result .= "-$ast->endLineno";
            }
        }

        if ((ast\kind_uses_flags($ast->kind) && !is_combinable_flag($ast->kind)) || $ast->flags != 0) {
            $result .= "\n    flags: " . format_flags($ast->kind, $ast->flags);
        }
        foreach ($ast->children as $i => $child) {
            if (($options & AST_DUMP_EXCLUDE_DOC_COMMENT) && $i === 'docComment') {
                continue;
            }
            $result .= "\n    $i: " . str_replace("\n", "\n    ", ast_dump($child, $options));
        }
        return $result;
    } else if ($ast === null) {
        return 'null';
    } else if (is_string($ast)) {
        return "\"$ast\"";
    } else {
        return (string) $ast;
    }
}

function ast_struct($ast, int $options = 0) {
    if ($ast instanceof ast\Node) {
        $result = ast\get_kind_name($ast->kind);
	$skip = array('AST_PARAM', 'AST_PARAM_LIST', 'AST_RETURN', 'AST_PROP_DECL', 'AST_PROP_ELEM');
	if (in_array($result, $skip)) {
	   return 'null';
	}
        $res = array();
        if ($options & AST_DUMP_LINENOS) {
            $result .= " @ $ast->lineno";
            if (isset($ast->endLineno)) {
                $result .= "-$ast->endLineno";
            }
        }

        foreach ($ast->children as $i => $child) {
            if (($options & AST_DUMP_EXCLUDE_DOC_COMMENT) && $i === 'docComment') {
                continue;
            }
	    $res[$result][$i] = ast_struct($child, $options);
            if ((ast\kind_uses_flags($ast->kind) && !is_combinable_flag($ast->kind)) || $ast->flags != 0) {
	      $res[$result]['flags'] = format_flags($ast->kind, $ast->flags);
            }
        }
        return $res;
    } else if ($ast === null) {
        return 'null';
    } else if (is_string($ast)) {
        return "\"$ast\"";
    } else {
        return (string) $ast;
    }
}

$file = $argv[1];
$astTree = ast_struct(ast\parse_file($file, $version=85), AST_DUMP_EXCLUDE_DOC_COMMENT);
//$Tree = json_encode($astTree, JSON_PRETTY_PRINT);
$Tree = json_encode($astTree);
echo($Tree);
/*
AST_ARRAY_ELEM:           value, key
AST_ARROW_FUNC:           name, docComment, params, stmts, returnType, attributes // name removed in version 110
AST_ASSIGN:               var, expr
AST_ASSIGN_OP:            var, expr
AST_ASSIGN_REF:           var, expr
AST_ATTRIBUTE:            class, args            // php 8.0+ attributes (version 80+)
AST_BINARY_OP:            left, right
AST_BREAK:                depth
AST_CALL:                 expr, args
AST_CALLABLE_CONVERT:                            // php 8.1+ first-class callable syntax
AST_CAST:                 expr
AST_CATCH:                class, var, stmts
AST_CLASS:                name, docComment, extends, implements, stmts, (for enums) type
AST_CLASS_CONST:          class, const
AST_CLASS_CONST_GROUP     class, attributes, type // version 80+
AST_CLASS_NAME:           class                   // version 70+
AST_CLONE:                expr                    // prior to version 120
AST_CLOSURE:              name, docComment, params, uses, stmts, returnType, attributes // name removed in version 110
AST_CLOSURE_VAR:          name
AST_CONDITIONAL:          cond, true, false
AST_CONST:                name
AST_CONST_ELEM:           name, value, docComment
AST_CONTINUE:             depth
AST_DECLARE:              declares, stmts
AST_DIM:                  expr, dim
AST_DO_WHILE:             stmts, cond
AST_ECHO:                 expr
AST_EMPTY:                expr
AST_ENUM_CASE:            name, expr, docComment, attributes // php 8.1+ enums
AST_EXIT:                 expr                   // prior to version 120
AST_FOR:                  init, cond, loop, stmts
AST_FOREACH:              expr, value, key, stmts
AST_FUNC_DECL:            name, docComment, params, stmts, returnType, attributes
                          uses                   // prior to version 60
AST_GLOBAL:               var
AST_GOTO:                 label
AST_GROUP_USE:            prefix, uses
AST_HALT_COMPILER:        offset
AST_IF_ELEM:              cond, stmts
AST_INCLUDE_OR_EVAL:      expr
AST_INSTANCEOF:           expr, class
AST_ISSET:                var
AST_LABEL:                name
AST_MAGIC_CONST:
AST_MATCH:                cond, stmts            // php 8.0+ match
AST_MATCH_ARM:            cond, expr             // php 8.0+ match
AST_METHOD:               name, docComment, params, stmts, returnType, attributes
                          uses                   // prior to version 60
AST_METHOD_CALL:          expr, method, args
AST_METHOD_REFERENCE:     class, method
AST_NAME:                 name
AST_NAMED_ARG:            name, expr             // php 8.0 named parameters
AST_NAMESPACE:            name, stmts
AST_NEW:                  class, args
AST_NULLABLE_TYPE:        type                   // Used only since PHP 7.1
AST_NULLSAFE_METHOD_CALL: expr, method, args     // php 8.0 null safe operator
AST_NULLSAFE_PROP:        expr, prop             // php 8.0 null safe operator
AST_PARAM:                type, name, default, attributes, docComment, hooks // 'hooks' field added in version 110
AST_POST_DEC:             var
AST_POST_INC:             var
AST_PRE_DEC:              var
AST_PRE_INC:              var
AST_PRINT:                expr
AST_PROP:                 expr, prop
AST_PROP_ELEM:            name, default, docComment, hooks // 'hooks' field added in version 110
AST_PROP_GROUP:           type, props, attributes // version 70+
AST_PROPERTY_HOOK:        name, docComment, params, stmts, attributes // version 110+
AST_PROPERTY_HOOK_SHORT_BODY: expr
AST_REF:                  var                    // only used in foreach ($a as &$v)
AST_RETURN:               expr
AST_SHELL_EXEC:           expr
AST_STATIC:               var, default
AST_STATIC_CALL:          class, method, args
AST_STATIC_PROP:          class, prop
AST_SWITCH:               cond, stmts
AST_SWITCH_CASE:          cond, stmts
AST_THROW:                expr
AST_TRAIT_ALIAS:          method, alias
AST_TRAIT_PRECEDENCE:     method, insteadof
AST_TRY:                  try, catches, finally
AST_TYPE:
AST_UNARY_OP:             expr
AST_UNPACK:               expr
AST_UNSET:                var
AST_USE_ELEM:             name, alias
AST_USE_TRAIT:            traits, adaptations
AST_VAR:                  name
AST_WHILE:                cond, stmts
AST_YIELD:                value, key
AST_YIELD_FROM:           expr

// List nodes (numerically indexed children):
AST_ARG_LIST
AST_ARRAY
AST_ATTRIBUTE_LIST        // php 8.0+ attributes (version 80+)
AST_ATTRIBUTE_GROUP       // php 8.0+ attributes (version 80+)
AST_CATCH_LIST
AST_CLASS_CONST_DECL
AST_CLOSURE_USES
AST_CONST_DECL
AST_ENCAPS_LIST           // interpolated string: "foo$bar"
AST_EXPR_LIST
AST_IF
AST_LIST
AST_MATCH_ARM_LIST        // php 8.0+ match
AST_NAME_LIST
AST_PARAM_LIST
AST_PROP_DECL
AST_STMT_LIST
AST_SWITCH_LIST
AST_TRAIT_ADAPTATIONS
AST_USE
AST_TYPE_UNION            // php 8.0+ union types
AST_TYPE_INTERSECTION     // php 8.1+ intersection types
*/
?>
