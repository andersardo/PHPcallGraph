"""Data models for call graph analysis."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Literal, Optional


class SymbolKind(str, Enum):
    """Type of symbol."""

    FUNCTION = "function"
    METHOD = "method"
    CLASS = "class"


class CallKind(str, Enum):
    """Type of function/method call."""

    FUNCTION = "function"
    METHOD = "method"
    STATIC = "static"
    CONSTRUCTOR = "constructor"
    UNKNOWN = "unknown"


class Visibility(str, Enum):
    """Symbol visibility modifier."""

    PUBLIC = "public"
    PRIVATE = "private"
    PROTECTED = "protected"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Symbol:
    """A defined function, method, or class."""

    name: str
    qualified_name: str
    kind: SymbolKind
    visibility: Visibility
    file: Path
    line: Optional[int] = None

    def __hash__(self) -> int:
        """Return hash of the symbol."""
        return hash(self.qualified_name)


@dataclass(frozen=True)
class Call:
    """A function or method call."""

    caller: str
    callee: str
    kind: CallKind
    file: Path
    line: Optional[int] = None
    confidence: Literal["exact", "inferred", "ambiguous", "unknown"] = "exact"

    def __hash__(self) -> int:
        """Return hash of the call."""
        return hash((self.caller, self.callee, self.kind))


@dataclass
class FileAnalysis:
    """Results of analyzing a single PHP file."""

    path: Path
    symbols: list[Symbol] = field(default_factory=list)
    calls: list[Call] = field(default_factory=list)
    parse_errors: list[str] = field(default_factory=list)
    success: bool = True


@dataclass(frozen=True)
class GraphEdge:
    """An edge in the call graph."""

    source: str
    target: str
    kind: CallKind = CallKind.UNKNOWN

    def __hash__(self) -> int:
        """Return hash of the edge."""
        return hash((self.source, self.target, self.kind))


@dataclass
class CallGraph:
    """Call graph for the entire project."""

    nodes: set[str] = field(default_factory=set)
    edges: set[GraphEdge] = field(default_factory=set)
    symbols: dict[str, Symbol] = field(default_factory=dict)
    unresolved_calls: set[str] = field(default_factory=set)
    external_calls: set[str] = field(default_factory=set)
