# iMessage Wrapped

A Python tool for extracting comprehensive messaging statistics from the macOS iMessage database. Generate a "year in review" analysis of your conversations with detailed metrics on message patterns, reactions, media sharing, and more.

## Table of Contents

- [Overview](#overview)
- [Requirements](#requirements)
- [Installation](#installation)
- [Database Access](#database-access)
- [Usage](#usage)
- [Output Format](#output-format)
- [SQL Reference](#sql-reference)
- [Database Schema](#database-schema)
- [Troubleshooting](#troubleshooting)
- [Privacy and Security](#privacy-and-security)
- [License](#license)

## Overview

iMessage Wrapped analyzes your iMessage conversation history and generates a JSON file containing statistics including:

- Total message counts (sent vs. received)
- Monthly and daily messaging patterns
- Peak texting hours and busiest days
- "I love you" counts and love emoji usage
- Pet name frequency (baby, babe, my love)
- Reaction statistics (hearts, likes, laughs)
- Media and attachment counts
- Voice memo and link sharing stats
- Response time analysis
- Double/triple text frequency
- Late night messaging patterns
- Message milestones (10k, 50k, 100k, etc.)

## Requirements

- macOS 10.15 or later
- Python 3.8 or later
- Access to iMessage database (`chat.db`)
- Full Disk Access permission for Terminal (if reading directly from Messages)

### Python Dependencies

This script uses only Python standard library modules:

- `sqlite3`
- `json`
- `re`
- `argparse`
- `collections`
- `datetime`
- `pathlib`

No external packages are required.

## Installation

### Option 1: Install from PyPI (recommended)

```bash
pip install imessage-year-wrapped
```

### Option 2: Install from GitHub

```bash
pip install git+https://github.com/dinesh-git17/imessage-wrapped.git
```

### Option 3: Install from source

```bash
git clone https://github.com/dinesh-git17/imessage-wrapped.git
cd imessage-wrapped
pip install .
```

### Development installation

```bash
git clone https://github.com/dinesh-git17/imessage-wrapped.git
cd imessage-wrapped
pip install -e ".[dev]"  # Includes pytest, pylint, ruff
```

## Database Access

The iMessage database is located at `~/Library/Messages/chat.db`. There are two methods to access it:

### Method 1: Copy the Database (Recommended)

The Messages app locks the database while running. Copy it to a working location:

```bash
# Quit Messages.app first, then:
cp ~/Library/Messages/chat.db ~/Desktop/chat.db
```

### Method 2: Direct Access with Full Disk Access

1. Open System Preferences > Security & Privacy > Privacy
2. Select "Full Disk Access" from the sidebar
3. Click the lock icon and authenticate
4. Add Terminal.app (or your terminal emulator) to the list
5. Restart Terminal

### Accessing iPhone Messages via Backup

To analyze iPhone messages not synced to your Mac:

1. Connect your iPhone and create a local backup using Finder
2. Locate the backup at:
   ```
   ~/Library/Application Support/MobileSync/Backup/<DEVICE_ID>/
   ```
3. The messages database is stored with a hashed filename:
   ```
   3d/3d0d7e5fb2ce288813306e4d4636395e047a3d28
   ```
4. Copy this file and rename it to `chat.db`

## Usage

### Basic Usage

```bash
imessage-wrapped --phone <PHONE_NUMBER> --year <YEAR> --db <PATH_TO_DB>
```

### Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--phone` | Yes | N/A | Contact's phone number (digits only, e.g., `5551234567`) |
| `--year` | No | Current year | Year to analyze |
| `--db` | No | `~/Library/Messages/chat.db` | Path to chat.db file |
| `--output`, `-o` | No | `imessage_wrapped.json` | Output JSON file path |

### Examples

Analyze 2025 messages with a contact:

```bash
imessage-wrapped --phone 5551234567 --year 2025 --db ~/Desktop/chat.db
```

Specify a custom output file:

```bash
imessage-wrapped --phone 5551234567 --year 2025 --output stats_2025.json
```

Analyze the current year using the default database location:

```bash
imessage-wrapped --phone 5551234567
```

### Finding a Contact's Phone Number

To find the exact format of a phone number in the database:

```bash
sqlite3 ~/Desktop/chat.db "SELECT ROWID, id FROM handle WHERE id LIKE '%555%';"
```

Phone numbers may be stored with or without country codes. Try variations if your initial query returns no results.

## Output Format

The script generates a JSON file with the following structure:

```json
{
  "meta": {
    "year": 2025,
    "generatedAt": "2025-12-27T10:30:00.000000",
    "daysTexting": 342
  },
  "classics": {
    "totalMessages": 45000,
    "youSent": 22000,
    "themSent": 23000,
    "avgPerDay": 131,
    "byMonth": [...],
    "busiestDays": [...],
    "peakHours": [...],
    "busiestSingleDays": [...],
    "first": {...},
    "last": {...}
  },
  "love": {
    "iLoveYou": {"you": 150, "them": 175, "total": 325},
    "heartReactions": {"you": 500, "them": 450},
    "emojis": [...],
    "petNames": [...]
  },
  "patterns": {
    "avgResponseTime": {"you": 3.5, "them": 4.2},
    "doubleTexts": {"you": 1200, "them": 800},
    "longestSilence": {...}
  },
  "media": {
    "attachments": {"you": 300, "them": 250, "total": 550},
    "voiceMemos": {"you": 45, "them": 30},
    "links": {"you": 120, "them": 80},
    "reactions": [...]
  },
  "wordStats": {
    "laughing": [...],
    "questions": {"you": 2000, "them": 1800},
    "allCaps": {"you": 150, "them": 100},
    "topEmojis": [...]
  },
  "milestones": [...],
  "lateNight": {
    "total": 500,
    "you": 280,
    "them": 220,
    "morningFirst": {"you": 180, "them": 162},
    "goodnightLast": {"you": 175, "them": 167}
  }
}
```

### Field Descriptions

#### meta
- `year`: The year analyzed
- `generatedAt`: ISO 8601 timestamp of when the analysis was run
- `daysTexting`: Number of unique days with at least one message

#### classics
- `totalMessages`: Combined message count for both parties
- `youSent` / `themSent`: Individual message counts
- `avgPerDay`: Average messages per day (total / daysTexting)
- `byMonth`: Array of monthly breakdowns with `month`, `you`, `them` fields
- `busiestDays`: Days of week ranked by message count
- `peakHours`: Top 5 busiest hours (12-hour format)
- `busiestSingleDays`: Top 5 individual dates by message count
- `first` / `last`: First and last messages of the year with date, sender, and text preview

#### love
- `iLoveYou`: Count of messages containing "i love you" (case-insensitive)
- `heartReactions`: iMessage heart reactions given by each party
- `emojis`: Counts for specific love-related emojis
- `petNames`: Counts for terms of endearment (baby, babe, my love)

#### patterns
- `avgResponseTime`: Average response time in minutes (for responses under 60 minutes)
- `doubleTexts`: Count of consecutive messages from the same sender
- `longestSilence`: Longest gap between messages with start time, end time, and duration in hours

#### media
- `attachments`: Messages containing any attachment
- `voiceMemos`: Audio messages (`.caf`, `.m4a` files)
- `links`: Messages containing HTTP/HTTPS URLs
- `reactions`: Breakdown by reaction type (love, like, dislike, laugh, emphasis, question)

#### wordStats
- `laughing`: Counts for "haha", "lol", and the laughing emoji
- `questions`: Messages containing question marks
- `allCaps`: Messages in all capital letters (minimum 6 characters)
- `topEmojis`: 15 most frequently used emojis

#### milestones
Array of message count milestones (10k, 25k, 50k, etc.) with the date each was reached

#### lateNight
- `total` / `you` / `them`: Messages sent between midnight and 4 AM
- `morningFirst`: Who sends the first message of the day (5 AM to noon) more often
- `goodnightLast`: Who sends the last message of the night (9 PM to 5 AM) more often

## SQL Reference

The repository includes `imessage-wrapped-sql-reference.md`, a comprehensive guide containing:

- Raw SQL queries for each statistic
- Date conversion formulas for Apple timestamps
- Table schema documentation
- Query examples for custom analysis

Use this reference to run individual queries or extend the analysis.

## Database Schema

### Key Tables

| Table | Description |
|-------|-------------|
| `message` | All messages with text, timestamps, and sender info |
| `handle` | Contact identifiers (phone numbers, emails) |
| `chat` | Chat/conversation metadata |
| `chat_message_join` | Links messages to chats |
| `attachment` | Attachment metadata (photos, videos, files) |
| `message_attachment_join` | Links messages to attachments |

### Important Columns

| Column | Table | Description |
|--------|-------|-------------|
| `text` | message | Message content |
| `date` | message | Apple timestamp (nanoseconds since 2001-01-01) |
| `is_from_me` | message | 1 if sent by you, 0 if received |
| `cache_has_attachments` | message | 1 if message has attachments |
| `associated_message_type` | message | Reaction type (2000-2005) |
| `id` | handle | Phone number or email address |

### Apple Timestamp Conversion

Apple stores dates as nanoseconds since January 1, 2001. To convert:

```sql
-- To readable datetime
datetime(message.date/1000000000 + 978307200, 'unixepoch', 'localtime')

-- To filter by year
WHERE message.date >= strftime('%s', '2025-01-01') * 1000000000 - 978307200000000000
  AND message.date < strftime('%s', '2026-01-01') * 1000000000 - 978307200000000000
```

### Reaction Types

| Value | Reaction |
|-------|----------|
| 2000 | Loved (heart) |
| 2001 | Liked (thumbs up) |
| 2002 | Disliked (thumbs down) |
| 2003 | Laughed |
| 2004 | Emphasized (exclamation) |
| 2005 | Questioned |
| 3000-3005 | Removed reactions (corresponding to above) |

## Troubleshooting

### "Database not found" Error

Ensure the path to `chat.db` is correct. If using the default location, verify Messages.app has synced your messages.

```bash
ls -la ~/Library/Messages/chat.db
```

### "Database is locked" Error

Quit the Messages application before running the script, or copy the database to a different location.

### Permission Denied

Grant Full Disk Access to Terminal:

1. System Preferences > Security & Privacy > Privacy
2. Select "Full Disk Access"
3. Add Terminal.app

### No Messages Found for Contact

Verify the phone number format matches what is stored in the database:

```bash
sqlite3 ~/Desktop/chat.db "SELECT DISTINCT id FROM handle;"
```

Phone numbers may include country codes (`+1`) or be formatted differently than expected.

### Incorrect Message Counts

The script filters by year. Verify the date range is correct for your data:

```bash
sqlite3 ~/Desktop/chat.db "SELECT MIN(date), MAX(date) FROM message;"
```

Convert the returned timestamps using the formula in the Database Schema section.

## Privacy and Security

This tool operates entirely locally. No data is transmitted externally.

### Recommendations

- Do not commit `chat.db` or output JSON files to version control
- Delete copied database files after analysis
- Store output files securely if they contain sensitive conversation data
- Add `*.json` and `chat.db` to your `.gitignore`

### Data Handling

The script reads from the database in read-only mode. No modifications are made to the original iMessage database.

## License

MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
