"""Typed application errors mapped to HTTP status codes by the handlers in main.py."""


class AppError(Exception):
    """Base for expected, client-facing errors."""

    status_code = 400

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code


class AIServiceError(AppError):
    """An AI provider (Groq / Replicate) is unconfigured or unavailable."""

    status_code = 503
