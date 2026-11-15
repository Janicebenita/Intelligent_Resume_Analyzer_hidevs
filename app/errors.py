"""Safe domain errors shared by CLI and HTTP boundaries."""


class AnalysisError(Exception):
    """A recoverable input or storage error with an actionable message."""

    def __init__(self, code: str, message: str, status: int = 422) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
