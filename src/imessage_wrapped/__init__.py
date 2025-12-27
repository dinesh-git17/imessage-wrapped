"""
iMessage Wrapped - Extract iMessage statistics for your year in review.

A Python CLI tool for analyzing iMessage conversations and generating
comprehensive statistics from the macOS chat.db database.
"""

from .imessage_wrapped import (
    APPLE_EPOCH_OFFSET,
    DAYS_OF_WEEK,
    MONTHS,
    NANOSECONDS,
    REACTION_TYPES,
    IMessageStats,
    apple_to_datetime,
    format_datetime,
    get_date_filter,
    main,
)

__version__ = "1.0.0"
__all__ = [
    "APPLE_EPOCH_OFFSET",
    "NANOSECONDS",
    "REACTION_TYPES",
    "DAYS_OF_WEEK",
    "MONTHS",
    "get_date_filter",
    "apple_to_datetime",
    "format_datetime",
    "IMessageStats",
    "main",
]
