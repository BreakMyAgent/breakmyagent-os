class UpstreamServiceError(Exception):
    """Base class for upstream service failures."""


class TargetModelError(UpstreamServiceError):
    """Raised when the target model call fails."""


class JudgeModelError(UpstreamServiceError):
    """Raised when the judge model call or output parsing fails."""


class TelemetryError(Exception):
    """Raised when telemetry persistence fails."""
