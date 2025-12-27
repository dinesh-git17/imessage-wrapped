"""
Tests for iMessage Wrapped stats extractor.

Run with: pytest test_imessage_wrapped.py -v
"""

# pylint: disable=redefined-outer-name

import os
import sqlite3
import tempfile
from datetime import datetime

import pytest

from imessage_wrapped import (
    APPLE_EPOCH_OFFSET,
    DAYS_OF_WEEK,
    NANOSECONDS,
    IMessageStats,
    apple_to_datetime,
    format_datetime,
    get_date_filter,
)

# =============================================================================
# FIXTURES
# =============================================================================


def datetime_to_apple(dt: datetime) -> int:
    """Convert Python datetime to Apple timestamp (nanoseconds since 2001-01-01)."""
    return int((dt.timestamp() - APPLE_EPOCH_OFFSET) * NANOSECONDS)


@pytest.fixture
def test_db():
    """Create a temporary test database with sample iMessage data."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    conn = sqlite3.connect(path)
    cursor = conn.cursor()

    # Create tables matching iMessage schema
    cursor.execute("""
        CREATE TABLE handle (
            ROWID INTEGER PRIMARY KEY,
            id TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE message (
            ROWID INTEGER PRIMARY KEY,
            handle_id INTEGER,
            text TEXT,
            date INTEGER,
            is_from_me INTEGER,
            cache_has_attachments INTEGER DEFAULT 0,
            associated_message_type INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE attachment (
            ROWID INTEGER PRIMARY KEY,
            filename TEXT,
            mime_type TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE message_attachment_join (
            message_id INTEGER,
            attachment_id INTEGER
        )
    """)

    # Insert test handle
    cursor.execute("INSERT INTO handle (ROWID, id) VALUES (1, '+15551234567')")

    # Insert test messages for 2025
    test_messages = [
        # January messages
        (1, 1, "Happy New Year!", datetime_to_apple(datetime(2025, 1, 1, 0, 5)), 0),
        (
            2,
            1,
            "Happy New Year to you too!",
            datetime_to_apple(datetime(2025, 1, 1, 0, 6)),
            1,
        ),
        (3, 1, "I love you", datetime_to_apple(datetime(2025, 1, 1, 10, 0)), 1),
        (
            4,
            1,
            "I love you too baby",
            datetime_to_apple(datetime(2025, 1, 1, 10, 1)),
            0,
        ),
        (5, 1, "haha that's funny", datetime_to_apple(datetime(2025, 1, 2, 14, 0)), 1),
        (6, 1, "lol I know right?", datetime_to_apple(datetime(2025, 1, 2, 14, 2)), 0),
        # February messages
        (7, 1, "Good morning babe", datetime_to_apple(datetime(2025, 2, 14, 8, 0)), 0),
        (
            8,
            1,
            "Good morning my love",
            datetime_to_apple(datetime(2025, 2, 14, 8, 5)),
            1,
        ),
        (
            9,
            1,
            "Happy Valentine's Day!",
            datetime_to_apple(datetime(2025, 2, 14, 9, 0)),
            1,
        ),
        (
            10,
            1,
            "Check this out https://example.com",
            datetime_to_apple(datetime(2025, 2, 14, 12, 0)),
            0,
        ),
        # Late night message
        (11, 1, "Can't sleep", datetime_to_apple(datetime(2025, 3, 1, 2, 30)), 1),
        (12, 1, "Me neither", datetime_to_apple(datetime(2025, 3, 1, 2, 35)), 0),
        # Question messages
        (
            13,
            1,
            "What are you doing?",
            datetime_to_apple(datetime(2025, 3, 15, 15, 0)),
            1,
        ),
        (
            14,
            1,
            "Nothing much, you?",
            datetime_to_apple(datetime(2025, 3, 15, 15, 5)),
            0,
        ),
        # ALL CAPS message
        (15, 1, "THIS IS AMAZING", datetime_to_apple(datetime(2025, 4, 1, 12, 0)), 1),
        # Double text
        (16, 1, "Hey", datetime_to_apple(datetime(2025, 4, 2, 10, 0)), 1),
        (17, 1, "Are you there?", datetime_to_apple(datetime(2025, 4, 2, 10, 5)), 1),
        (18, 1, "Sorry was busy", datetime_to_apple(datetime(2025, 4, 2, 11, 0)), 0),
        # Emoji message
        (19, 1, "Love this! 😂❤️", datetime_to_apple(datetime(2025, 5, 1, 14, 0)), 0),
        (20, 1, "Same! 🥰", datetime_to_apple(datetime(2025, 5, 1, 14, 5)), 1),
    ]

    cursor.executemany(
        "INSERT INTO message (ROWID, handle_id, text, date, is_from_me) VALUES (?, ?, ?, ?, ?)",
        test_messages,
    )

    # Insert a heart reaction
    cursor.execute(
        "INSERT INTO message (ROWID, handle_id, text, date, is_from_me, associated_message_type) "
        "VALUES (21, 1, NULL, ?, 0, 2000)",
        (datetime_to_apple(datetime(2025, 5, 1, 14, 6)),),
    )

    # Insert attachment
    cursor.execute(
        "INSERT INTO attachment (ROWID, filename, mime_type) VALUES (1, 'voice.caf', 'audio/x-caf')"
    )
    cursor.execute("INSERT INTO message_attachment_join (message_id, attachment_id) VALUES (19, 1)")
    cursor.execute("UPDATE message SET cache_has_attachments = 1 WHERE ROWID = 19")

    conn.commit()
    conn.close()

    yield path

    # Cleanup
    os.unlink(path)


@pytest.fixture
def stats(test_db):
    """Create an IMessageStats instance with the test database."""
    s = IMessageStats(test_db, "5551234567", 2025)
    yield s
    s.close()


# =============================================================================
# HELPER FUNCTION TESTS
# =============================================================================


class TestHelperFunctions:
    """Tests for standalone helper functions."""

    def test_get_date_filter_returns_tuple(self):
        """get_date_filter should return a tuple of two integers."""
        start, end = get_date_filter(2025)
        assert isinstance(start, int)
        assert isinstance(end, int)
        assert start < end

    def test_get_date_filter_year_boundaries(self):
        """get_date_filter should return correct year boundaries."""
        start, end = get_date_filter(2025)

        # Convert back to datetime to verify
        start_dt = apple_to_datetime(start)
        end_dt = apple_to_datetime(end)

        assert start_dt.year == 2025
        assert start_dt.month == 1
        assert start_dt.day == 1

        assert end_dt.year == 2026
        assert end_dt.month == 1
        assert end_dt.day == 1

    def test_apple_to_datetime_conversion(self):
        """apple_to_datetime should correctly convert Apple timestamps."""
        # Known timestamp: January 1, 2025, 00:00:00 UTC
        dt = datetime(2025, 1, 1, 0, 0, 0)
        apple_ts = datetime_to_apple(dt)

        result = apple_to_datetime(apple_ts)

        assert result.year == 2025
        assert result.month == 1
        assert result.day == 1

    def test_format_datetime_output(self):
        """format_datetime should return properly formatted string."""
        dt = datetime(2025, 3, 15, 14, 30, 0)
        result = format_datetime(dt)

        assert "Mar 15, 2025" in result
        assert "2:30 PM" in result


# =============================================================================
# IMESSAGESTATS CLASS TESTS
# =============================================================================


class TestIMessageStatsBasics:
    """Tests for basic IMessageStats functionality."""

    def test_init_creates_connection(self, stats):
        """IMessageStats should create a database connection."""
        assert stats.conn is not None
        assert stats.cursor is not None

    def test_init_sets_date_range(self, stats):
        """IMessageStats should set correct date range for the year."""
        assert stats.date_start < stats.date_end
        assert stats.year == 2025

    def test_close_closes_connection(self, test_db):
        """close() should close the database connection."""
        s = IMessageStats(test_db, "5551234567", 2025)
        s.close()
        with pytest.raises(sqlite3.ProgrammingError):
            s.cursor.execute("SELECT 1")


class TestMessageCounts:
    """Tests for message counting methods."""

    def test_get_total_messages(self, stats):
        """get_total_messages should return correct counts."""
        result = stats.get_total_messages()

        assert "total" in result
        assert "you" in result
        assert "them" in result
        assert result["total"] == result["you"] + result["them"]
        assert result["total"] == 21  # 20 regular messages + 1 reaction

    def test_get_messages_by_month(self, stats):
        """get_messages_by_month should return monthly breakdown."""
        result = stats.get_messages_by_month()

        assert isinstance(result, list)
        assert len(result) > 0

        # Check structure
        for month_data in result:
            assert "month" in month_data
            assert "you" in month_data
            assert "them" in month_data

    def test_get_busiest_days_of_week(self, stats):
        """get_busiest_days_of_week should return day breakdown."""
        result = stats.get_busiest_days_of_week()

        assert isinstance(result, list)

        for day_data in result:
            assert day_data["day"] in DAYS_OF_WEEK
            assert isinstance(day_data["count"], int)

    def test_get_peak_hours(self, stats):
        """get_peak_hours should return top 5 hours."""
        result = stats.get_peak_hours()

        assert isinstance(result, list)
        assert len(result) <= 5

        for hour_data in result:
            assert "hour" in hour_data
            assert "count" in hour_data
            assert "AM" in hour_data["hour"] or "PM" in hour_data["hour"]


class TestLoveStats:
    """Tests for love and affection statistics."""

    def test_get_i_love_you_count(self, stats):
        """get_i_love_you_count should find 'I love you' messages."""
        result = stats.get_i_love_you_count()

        assert result["total"] == 2  # Two "I love you" messages in test data
        assert result["you"] == 1
        assert result["them"] == 1

    def test_get_word_phrase_count_baby(self, stats):
        """get_word_phrase_count should find 'baby' messages."""
        result = stats.get_word_phrase_count("baby")

        assert result["them"] >= 1  # "I love you too baby"

    def test_get_word_phrase_count_babe(self, stats):
        """get_word_phrase_count should find 'babe' messages."""
        result = stats.get_word_phrase_count("babe")

        assert result["them"] >= 1  # "Good morning babe"

    def test_get_heart_reactions(self, stats):
        """get_heart_reactions should count heart reactions."""
        result = stats.get_heart_reactions()

        assert "you" in result
        assert "them" in result
        assert result["them"] == 1  # One heart reaction in test data


class TestPatternStats:
    """Tests for conversation pattern statistics."""

    def test_get_double_texts(self, stats):
        """get_double_texts should count consecutive messages."""
        result = stats.get_double_texts()

        assert "you" in result
        assert "them" in result
        assert result["you"] >= 1  # "Hey" followed by "Are you there?"

    def test_get_response_times(self, stats):
        """get_response_times should calculate average response times."""
        result = stats.get_response_times()

        assert "you" in result
        assert "them" in result
        assert isinstance(result["you"], float)
        assert isinstance(result["them"], float)

    def test_get_longest_silence(self, stats):
        """get_longest_silence should find the longest gap."""
        result = stats.get_longest_silence()

        assert "start" in result
        assert "end" in result
        assert "hours" in result
        assert result["hours"] > 0


class TestMediaStats:
    """Tests for media and attachment statistics."""

    def test_get_attachments(self, stats):
        """get_attachments should count messages with attachments."""
        result = stats.get_attachments()

        assert result["total"] >= 1  # One attachment in test data

    def test_get_links(self, stats):
        """get_links should count messages with URLs."""
        result = stats.get_links()

        assert result["them"] >= 1  # "Check this out https://example.com"

    def test_get_reactions(self, stats):
        """get_reactions should return reaction breakdown."""
        result = stats.get_reactions()

        assert isinstance(result, list)
        # Should have at least one reaction type
        if len(result) > 0:
            assert "type" in result[0]
            assert "you" in result[0]
            assert "them" in result[0]


class TestWordStats:
    """Tests for word and phrase statistics."""

    def test_get_questions(self, stats):
        """get_questions should count messages with question marks."""
        result = stats.get_questions()

        assert result["you"] >= 1  # "What are you doing?"
        assert result["them"] >= 1  # "Nothing much, you?"

    def test_get_all_caps(self, stats):
        """get_all_caps should count ALL CAPS messages."""
        result = stats.get_all_caps()

        assert result["you"] >= 1  # "THIS IS AMAZING"

    def test_haha_count(self, stats):
        """get_word_phrase_count should find 'haha' messages."""
        result = stats.get_word_phrase_count("haha")

        assert result["you"] >= 1  # "haha that's funny"

    def test_lol_count(self, stats):
        """get_word_phrase_count should find 'lol' messages."""
        result = stats.get_word_phrase_count("lol")

        assert result["them"] >= 1  # "lol I know right?"


class TestLateNightStats:
    """Tests for late night messaging statistics."""

    def test_get_late_night_messages(self, stats):
        """get_late_night_messages should count messages between midnight and 4 AM."""
        result = stats.get_late_night_messages()

        assert "total" in result
        assert "you" in result
        assert "them" in result
        assert result["total"] >= 2  # Two late night messages in test data

    def test_get_morning_first(self, stats):
        """get_morning_first should track who texts first in the morning."""
        result = stats.get_morning_first()

        assert "you" in result
        assert "them" in result

    def test_get_goodnight_last(self, stats):
        """get_goodnight_last should track who texts last at night."""
        result = stats.get_goodnight_last()

        assert "you" in result
        assert "them" in result


class TestFirstLastMessages:
    """Tests for first and last message retrieval."""

    def test_get_first_last_message(self, stats):
        """get_first_last_message should return first and last messages."""
        result = stats.get_first_last_message()

        assert "first" in result
        assert "last" in result

        assert "date" in result["first"]
        assert "sender" in result["first"]
        assert "text" in result["first"]

        assert result["first"]["text"] == "Happy New Year!"

    def test_get_busiest_single_days(self, stats):
        """get_busiest_single_days should return top days by message count."""
        result = stats.get_busiest_single_days(limit=3)

        assert isinstance(result, list)
        assert len(result) <= 3

        for day_data in result:
            assert "date" in day_data
            assert "count" in day_data


class TestTopEmojis:
    """Tests for emoji statistics."""

    def test_get_top_emojis(self, stats):
        """get_top_emojis should return most used emojis."""
        result = stats.get_top_emojis(limit=10)

        assert isinstance(result, list)

        for emoji_data in result:
            assert "emoji" in emoji_data
            assert "count" in emoji_data

    def test_get_emoji_count(self, stats):
        """get_emoji_count should count specific emoji usage."""
        result = stats.get_emoji_count("❤️")

        assert "you" in result
        assert "them" in result


class TestGetAllStats:
    """Tests for the comprehensive get_all_stats method."""

    def test_get_all_stats_returns_complete_structure(self, stats):
        """get_all_stats should return all expected sections."""
        result = stats.get_all_stats()

        expected_sections = [
            "meta",
            "classics",
            "love",
            "patterns",
            "media",
            "wordStats",
            "milestones",
            "lateNight",
        ]

        for section in expected_sections:
            assert section in result, f"Missing section: {section}"

    def test_get_all_stats_meta(self, stats):
        """get_all_stats meta section should have correct fields."""
        result = stats.get_all_stats()

        assert result["meta"]["year"] == 2025
        assert "generatedAt" in result["meta"]
        assert "daysTexting" in result["meta"]

    def test_get_all_stats_classics(self, stats):
        """get_all_stats classics section should have message counts."""
        result = stats.get_all_stats()

        classics = result["classics"]
        assert classics["totalMessages"] > 0
        assert "youSent" in classics
        assert "themSent" in classics
        assert "avgPerDay" in classics


# =============================================================================
# EDGE CASE TESTS
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_database(self):
        """Stats should handle empty database gracefully."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

        conn = sqlite3.connect(path)
        cursor = conn.cursor()

        cursor.execute("CREATE TABLE handle (ROWID INTEGER PRIMARY KEY, id TEXT)")
        cursor.execute("""
            CREATE TABLE message (
                ROWID INTEGER PRIMARY KEY,
                handle_id INTEGER,
                text TEXT,
                date INTEGER,
                is_from_me INTEGER,
                cache_has_attachments INTEGER DEFAULT 0,
                associated_message_type INTEGER DEFAULT 0
            )
        """)
        cursor.execute("INSERT INTO handle (ROWID, id) VALUES (1, '+15559999999')")
        conn.commit()
        conn.close()

        try:
            s = IMessageStats(path, "5559999999", 2025)
            result = s.get_total_messages()
            assert result["total"] == 0
            s.close()
        finally:
            os.unlink(path)

    def test_nonexistent_contact(self, test_db):
        """Stats should handle nonexistent contact gracefully."""
        s = IMessageStats(test_db, "0000000000", 2025)
        result = s.get_total_messages()
        assert result["total"] == 0
        s.close()

    def test_wrong_year(self, test_db):
        """Stats should return zero for years with no messages."""
        s = IMessageStats(test_db, "5551234567", 2020)
        result = s.get_total_messages()
        assert result["total"] == 0
        s.close()


# =============================================================================
# MAIN
# =============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
