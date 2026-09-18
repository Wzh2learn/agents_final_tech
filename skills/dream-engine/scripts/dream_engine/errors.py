from __future__ import annotations


class DreamError(Exception):
    """Base error with human-readable message and fix suggestion."""

    def __init__(self, message: str, fix: str = ""):
        self.message = message
        self.fix = fix
        super().__init__(str(self))

    def __str__(self) -> str:
        s = f"❌ {self.message}"
        if self.fix:
            s += f"\n💡 修复：{self.fix}"
        return s


class IngestError(DreamError):
    pass


class GraphBuildError(DreamError):
    pass


class ActivationError(DreamError):
    pass
