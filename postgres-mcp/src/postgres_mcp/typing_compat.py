"""Compatibility module for typing features."""
import sys

if sys.version_info >= (3, 12):
    from typing import override
else:
    # Fallback for Python < 3.12
    def override(func):
        """Decorator to indicate that a method overrides a parent method."""
        return func