"""AST traversal and symbol/call extraction."""

import logging
from pathlib import Path
from typing import Any, Optional

from .models import Call, CallKind, FileAnalysis, Symbol, SymbolKind, Visibility

logger = logging.getLogger(__name__)


class ASTVisitor:
    """Traverse PHP AST and extract symbols and calls."""

    def __init__(self, source_file: Path, ast_data: dict[str, Any]):
        """Initialize the visitor.

        Args:
            source_file: Path to the source PHP file
            ast_data: The AST data from the parser
        """
        self.source_file = Path(source_file).resolve()
        self.ast_data = ast_data
        self.current_namespace: str = ""
        self.current_class: Optional[str] = None
        self.current_function: Optional[str] = None
        self.symbols: list[Symbol] = []
        self.calls: list[Call] = []
        self.errors: list[str] = []

    def visit(self) -> FileAnalysis:
        """Visit the AST and extract symbols and calls.

        Returns:
            FileAnalysis containing extracted symbols and calls
        """
        try:
            self._visit_node(self.ast_data)
        except Exception as e:
            logger.warning(f"Error visiting AST in {self.source_file}: {e}")
            self.errors.append(str(e))

        return FileAnalysis(
            path=self.source_file,
            symbols=self.symbols,
            calls=self.calls,
            parse_errors=self.errors,
            success=len(self.errors) == 0,
        )

    def _visit_node(self, node: Any) -> None:
        """Visit a single AST node.

        Args:
            node: The AST node to visit
        """
        if isinstance(node, dict):
            if len(node) == 1:
                kind, data = next(iter(node.items()))
                self._dispatch(kind, data)
            else:
                for value in node.values():
                    self._visit_node(value)
        elif isinstance(node, list):
            for item in node:
                self._visit_node(item)

    def _dispatch(self, kind: str, data: Any) -> None:
        """Dispatch to handler based on AST node kind.

        Args:
            kind: The AST node kind
            data: The node data
        """
        handlers = {
            "AST_NAMESPACE": self._handle_namespace,
            "AST_CLASS": self._handle_class,
            "AST_FUNC_DECL": self._handle_function,
            "AST_METHOD": self._handle_method,
            "AST_CALL": self._handle_call,
            "AST_METHOD_CALL": self._handle_method_call,
            "AST_STATIC_CALL": self._handle_static_call,
            "AST_NEW": self._handle_new,
        }

        handler = handlers.get(kind)
        if handler:
            try:
                handler(data)
            except Exception as e:
                logger.debug(f"Error in handler for {kind}: {e}")
                self.errors.append(f"Handler error for {kind}: {e}")
        else:
            self._visit_node(data)

    def _handle_namespace(self, data: Any) -> None:
        """Handle namespace declaration."""
        if isinstance(data, dict) and "name" in data:
            name = data["name"]
            if isinstance(name, str):
                self.current_namespace = name.strip('"')
        self._visit_node(data)

    def _handle_class(self, data: Any) -> None:
        """Handle class declaration."""
        if not isinstance(data, dict):
            return

        name = data.get("name")
        if not name:
            return

        class_name = self._clean_string(name)
        qualified_name = self._qualify_name(class_name)

        self.symbols.append(
            Symbol(
                name=class_name,
                qualified_name=qualified_name,
                kind=SymbolKind.CLASS,
                visibility=Visibility.UNKNOWN,
                file=self.source_file,
            )
        )

        prev_class = self.current_class
        self.current_class = qualified_name
        self._visit_node(data)
        self.current_class = prev_class

    def _handle_function(self, data: Any) -> None:
        """Handle global function declaration."""
        if not isinstance(data, dict):
            return

        name = data.get("name")
        if not name:
            return

        func_name = self._clean_string(name)
        qualified_name = self._qualify_name(func_name)

        self.symbols.append(
            Symbol(
                name=func_name,
                qualified_name=qualified_name,
                kind=SymbolKind.FUNCTION,
                visibility=Visibility.PUBLIC,
                file=self.source_file,
            )
        )

        prev_func = self.current_function
        self.current_function = qualified_name
        self._visit_node(data)
        self.current_function = prev_func

    def _handle_method(self, data: Any) -> None:
        """Handle method declaration."""
        if not isinstance(data, dict):
            return

        name = data.get("name")
        if not name:
            return

        method_name = self._clean_string(name)
        visibility = self._extract_visibility(data)

        if self.current_class:
            qualified_name = f"{self.current_class}::{method_name}"
        else:
            qualified_name = self._qualify_name(method_name)

        self.symbols.append(
            Symbol(
                name=method_name,
                qualified_name=qualified_name,
                kind=SymbolKind.METHOD,
                visibility=visibility,
                file=self.source_file,
            )
        )

        prev_func = self.current_function
        self.current_function = qualified_name
        self._visit_node(data)
        self.current_function = prev_func

    def _handle_call(self, data: Any) -> None:
        """Handle function call."""
        if not isinstance(data, dict):
            return

        expr = data.get("expr")
        if not expr or not isinstance(expr, dict):
            self._visit_node(data)
            return

        if "AST_NAME" in expr:
            name_data = expr["AST_NAME"]
            if isinstance(name_data, dict):
                func_name = name_data.get("name")
                if func_name:
                    callee = self._clean_string(func_name)
                    if self.current_function:
                        self.calls.append(
                            Call(
                                caller=self.current_function,
                                callee=callee,
                                kind=CallKind.FUNCTION,
                                file=self.source_file,
                            )
                        )

        self._visit_node(data)

    def _handle_method_call(self, data: Any) -> None:
        """Handle method call."""
        if not isinstance(data, dict):
            return

        method = data.get("method")
        if not method:
            self._visit_node(data)
            return

        method_name = self._clean_string(method)
        if self.current_function:
            self.calls.append(
                Call(
                    caller=self.current_function,
                    callee=method_name,
                    kind=CallKind.METHOD,
                    file=self.source_file,
                )
            )

        self._visit_node(data)

    def _handle_static_call(self, data: Any) -> None:
        """Handle static method call."""
        if not isinstance(data, dict):
            return

        class_node = data.get("class")
        method = data.get("method")

        if not class_node or not method:
            self._visit_node(data)
            return

        class_name = self._extract_name_from_node(class_node)
        method_name = self._clean_string(method)

        if class_name and self.current_function:
            callee = f"{class_name}::{method_name}"
            self.calls.append(
                Call(
                    caller=self.current_function,
                    callee=callee,
                    kind=CallKind.STATIC,
                    file=self.source_file,
                )
            )

        self._visit_node(data)

    def _handle_new(self, data: Any) -> None:
        """Handle object instantiation."""
        if not isinstance(data, dict):
            return

        expr = data.get("expr")
        if expr and isinstance(expr, dict) and "AST_NEW" in expr:
            new_node = expr["AST_NEW"]
            if isinstance(new_node, dict):
                class_node = new_node.get("class")
                if class_node:
                    class_name = self._extract_name_from_node(class_node)
                    if class_name and self.current_function:
                        self.calls.append(
                            Call(
                                caller=self.current_function,
                                callee=class_name,
                                kind=CallKind.CONSTRUCTOR,
                                file=self.source_file,
                            )
                        )

        self._visit_node(data)

    def _clean_string(self, value: Any) -> str:
        """Clean a string value from the AST."""
        if isinstance(value, str):
            return value.strip('"')
        return str(value)

    def _extract_name_from_node(self, node: Any) -> Optional[str]:
        """Extract a name from a name node."""
        if isinstance(node, dict):
            if "AST_NAME" in node:
                name_data = node["AST_NAME"]
                if isinstance(name_data, dict) and "name" in name_data:
                    return self._clean_string(name_data["name"])
        return None

    def _extract_visibility(self, data: dict[str, Any]) -> Visibility:
        """Extract visibility modifier from method data."""
        flags = data.get("flags")
        if not flags:
            return Visibility.UNKNOWN

        flags_str = str(flags).upper()
        if "PRIVATE" in flags_str:
            return Visibility.PRIVATE
        elif "PROTECTED" in flags_str:
            return Visibility.PROTECTED
        elif "PUBLIC" in flags_str:
            return Visibility.PUBLIC

        return Visibility.UNKNOWN

    def _qualify_name(self, name: str) -> str:
        """Qualify a name with namespace if present."""
        if self.current_namespace:
            return f"{self.current_namespace}\\{name}"
        return name
