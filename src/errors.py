"""Custom exception types."""


class PHPcallGraphError(Exception):
    """Base exception for all PHPcallGraph errors."""

    pass


class PHPParserError(PHPcallGraphError):
    """Error running the PHP parser."""

    pass


class ConfigError(PHPcallGraphError):
    """Invalid configuration."""

    pass


class AnalysisError(PHPcallGraphError):
    """Error during code analysis."""

    pass
