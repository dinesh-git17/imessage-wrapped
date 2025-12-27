# iMessage Wrapped — SQL Query Reference

**Purpose:** Complete SQL query reference for extracting iMessage statistics from `chat.db`
**Database:** macOS iMessage database (`~/Library/Messages/chat.db`)
**Target Contact:** Replace `YOUR_PHONE_NUMBER` with your contact's phone number (e.g., `5551234567`)
**Date Range:** Adjust year as needed (examples use 2025)

---

## Table of Contents

1. [Database Setup](#1-database-setup)
2. [The Classics](#2-the-classics)
3. [Love & Affection](#3-love--affection)
4. [Conversation Patterns](#4-conversation-patterns)
5. [Media & Attachments](#5-media--attachments)
6. [Reactions](#6-reactions)
7. [Word Stats](#7-word-stats)
8. [Milestones](#8-milestones)
9. [Late Night Stats](#9-late-night-stats)
10. [Helper Functions](#10-helper-functions)
11. [Complete Python Script](#11-complete-python-script)

---

## 1. Database Setup

### Locating the Database

```bash
# Copy chat.db to a working location (database is locked while Messages.app runs)
cp ~/Library/Messages/chat.db ~/Desktop/chat.db
```

### Opening with SQLite

```bash
sqlite3 ~/Desktop/chat.db
```

### Key Tables

| Table                     | Purpose                                      |
| ------------------------- | -------------------------------------------- |
| `message`                 | All messages (text, timestamps, sender info) |
| `handle`                  | Contact identifiers (phone numbers, emails)  |
| `chat`                    | Chat metadata                                |
| `chat_message_join`       | Links messages to chats                      |
| `attachment`              | Attachment metadata (photos, videos, files)  |
| `message_attachment_join` | Links messages to attachments                |

### Date Conversion

Apple stores dates as **nanoseconds since January 1, 2001**. Use these conversions:

```sql
-- Convert Apple timestamp to readable date
datetime(message.date/1000000000 + 978307200, 'unixepoch', 'localtime')

-- Filter for 2025
WHERE message.date >= strftime('%s', '2025-01-01') * 1000000000 - 978307200000000000
  AND message.date < strftime('%s', '2026-01-01') * 1000000000 - 978307200000000000
```

### Finding Your Contact's Handle ID

```sql
SELECT ROWID, id FROM handle WHERE id LIKE '%YOUR_PHONE_NUMBER%';
-- Note the ROWID — use it for handle_id filters
```

---

## 2. The Classics

### Total Messages (Combined)

```sql
SELECT COUNT(*) as total_messages
FROM message m
JOIN handle h ON m.handle_id = h.ROWID
WHERE h.id LIKE '%YOUR_PHONE_NUMBER%'
  AND m.date >= strftime('%s', '2025-01-01') * 1000000000 - 978307200000000000
  AND m.date < strftime('%s', '2026-01-01') * 1000000000 - 978307200000000000;
```

### Messages You Sent

```sql
SELECT COUNT(*) as you_sent
FROM message m
JOIN handle h ON m.handle_id = h.ROWID
WHERE h.id LIKE '%YOUR_PHONE_NUMBER%'
  AND m.is_from_me = 1
  AND m.date >= strftime('%s', '2025-01-01') * 1000000000 - 978307200000000000
  AND m.date < strftime('%s', '2026-01-01') * 1000000000 - 978307200000000000;
```

### Messages They Sent

```sql
SELECT COUNT(*) as they_sent
FROM message m
JOIN handle h ON m.handle_id = h.ROWID
WHERE h.id LIKE '%YOUR_PHONE_NUMBER%'
  AND m.is_from_me = 0
  AND m.date >= strftime('%s', '2025-01-01') * 1000000000 - 978307200000000000
  AND m.date < strftime('%s', '2026-01-01') * 1000000000 - 978307200000000000;
```

### Messages by Month

```sql
SELECT
    strftime('%m', datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime')) as month,
    SUM(CASE WHEN m.is_from_me = 1 THEN 1 ELSE 0 END) as you,
    SUM(CASE WHEN m.is_from_me = 0 THEN 1 ELSE 0 END) as them
FROM message m
JOIN handle h ON m.handle_id = h.ROWID
WHERE h.id LIKE '%YOUR_PHONE_NUMBER%'
  AND m.date >= strftime('%s', '2025-01-01') * 1000000000 - 978307200000000000
  AND m.date < strftime('%s', '2026-01-01') * 1000000000 - 978307200000000000
GROUP BY month
ORDER BY month;
```

### Busiest Day of the Week

```sql
SELECT
    CASE strftime('%w', datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime'))
        WHEN '0' THEN 'Sunday'
        WHEN '1' THEN 'Monday'
        WHEN '2' THEN 'Tuesday'
        WHEN '3' THEN 'Wednesday'
        WHEN '4' THEN 'Thursday'
        WHEN '5' THEN 'Friday'
        WHEN '6' THEN 'Saturday'
    END as day_of_week,
    COUNT(*) as message_count
FROM message m
JOIN handle h ON m.handle_id = h.ROWID
WHERE h.id LIKE '%YOUR_PHONE_NUMBER%'
  AND m.date >= strftime('%s', '2025-01-01') * 1000000000 - 978307200000000000
  AND m.date < strftime('%s', '2026-01-01') * 1000000000 - 978307200000000000
GROUP BY day_of_week
ORDER BY message_count DESC;
```

### Peak Texting Hours

```sql
SELECT
    strftime('%H', datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime')) as hour,
    COUNT(*) as message_count
FROM message m
JOIN handle h ON m.handle_id = h.ROWID
WHERE h.id LIKE '%YOUR_PHONE_NUMBER%'
  AND m.date >= strftime('%s', '2025-01-01') * 1000000000 - 978307200000000000
  AND m.date < strftime('%s', '2026-01-01') * 1000000000 - 978307200000000000
GROUP BY hour
ORDER BY message_count DESC
LIMIT 5;
```

### First Message of the Year

```sql
SELECT
    datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime') as date,
    CASE WHEN m.is_from_me = 1 THEN 'You' ELSE 'Them' END as sender,
    m.text
FROM message m
JOIN handle h ON m.handle_id = h.ROWID
WHERE h.id LIKE '%YOUR_PHONE_NUMBER%'
  AND m.date >= strftime('%s', '2025-01-01') * 1000000000 - 978307200000000000
  AND m.date < strftime('%s', '2026-01-01') * 1000000000 - 978307200000000000
  AND m.text IS NOT NULL
  AND m.text != ''
ORDER BY m.date ASC
LIMIT 1;
```

### Last Message of the Year

```sql
SELECT
    datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime') as date,
    CASE WHEN m.is_from_me = 1 THEN 'You' ELSE 'Them' END as sender,
    m.text
FROM message m
JOIN handle h ON m.handle_id = h.ROWID
WHERE h.id LIKE '%YOUR_PHONE_NUMBER%'
  AND m.date >= strftime('%s', '2025-01-01') * 1000000000 - 978307200000000000
  AND m.date < strftime('%s', '2026-01-01') * 1000000000 - 978307200000000000
  AND m.text IS NOT NULL
  AND m.text != ''
ORDER BY m.date DESC
LIMIT 1;
```

### Busiest Single Days (Top 5)

```sql
SELECT
    strftime('%Y-%m-%d', datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime')) as date,
    COUNT(*) as message_count
FROM message m
JOIN handle h ON m.handle_id = h.ROWID
WHERE h.id LIKE '%YOUR_PHONE_NUMBER%'
  AND m.date >= strftime('%s', '2025-01-01') * 1000000000 - 978307200000000000
  AND m.date < strftime('%s', '2026-01-01') * 1000000000 - 978307200000000000
GROUP BY date
ORDER BY message_count DESC
LIMIT 5;
```

---

## 3. Love & Affection

### "I Love You" Count

```sql
-- Your "I love you" messages
SELECT COUNT(*) as you_i_love_you
FROM message m
JOIN handle h ON m.handle_id = h.ROWID
WHERE h.id LIKE '%YOUR_PHONE_NUMBER%'
  AND m.is_from_me = 1
  AND m.date >= strftime('%s', '2025-01-01') * 1000000000 - 978307200000000000
  AND m.date < strftime('%s', '2026-01-01') * 1000000000 - 978307200000000000
  AND LOWER(m.text) LIKE '%i love you%';

-- Their "I love you" messages
SELECT COUNT(*) as them_i_love_you
FROM message m
JOIN handle h ON m.handle_id = h.ROWID
WHERE h.id LIKE '%YOUR_PHONE_NUMBER%'
  AND m.is_from_me = 0
  AND m.date >= strftime('%s', '2025-01-01') * 1000000000 - 978307200000000000
  AND m.date < strftime('%s', '2026-01-01') * 1000000000 - 978307200000000000
  AND LOWER(m.text) LIKE '%i love you%';
```

### Love Emojis (Per Emoji)

```sql
-- ♥️ Red Heart
SELECT
    SUM(CASE WHEN m.is_from_me = 1 THEN 1 ELSE 0 END) as you,
    SUM(CASE WHEN m.is_from_me = 0 THEN 1 ELSE 0 END) as them
FROM message m
JOIN handle h ON m.handle_id = h.ROWID
WHERE h.id LIKE '%YOUR_PHONE_NUMBER%'
  AND m.date >= strftime('%s', '2025-01-01') * 1000000000 - 978307200000000000
  AND m.date < strftime('%s', '2026-01-01') * 1000000000 - 978307200000000000
  AND m.text LIKE '%♥️%';

-- 😘 Kiss Face
SELECT
    SUM(CASE WHEN m.is_from_me = 1 THEN 1 ELSE 0 END) as you,
    SUM(CASE WHEN m.is_from_me = 0 THEN 1 ELSE 0 END) as them
FROM message m
JOIN handle h ON m.handle_id = h.ROWID
WHERE h.id LIKE '%YOUR_PHONE_NUMBER%'
  AND m.date >= strftime('%s', '2025-01-01') * 1000000000 - 978307200000000000
  AND m.date < strftime('%s', '2026-01-01') * 1000000000 - 978307200000000000
  AND m.text LIKE '%😘%';

-- 🥰 Smiling Face with Hearts
SELECT
    SUM(CASE WHEN m.is_from_me = 1 THEN 1 ELSE 0 END) as you,
    SUM(CASE WHEN m.is_from_me = 0 THEN 1 ELSE 0 END) as them
FROM message m
JOIN handle h ON m.handle_id = h.ROWID
WHERE h.id LIKE '%YOUR_PHONE_NUMBER%'
  AND m.date >= strftime('%s', '2025-01-01') * 1000000000 - 978307200000000000
  AND m.date < strftime('%s', '2026-01-01') * 1000000000 - 978307200000000000
  AND m.text LIKE '%🥰%';

-- 🫶🏽 Heart Hands
SELECT
    SUM(CASE WHEN m.is_from_me = 1 THEN 1 ELSE 0 END) as you,
    SUM(CASE WHEN m.is_from_me = 0 THEN 1 ELSE 0 END) as them
FROM message m
JOIN handle h ON m.handle_id = h.ROWID
WHERE h.id LIKE '%YOUR_PHONE_NUMBER%'
  AND m.date >= strftime('%s', '2025-01-01') * 1000000000 - 978307200000000000
  AND m.date < strftime('%s', '2026-01-01') * 1000000000 - 978307200000000000
  AND m.text LIKE '%🫶%';
```

### Pet Names

```sql
-- "baby" (includes babyy, babyyy, etc.)
SELECT
    SUM(CASE WHEN m.is_from_me = 1 THEN 1 ELSE 0 END) as you,
    SUM(CASE WHEN m.is_from_me = 0 THEN 1 ELSE 0 END) as them
FROM message m
JOIN handle h ON m.handle_id = h.ROWID
WHERE h.id LIKE '%YOUR_PHONE_NUMBER%'
  AND m.date >= strftime('%s', '2025-01-01') * 1000000000 - 978307200000000000
  AND m.date < strftime('%s', '2026-01-01') * 1000000000 - 978307200000000000
  AND LOWER(m.text) LIKE '%baby%';

-- "babe"
SELECT
    SUM(CASE WHEN m.is_from_me = 1 THEN 1 ELSE 0 END) as you,
    SUM(CASE WHEN m.is_from_me = 0 THEN 1 ELSE 0 END) as them
FROM message m
JOIN handle h ON m.handle_id = h.ROWID
WHERE h.id LIKE '%YOUR_PHONE_NUMBER%'
  AND m.date >= strftime('%s', '2025-01-01') * 1000000000 - 978307200000000000
  AND m.date < strftime('%s', '2026-01-01') * 1000000000 - 978307200000000000
  AND LOWER(m.text) LIKE '%babe%';

-- "my love"
SELECT
    SUM(CASE WHEN m.is_from_me = 1 THEN 1 ELSE 0 END) as you,
    SUM(CASE WHEN m.is_from_me = 0 THEN 1 ELSE 0 END) as them
FROM message m
JOIN handle h ON m.handle_id = h.ROWID
WHERE h.id LIKE '%YOUR_PHONE_NUMBER%'
  AND m.date >= strftime('%s', '2025-01-01') * 1000000000 - 978307200000000000
  AND m.date < strftime('%s', '2026-01-01') * 1000000000 - 978307200000000000
  AND LOWER(m.text) LIKE '%my love%';
```

---

## 4. Conversation Patterns

### Average Response Time

This requires more complex analysis — export messages and calculate in Python/JS:

```sql
-- Export all messages with timestamps for response time calculation
SELECT
    m.ROWID,
    datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime') as timestamp,
    m.date as raw_date,
    m.is_from_me,
    m.text
FROM message m
JOIN handle h ON m.handle_id = h.ROWID
WHERE h.id LIKE '%YOUR_PHONE_NUMBER%'
  AND m.date >= strftime('%s', '2025-01-01') * 1000000000 - 978307200000000000
  AND m.date < strftime('%s', '2026-01-01') * 1000000000 - 978307200000000000
ORDER BY m.date;
```

### Double/Triple Texts (Consecutive Messages)

```sql
-- Export for analysis (count consecutive is_from_me = 1 or 0 sequences)
SELECT
    m.ROWID,
    m.is_from_me,
    m.date
FROM message m
JOIN handle h ON m.handle_id = h.ROWID
WHERE h.id LIKE '%YOUR_PHONE_NUMBER%'
  AND m.date >= strftime('%s', '2025-01-01') * 1000000000 - 978307200000000000
  AND m.date < strftime('%s', '2026-01-01') * 1000000000 - 978307200000000000
ORDER BY m.date;
```

### Longest Silence Gap

```sql
-- Find gaps between messages (requires window functions)
WITH ordered_messages AS (
    SELECT
        m.date as current_date,
        LAG(m.date) OVER (ORDER BY m.date) as prev_date,
        datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime') as current_time
    FROM message m
    JOIN handle h ON m.handle_id = h.ROWID
    WHERE h.id LIKE '%YOUR_PHONE_NUMBER%'
      AND m.date >= strftime('%s', '2025-01-01') * 1000000000 - 978307200000000000
      AND m.date < strftime('%s', '2026-01-01') * 1000000000 - 978307200000000000
)
SELECT
    datetime(prev_date/1000000000 + 978307200, 'unixepoch', 'localtime') as gap_start,
    current_time as gap_end,
    (current_date - prev_date) / 1000000000.0 / 3600 as hours_gap
FROM ordered_messages
WHERE prev_date IS NOT NULL
ORDER BY hours_gap DESC
LIMIT 5;
```

---

## 5. Media & Attachments

### Total Attachments by Person

```sql
SELECT
    SUM(CASE WHEN m.is_from_me = 1 THEN 1 ELSE 0 END) as you,
    SUM(CASE WHEN m.is_from_me = 0 THEN 1 ELSE 0 END) as them
FROM message m
JOIN handle h ON m.handle_id = h.ROWID
WHERE h.id LIKE '%YOUR_PHONE_NUMBER%'
  AND m.date >= strftime('%s', '2025-01-01') * 1000000000 - 978307200000000000
  AND m.date < strftime('%s', '2026-01-01') * 1000000000 - 978307200000000000
  AND m.cache_has_attachments = 1;
```

### Voice Memos

```sql
SELECT
    SUM(CASE WHEN m.is_from_me = 1 THEN 1 ELSE 0 END) as you,
    SUM(CASE WHEN m.is_from_me = 0 THEN 1 ELSE 0 END) as them
FROM message m
JOIN handle h ON m.handle_id = h.ROWID
JOIN message_attachment_join maj ON m.ROWID = maj.message_id
JOIN attachment a ON maj.attachment_id = a.ROWID
WHERE h.id LIKE '%YOUR_PHONE_NUMBER%'
  AND m.date >= strftime('%s', '2025-01-01') * 1000000000 - 978307200000000000
  AND m.date < strftime('%s', '2026-01-01') * 1000000000 - 978307200000000000
  AND (a.mime_type LIKE '%audio%' OR a.filename LIKE '%.caf' OR a.filename LIKE '%.m4a');
```

### Links Shared

```sql
SELECT
    SUM(CASE WHEN m.is_from_me = 1 THEN 1 ELSE 0 END) as you,
    SUM(CASE WHEN m.is_from_me = 0 THEN 1 ELSE 0 END) as them
FROM message m
JOIN handle h ON m.handle_id = h.ROWID
WHERE h.id LIKE '%YOUR_PHONE_NUMBER%'
  AND m.date >= strftime('%s', '2025-01-01') * 1000000000 - 978307200000000000
  AND m.date < strftime('%s', '2026-01-01') * 1000000000 - 978307200000000000
  AND (m.text LIKE '%http://%' OR m.text LIKE '%https://%');
```

---

## 6. Reactions

### Understanding Reactions in iMessage

Reactions are stored as separate messages with `associated_message_type` values:

| Value | Reaction            |
| ----- | ------------------- |
| 2000  | ❤️ Loved            |
| 2001  | 👍 Liked            |
| 2002  | 👎 Disliked         |
| 2003  | 😂 Laughed          |
| 2004  | ‼️ Emphasized       |
| 2005  | ❓ Questioned       |
| 3000  | Removed ❤️ Love     |
| 3001  | Removed 👍 Like     |
| 3002  | Removed 👎 Dislike  |
| 3003  | Removed 😂 Laugh    |
| 3004  | Removed ‼️ Emphasis |
| 3005  | Removed ❓ Question |

### Heart Reactions Given

```sql
-- Heart reactions THEY gave (on your messages)
SELECT COUNT(*) as their_heart_reactions
FROM message m
JOIN handle h ON m.handle_id = h.ROWID
WHERE h.id LIKE '%YOUR_PHONE_NUMBER%'
  AND m.date >= strftime('%s', '2025-01-01') * 1000000000 - 978307200000000000
  AND m.date < strftime('%s', '2026-01-01') * 1000000000 - 978307200000000000
  AND m.associated_message_type = 2000
  AND m.is_from_me = 0;

-- Heart reactions YOU gave (on their messages)
SELECT COUNT(*) as your_heart_reactions
FROM message m
JOIN handle h ON m.handle_id = h.ROWID
WHERE h.id LIKE '%YOUR_PHONE_NUMBER%'
  AND m.date >= strftime('%s', '2025-01-01') * 1000000000 - 978307200000000000
  AND m.date < strftime('%s', '2026-01-01') * 1000000000 - 978307200000000000
  AND m.associated_message_type = 2000
  AND m.is_from_me = 1;
```

### All Reactions by Type and Person

```sql
SELECT
    CASE m.associated_message_type
        WHEN 2000 THEN '❤️ Love'
        WHEN 2001 THEN '👍 Like'
        WHEN 2002 THEN '👎 Dislike'
        WHEN 2003 THEN '😂 Laugh'
        WHEN 2004 THEN '‼️ Emphasis'
        WHEN 2005 THEN '❓ Question'
    END as reaction_type,
    SUM(CASE WHEN m.is_from_me = 1 THEN 1 ELSE 0 END) as you,
    SUM(CASE WHEN m.is_from_me = 0 THEN 1 ELSE 0 END) as them
FROM message m
JOIN handle h ON m.handle_id = h.ROWID
WHERE h.id LIKE '%YOUR_PHONE_NUMBER%'
  AND m.date >= strftime('%s', '2025-01-01') * 1000000000 - 978307200000000000
  AND m.date < strftime('%s', '2026-01-01') * 1000000000 - 978307200000000000
  AND m.associated_message_type BETWEEN 2000 AND 2005
GROUP BY reaction_type
ORDER BY (you + them) DESC;
```

---

## 7. Word Stats

### "Haha" Count

```sql
SELECT
    SUM(CASE WHEN m.is_from_me = 1 THEN 1 ELSE 0 END) as you,
    SUM(CASE WHEN m.is_from_me = 0 THEN 1 ELSE 0 END) as them
FROM message m
JOIN handle h ON m.handle_id = h.ROWID
WHERE h.id LIKE '%YOUR_PHONE_NUMBER%'
  AND m.date >= strftime('%s', '2025-01-01') * 1000000000 - 978307200000000000
  AND m.date < strftime('%s', '2026-01-01') * 1000000000 - 978307200000000000
  AND LOWER(m.text) LIKE '%haha%';
```

### "LOL" Count

```sql
SELECT
    SUM(CASE WHEN m.is_from_me = 1 THEN 1 ELSE 0 END) as you,
    SUM(CASE WHEN m.is_from_me = 0 THEN 1 ELSE 0 END) as them
FROM message m
JOIN handle h ON m.handle_id = h.ROWID
WHERE h.id LIKE '%YOUR_PHONE_NUMBER%'
  AND m.date >= strftime('%s', '2025-01-01') * 1000000000 - 978307200000000000
  AND m.date < strftime('%s', '2026-01-01') * 1000000000 - 978307200000000000
  AND LOWER(m.text) LIKE '%lol%';
```

### 😂 Emoji Count

```sql
SELECT
    SUM(CASE WHEN m.is_from_me = 1 THEN 1 ELSE 0 END) as you,
    SUM(CASE WHEN m.is_from_me = 0 THEN 1 ELSE 0 END) as them
FROM message m
JOIN handle h ON m.handle_id = h.ROWID
WHERE h.id LIKE '%YOUR_PHONE_NUMBER%'
  AND m.date >= strftime('%s', '2025-01-01') * 1000000000 - 978307200000000000
  AND m.date < strftime('%s', '2026-01-01') * 1000000000 - 978307200000000000
  AND m.text LIKE '%😂%';
```

### Question Marks (Who Asks More?)

```sql
SELECT
    SUM(CASE WHEN m.is_from_me = 1 THEN 1 ELSE 0 END) as you,
    SUM(CASE WHEN m.is_from_me = 0 THEN 1 ELSE 0 END) as them
FROM message m
JOIN handle h ON m.handle_id = h.ROWID
WHERE h.id LIKE '%YOUR_PHONE_NUMBER%'
  AND m.date >= strftime('%s', '2025-01-01') * 1000000000 - 978307200000000000
  AND m.date < strftime('%s', '2026-01-01') * 1000000000 - 978307200000000000
  AND m.text LIKE '%?%';
```

### ALL CAPS Messages

```sql
SELECT
    SUM(CASE WHEN m.is_from_me = 1 THEN 1 ELSE 0 END) as you,
    SUM(CASE WHEN m.is_from_me = 0 THEN 1 ELSE 0 END) as them
FROM message m
JOIN handle h ON m.handle_id = h.ROWID
WHERE h.id LIKE '%YOUR_PHONE_NUMBER%'
  AND m.date >= strftime('%s', '2025-01-01') * 1000000000 - 978307200000000000
  AND m.date < strftime('%s', '2026-01-01') * 1000000000 - 978307200000000000
  AND m.text = UPPER(m.text)
  AND m.text GLOB '*[A-Z]*'
  AND LENGTH(m.text) > 5;
```

### Top Emojis Used (Requires External Processing)

Export messages and count emojis with Python/JS:

```sql
-- Export all message text for emoji analysis
SELECT m.text
FROM message m
JOIN handle h ON m.handle_id = h.ROWID
WHERE h.id LIKE '%YOUR_PHONE_NUMBER%'
  AND m.date >= strftime('%s', '2025-01-01') * 1000000000 - 978307200000000000
  AND m.date < strftime('%s', '2026-01-01') * 1000000000 - 978307200000000000
  AND m.text IS NOT NULL;
```

---

## 8. Milestones

### Date You Hit Message Milestones

```sql
-- Running count to find milestone dates
WITH numbered_messages AS (
    SELECT
        ROW_NUMBER() OVER (ORDER BY m.date) as msg_number,
        datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime') as timestamp
    FROM message m
    JOIN handle h ON m.handle_id = h.ROWID
    WHERE h.id LIKE '%YOUR_PHONE_NUMBER%'
)
SELECT msg_number, timestamp
FROM numbered_messages
WHERE msg_number IN (10000, 50000, 100000, 150000, 200000, 250000, 300000);
```

### First Message Ever (All Time)

```sql
SELECT
    datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime') as date,
    CASE WHEN m.is_from_me = 1 THEN 'You' ELSE 'Them' END as sender,
    m.text
FROM message m
JOIN handle h ON m.handle_id = h.ROWID
WHERE h.id LIKE '%YOUR_PHONE_NUMBER%'
  AND m.text IS NOT NULL
ORDER BY m.date ASC
LIMIT 1;
```

---

## 9. Late Night Stats

### Messages Between Midnight - 4 AM

```sql
SELECT
    COUNT(*) as total,
    SUM(CASE WHEN m.is_from_me = 1 THEN 1 ELSE 0 END) as you,
    SUM(CASE WHEN m.is_from_me = 0 THEN 1 ELSE 0 END) as them
FROM message m
JOIN handle h ON m.handle_id = h.ROWID
WHERE h.id LIKE '%YOUR_PHONE_NUMBER%'
  AND m.date >= strftime('%s', '2025-01-01') * 1000000000 - 978307200000000000
  AND m.date < strftime('%s', '2026-01-01') * 1000000000 - 978307200000000000
  AND CAST(strftime('%H', datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime')) AS INTEGER) < 4;
```

### Who Texts First in the Morning

```sql
-- First message each day between 5 AM - 12 PM
WITH daily_first AS (
    SELECT
        strftime('%Y-%m-%d', datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime')) as day,
        m.is_from_me,
        ROW_NUMBER() OVER (
            PARTITION BY strftime('%Y-%m-%d', datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime'))
            ORDER BY m.date
        ) as rn
    FROM message m
    JOIN handle h ON m.handle_id = h.ROWID
    WHERE h.id LIKE '%YOUR_PHONE_NUMBER%'
      AND m.date >= strftime('%s', '2025-01-01') * 1000000000 - 978307200000000000
      AND m.date < strftime('%s', '2026-01-01') * 1000000000 - 978307200000000000
      AND CAST(strftime('%H', datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime')) AS INTEGER) BETWEEN 5 AND 12
)
SELECT
    SUM(CASE WHEN is_from_me = 1 THEN 1 ELSE 0 END) as you_first,
    SUM(CASE WHEN is_from_me = 0 THEN 1 ELSE 0 END) as them_first
FROM daily_first
WHERE rn = 1;
```

### Who Says Goodnight Last

```sql
-- Last message each day between 9 PM - 4 AM (next day)
WITH daily_last AS (
    SELECT
        CASE
            WHEN CAST(strftime('%H', datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime')) AS INTEGER) < 5
            THEN strftime('%Y-%m-%d', datetime(m.date/1000000000 + 978307200 - 86400, 'unixepoch', 'localtime'))
            ELSE strftime('%Y-%m-%d', datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime'))
        END as night,
        m.is_from_me,
        ROW_NUMBER() OVER (
            PARTITION BY CASE
                WHEN CAST(strftime('%H', datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime')) AS INTEGER) < 5
                THEN strftime('%Y-%m-%d', datetime(m.date/1000000000 + 978307200 - 86400, 'unixepoch', 'localtime'))
                ELSE strftime('%Y-%m-%d', datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime'))
            END
            ORDER BY m.date DESC
        ) as rn
    FROM message m
    JOIN handle h ON m.handle_id = h.ROWID
    WHERE h.id LIKE '%YOUR_PHONE_NUMBER%'
      AND m.date >= strftime('%s', '2025-01-01') * 1000000000 - 978307200000000000
      AND m.date < strftime('%s', '2026-01-01') * 1000000000 - 978307200000000000
      AND (
          CAST(strftime('%H', datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime')) AS INTEGER) >= 21
          OR CAST(strftime('%H', datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime')) AS INTEGER) < 5
      )
)
SELECT
    SUM(CASE WHEN is_from_me = 1 THEN 1 ELSE 0 END) as you_last,
    SUM(CASE WHEN is_from_me = 0 THEN 1 ELSE 0 END) as them_last
FROM daily_last
WHERE rn = 1;
```

---

## 10. Helper Functions

### Python Script for Response Time Calculation

```python
import sqlite3
from datetime import datetime

def calculate_response_times(db_path, phone_number, year=2025):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    query = f"""
    SELECT
        m.date,
        m.is_from_me
    FROM message m
    JOIN handle h ON m.handle_id = h.ROWID
    WHERE h.id LIKE '%{phone_number}%'
      AND m.date >= strftime('%s', '{year}-01-01') * 1000000000 - 978307200000000000
      AND m.date < strftime('%s', '{year+1}-01-01') * 1000000000 - 978307200000000000
    ORDER BY m.date
    """

    cursor.execute(query)
    messages = cursor.fetchall()

    your_response_times = []
    their_response_times = []

    for i in range(1, len(messages)):
        current = messages[i]
        previous = messages[i-1]

        # Skip if same sender (not a response)
        if current[1] == previous[1]:
            continue

        # Calculate time difference in minutes
        time_diff = (current[0] - previous[0]) / 1000000000 / 60

        # Only count responses under 60 minutes as "responses"
        if time_diff > 60:
            continue

        if current[1] == 1:  # You responding
            your_response_times.append(time_diff)
        else:  # Them responding
            their_response_times.append(time_diff)

    your_avg = sum(your_response_times) / len(your_response_times) if your_response_times else 0
    their_avg = sum(their_response_times) / len(their_response_times) if their_response_times else 0

    return {
        'your_avg_minutes': round(your_avg, 1),
        'their_avg_minutes': round(their_avg, 1)
    }
```

### Python Script for Emoji Counting

```python
import sqlite3
import re
from collections import Counter

def count_emojis(db_path, phone_number, year=2025):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    query = f"""
    SELECT m.text
    FROM message m
    JOIN handle h ON m.handle_id = h.ROWID
    WHERE h.id LIKE '%{phone_number}%'
      AND m.date >= strftime('%s', '{year}-01-01') * 1000000000 - 978307200000000000
      AND m.date < strftime('%s', '{year+1}-01-01') * 1000000000 - 978307200000000000
      AND m.text IS NOT NULL
    """

    cursor.execute(query)
    messages = cursor.fetchall()

    # Emoji regex pattern
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"  # dingbats
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "\U0001FA00-\U0001FA6F"  # chess symbols
        "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-A
        "\U00002600-\U000026FF"  # misc symbols
        "\U0001F000-\U0001F02F"  # mahjong tiles
        "]+", flags=re.UNICODE
    )

    emoji_counter = Counter()

    for (text,) in messages:
        if text:
            emojis = emoji_pattern.findall(text)
            for emoji in emojis:
                # Count individual emojis
                for char in emoji:
                    emoji_counter[char] += 1

    return emoji_counter.most_common(15)
```

### Python Script for Double Text Counting

```python
import sqlite3

def count_double_texts(db_path, phone_number, year=2025):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    query = f"""
    SELECT m.is_from_me
    FROM message m
    JOIN handle h ON m.handle_id = h.ROWID
    WHERE h.id LIKE '%{phone_number}%'
      AND m.date >= strftime('%s', '{year}-01-01') * 1000000000 - 978307200000000000
      AND m.date < strftime('%s', '{year+1}-01-01') * 1000000000 - 978307200000000000
    ORDER BY m.date
    """

    cursor.execute(query)
    messages = cursor.fetchall()

    your_double_texts = 0
    their_double_texts = 0

    for i in range(1, len(messages)):
        current = messages[i][0]
        previous = messages[i-1][0]

        if current == previous:  # Same sender = double text
            if current == 1:
                your_double_texts += 1
            else:
                their_double_texts += 1

    return {
        'you': your_double_texts,
        'them': their_double_texts
    }
```

---

## Quick Reference Card

### Date Filter Template

```sql
-- Replace YEAR with target year (e.g., 2026)
AND m.date >= strftime('%s', 'YEAR-01-01') * 1000000000 - 978307200000000000
AND m.date < strftime('%s', 'YEAR+1-01-01') * 1000000000 - 978307200000000000
```

### Common Column Reference

| Column                      | Description                |
| --------------------------- | -------------------------- |
| `m.text`                    | Message content            |
| `m.is_from_me`              | 1 = you sent, 0 = received |
| `m.date`                    | Apple nanosecond timestamp |
| `m.cache_has_attachments`   | 1 = has media              |
| `m.associated_message_type` | Reaction type (2000-2005)  |
| `h.id`                      | Phone number / email       |

### Timestamp Conversion Cheat Sheet

```sql
-- Apple timestamp to readable
datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime')

-- Get hour (0-23)
strftime('%H', datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime'))

-- Get day of week (0 = Sunday)
strftime('%w', datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime'))

-- Get month (01-12)
strftime('%m', datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime'))

-- Get date (YYYY-MM-DD)
strftime('%Y-%m-%d', datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime'))
```

---

## Notes for Future Years

1. **Backup Access:** Use Finder to back up iPhone, then extract `chat.db` from:

   ```
   ~/Library/Application Support/MobileSync/Backup/[DEVICE_ID]/3d/3d0d7e5fb2ce288813306e4d4636395e047a3d28
   ```

2. **Full Disk Access:** Grant Terminal full disk access in System Preferences > Security & Privacy to read `chat.db` directly

3. **Date Adjustments:** Update all year references in the date filters

4. **Phone Number:** Update the `YOUR_PHONE_NUMBER` placeholder with your contact's number

5. **Export Results:** Use `.mode csv` and `.output filename.csv` in SQLite to export results

---

## 11. Complete Python Script

This script runs all queries and outputs a complete JSON file with your iMessage stats.

```python
#!/usr/bin/env python3
"""
iMessage Wrapped - Complete Stats Extractor
============================================
Extracts comprehensive messaging statistics from macOS iMessage database.

Usage:
    python imessage_wrapped.py --phone YOUR_PHONE_NUMBER --year 2025 --db ~/Desktop/chat.db

Requirements:
    - macOS with iMessage
    - Python 3.8+
    - Copy chat.db from ~/Library/Messages/chat.db (quit Messages app first)
"""

import sqlite3
import json
import re
import argparse
from collections import Counter
from datetime import datetime
from pathlib import Path


# =============================================================================
# CONFIGURATION
# =============================================================================

APPLE_EPOCH_OFFSET = 978307200  # Seconds between Unix epoch and Apple epoch
NANOSECONDS = 1000000000

# Reaction type mappings
REACTION_TYPES = {
    2000: "❤️ Love",
    2001: "👍 Like",
    2002: "👎 Dislike",
    2003: "😂 Laugh",
    2004: "‼️ Emphasis",
    2005: "❓ Question",
}

# Days of week mapping
DAYS_OF_WEEK = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

# Month names
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Emoji regex pattern
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U00002702-\U000027B0"  # dingbats
    "\U0001F900-\U0001F9FF"  # supplemental symbols
    "\U0001FA00-\U0001FA6F"  # chess symbols
    "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-A
    "\U00002600-\U000026FF"  # misc symbols
    "\U0001F000-\U0001F02F"  # mahjong tiles
    "\U00002500-\U00002BEF"  # various symbols
    "\U0001F004"  # mahjong
    "\U0001F0CF"  # playing card
    "]+",
    flags=re.UNICODE,
)


# =============================================================================
# DATABASE HELPERS
# =============================================================================

def get_date_filter(year: int) -> tuple[int, int]:
    """Get Apple timestamp bounds for a given year."""
    start = int((datetime(year, 1, 1).timestamp() - APPLE_EPOCH_OFFSET) * NANOSECONDS)
    end = int((datetime(year + 1, 1, 1).timestamp() - APPLE_EPOCH_OFFSET) * NANOSECONDS)
    return start, end


def apple_to_datetime(timestamp: int) -> datetime:
    """Convert Apple timestamp to Python datetime."""
    return datetime.fromtimestamp(timestamp / NANOSECONDS + APPLE_EPOCH_OFFSET)


def format_datetime(dt: datetime) -> str:
    """Format datetime for display."""
    return dt.strftime("%b %d, %Y at %I:%M %p")


# =============================================================================
# STAT EXTRACTION FUNCTIONS
# =============================================================================

class iMessageStats:
    def __init__(self, db_path: str, phone_number: str, year: int):
        self.db_path = db_path
        self.phone_number = phone_number
        self.year = year
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.date_start, self.date_end = get_date_filter(year)

    def _base_query(self, extra_conditions: str = "", extra_joins: str = "") -> str:
        """Generate base query with standard filters."""
        return f"""
            FROM message m
            JOIN handle h ON m.handle_id = h.ROWID
            {extra_joins}
            WHERE h.id LIKE '%{self.phone_number}%'
              AND m.date >= {self.date_start}
              AND m.date < {self.date_end}
              {extra_conditions}
        """

    def get_total_messages(self) -> dict:
        """Get total message counts."""
        query = f"SELECT COUNT(*), SUM(CASE WHEN m.is_from_me = 1 THEN 1 ELSE 0 END), SUM(CASE WHEN m.is_from_me = 0 THEN 1 ELSE 0 END) {self._base_query()}"
        self.cursor.execute(query)
        total, you, them = self.cursor.fetchone()
        return {"total": total or 0, "you": you or 0, "them": them or 0}

    def get_messages_by_month(self) -> list[dict]:
        """Get message breakdown by month."""
        query = f"""
            SELECT
                CAST(strftime('%m', datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime')) AS INTEGER) as month,
                SUM(CASE WHEN m.is_from_me = 1 THEN 1 ELSE 0 END) as you,
                SUM(CASE WHEN m.is_from_me = 0 THEN 1 ELSE 0 END) as them
            {self._base_query()}
            GROUP BY month
            ORDER BY month
        """
        self.cursor.execute(query)
        results = []
        for month, you, them in self.cursor.fetchall():
            results.append({"month": MONTHS[month - 1], "you": you or 0, "them": them or 0})
        return results

    def get_busiest_days_of_week(self) -> list[dict]:
        """Get message counts by day of week."""
        query = f"""
            SELECT
                CAST(strftime('%w', datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime')) AS INTEGER) as dow,
                COUNT(*) as count
            {self._base_query()}
            GROUP BY dow
            ORDER BY count DESC
        """
        self.cursor.execute(query)
        return [{"day": DAYS_OF_WEEK[dow], "count": count} for dow, count in self.cursor.fetchall()]

    def get_peak_hours(self) -> list[dict]:
        """Get top 5 busiest hours."""
        query = f"""
            SELECT
                CAST(strftime('%H', datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime')) AS INTEGER) as hour,
                COUNT(*) as count
            {self._base_query()}
            GROUP BY hour
            ORDER BY count DESC
            LIMIT 5
        """
        self.cursor.execute(query)
        results = []
        for hour, count in self.cursor.fetchall():
            hour_str = f"{hour % 12 or 12} {'AM' if hour < 12 else 'PM'}"
            results.append({"hour": hour_str, "count": count})
        return results

    def get_first_last_message(self) -> dict:
        """Get first and last message of the year."""
        # First message
        query_first = f"""
            SELECT m.date, m.is_from_me, m.text
            {self._base_query("AND m.text IS NOT NULL AND m.text != ''")}
            ORDER BY m.date ASC
            LIMIT 1
        """
        self.cursor.execute(query_first)
        first = self.cursor.fetchone()

        # Last message
        query_last = f"""
            SELECT m.date, m.is_from_me, m.text
            {self._base_query("AND m.text IS NOT NULL AND m.text != ''")}
            ORDER BY m.date DESC
            LIMIT 1
        """
        self.cursor.execute(query_last)
        last = self.cursor.fetchone()

        result = {}
        if first:
            result["first"] = {
                "date": format_datetime(apple_to_datetime(first[0])),
                "sender": "You" if first[1] == 1 else "Them",
                "text": first[2][:100] if first[2] else "",
            }
        if last:
            result["last"] = {
                "date": format_datetime(apple_to_datetime(last[0])),
                "sender": "You" if last[1] == 1 else "Them",
                "text": last[2][:100] if last[2] else "",
            }
        return result

    def get_busiest_single_days(self, limit: int = 5) -> list[dict]:
        """Get the busiest single days."""
        query = f"""
            SELECT
                strftime('%Y-%m-%d', datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime')) as date,
                COUNT(*) as count
            {self._base_query()}
            GROUP BY date
            ORDER BY count DESC
            LIMIT {limit}
        """
        self.cursor.execute(query)
        results = []
        for date_str, count in self.cursor.fetchall():
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            results.append({"date": dt.strftime("%b %d, %Y"), "count": count})
        return results

    def get_i_love_you_count(self) -> dict:
        """Count 'I love you' messages."""
        query = f"""
            SELECT
                SUM(CASE WHEN m.is_from_me = 1 THEN 1 ELSE 0 END) as you,
                SUM(CASE WHEN m.is_from_me = 0 THEN 1 ELSE 0 END) as them
            {self._base_query("AND LOWER(m.text) LIKE '%i love you%'")}
        """
        self.cursor.execute(query)
        you, them = self.cursor.fetchone()
        return {"you": you or 0, "them": them or 0, "total": (you or 0) + (them or 0)}

    def get_word_phrase_count(self, phrase: str) -> dict:
        """Count messages containing a specific word/phrase."""
        query = f"""
            SELECT
                SUM(CASE WHEN m.is_from_me = 1 THEN 1 ELSE 0 END) as you,
                SUM(CASE WHEN m.is_from_me = 0 THEN 1 ELSE 0 END) as them
            {self._base_query(f"AND LOWER(m.text) LIKE '%{phrase.lower()}%'")}
        """
        self.cursor.execute(query)
        you, them = self.cursor.fetchone()
        return {"you": you or 0, "them": them or 0}

    def get_emoji_count(self, emoji: str) -> dict:
        """Count messages containing a specific emoji."""
        query = f"""
            SELECT
                SUM(CASE WHEN m.is_from_me = 1 THEN 1 ELSE 0 END) as you,
                SUM(CASE WHEN m.is_from_me = 0 THEN 1 ELSE 0 END) as them
            {self._base_query(f"AND m.text LIKE '%{emoji}%'")}
        """
        self.cursor.execute(query)
        you, them = self.cursor.fetchone()
        return {"you": you or 0, "them": them or 0}

    def get_reactions(self) -> list[dict]:
        """Get reaction counts by type and person."""
        query = f"""
            SELECT
                m.associated_message_type,
                SUM(CASE WHEN m.is_from_me = 1 THEN 1 ELSE 0 END) as you,
                SUM(CASE WHEN m.is_from_me = 0 THEN 1 ELSE 0 END) as them
            {self._base_query("AND m.associated_message_type BETWEEN 2000 AND 2005")}
            GROUP BY m.associated_message_type
            ORDER BY (you + them) DESC
        """
        self.cursor.execute(query)
        return [
            {"type": REACTION_TYPES.get(rtype, f"Type {rtype}"), "you": you or 0, "them": them or 0}
            for rtype, you, them in self.cursor.fetchall()
        ]

    def get_heart_reactions(self) -> dict:
        """Get heart reaction counts specifically."""
        query = f"""
            SELECT
                SUM(CASE WHEN m.is_from_me = 1 THEN 1 ELSE 0 END) as you,
                SUM(CASE WHEN m.is_from_me = 0 THEN 1 ELSE 0 END) as them
            {self._base_query("AND m.associated_message_type = 2000")}
        """
        self.cursor.execute(query)
        you, them = self.cursor.fetchone()
        return {"you": you or 0, "them": them or 0}

    def get_attachments(self) -> dict:
        """Get attachment counts."""
        query = f"""
            SELECT
                SUM(CASE WHEN m.is_from_me = 1 THEN 1 ELSE 0 END) as you,
                SUM(CASE WHEN m.is_from_me = 0 THEN 1 ELSE 0 END) as them
            {self._base_query("AND m.cache_has_attachments = 1")}
        """
        self.cursor.execute(query)
        you, them = self.cursor.fetchone()
        return {"you": you or 0, "them": them or 0, "total": (you or 0) + (them or 0)}

    def get_voice_memos(self) -> dict:
        """Get voice memo counts."""
        query = f"""
            SELECT
                SUM(CASE WHEN m.is_from_me = 1 THEN 1 ELSE 0 END) as you,
                SUM(CASE WHEN m.is_from_me = 0 THEN 1 ELSE 0 END) as them
            {self._base_query(
                "AND (a.mime_type LIKE '%audio%' OR a.filename LIKE '%.caf' OR a.filename LIKE '%.m4a')",
                "JOIN message_attachment_join maj ON m.ROWID = maj.message_id JOIN attachment a ON maj.attachment_id = a.ROWID"
            )}
        """
        self.cursor.execute(query)
        you, them = self.cursor.fetchone()
        return {"you": you or 0, "them": them or 0}

    def get_links(self) -> dict:
        """Get link counts."""
        query = f"""
            SELECT
                SUM(CASE WHEN m.is_from_me = 1 THEN 1 ELSE 0 END) as you,
                SUM(CASE WHEN m.is_from_me = 0 THEN 1 ELSE 0 END) as them
            {self._base_query("AND (m.text LIKE '%http://%' OR m.text LIKE '%https://%')")}
        """
        self.cursor.execute(query)
        you, them = self.cursor.fetchone()
        return {"you": you or 0, "them": them or 0}

    def get_questions(self) -> dict:
        """Get question mark counts."""
        query = f"""
            SELECT
                SUM(CASE WHEN m.is_from_me = 1 THEN 1 ELSE 0 END) as you,
                SUM(CASE WHEN m.is_from_me = 0 THEN 1 ELSE 0 END) as them
            {self._base_query("AND m.text LIKE '%?%'")}
        """
        self.cursor.execute(query)
        you, them = self.cursor.fetchone()
        return {"you": you or 0, "them": them or 0}

    def get_all_caps(self) -> dict:
        """Get ALL CAPS message counts."""
        query = f"""
            SELECT
                SUM(CASE WHEN m.is_from_me = 1 THEN 1 ELSE 0 END) as you,
                SUM(CASE WHEN m.is_from_me = 0 THEN 1 ELSE 0 END) as them
            {self._base_query("AND m.text = UPPER(m.text) AND m.text GLOB '*[A-Z]*' AND LENGTH(m.text) > 5")}
        """
        self.cursor.execute(query)
        you, them = self.cursor.fetchone()
        return {"you": you or 0, "them": them or 0}

    def get_late_night_messages(self) -> dict:
        """Get messages between midnight and 4 AM."""
        query = f"""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN m.is_from_me = 1 THEN 1 ELSE 0 END) as you,
                SUM(CASE WHEN m.is_from_me = 0 THEN 1 ELSE 0 END) as them
            {self._base_query("AND CAST(strftime('%H', datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime')) AS INTEGER) < 4")}
        """
        self.cursor.execute(query)
        total, you, them = self.cursor.fetchone()
        return {"total": total or 0, "you": you or 0, "them": them or 0}

    def get_morning_first(self) -> dict:
        """Get who texts first in the morning more often."""
        query = f"""
            WITH daily_first AS (
                SELECT
                    strftime('%Y-%m-%d', datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime')) as day,
                    m.is_from_me,
                    ROW_NUMBER() OVER (
                        PARTITION BY strftime('%Y-%m-%d', datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime'))
                        ORDER BY m.date
                    ) as rn
                {self._base_query("AND CAST(strftime('%H', datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime')) AS INTEGER) BETWEEN 5 AND 12")}
            )
            SELECT
                SUM(CASE WHEN is_from_me = 1 THEN 1 ELSE 0 END) as you,
                SUM(CASE WHEN is_from_me = 0 THEN 1 ELSE 0 END) as them
            FROM daily_first
            WHERE rn = 1
        """
        self.cursor.execute(query)
        you, them = self.cursor.fetchone()
        return {"you": you or 0, "them": them or 0}

    def get_goodnight_last(self) -> dict:
        """Get who says goodnight last more often."""
        query = f"""
            WITH daily_last AS (
                SELECT
                    CASE
                        WHEN CAST(strftime('%H', datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime')) AS INTEGER) < 5
                        THEN strftime('%Y-%m-%d', datetime(m.date/1000000000 + 978307200 - 86400, 'unixepoch', 'localtime'))
                        ELSE strftime('%Y-%m-%d', datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime'))
                    END as night,
                    m.is_from_me,
                    ROW_NUMBER() OVER (
                        PARTITION BY CASE
                            WHEN CAST(strftime('%H', datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime')) AS INTEGER) < 5
                            THEN strftime('%Y-%m-%d', datetime(m.date/1000000000 + 978307200 - 86400, 'unixepoch', 'localtime'))
                            ELSE strftime('%Y-%m-%d', datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime'))
                        END
                        ORDER BY m.date DESC
                    ) as rn
                {self._base_query("""AND (
                    CAST(strftime('%H', datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime')) AS INTEGER) >= 21
                    OR CAST(strftime('%H', datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime')) AS INTEGER) < 5
                )""")}
            )
            SELECT
                SUM(CASE WHEN is_from_me = 1 THEN 1 ELSE 0 END) as you,
                SUM(CASE WHEN is_from_me = 0 THEN 1 ELSE 0 END) as them
            FROM daily_last
            WHERE rn = 1
        """
        self.cursor.execute(query)
        you, them = self.cursor.fetchone()
        return {"you": you or 0, "them": them or 0}

    def get_double_texts(self) -> dict:
        """Count consecutive messages from same sender."""
        query = f"""
            SELECT m.is_from_me
            {self._base_query()}
            ORDER BY m.date
        """
        self.cursor.execute(query)
        messages = self.cursor.fetchall()

        your_double_texts = 0
        their_double_texts = 0

        for i in range(1, len(messages)):
            if messages[i][0] == messages[i - 1][0]:
                if messages[i][0] == 1:
                    your_double_texts += 1
                else:
                    their_double_texts += 1

        return {"you": your_double_texts, "them": their_double_texts}

    def get_response_times(self) -> dict:
        """Calculate average response times."""
        query = f"""
            SELECT m.date, m.is_from_me
            {self._base_query()}
            ORDER BY m.date
        """
        self.cursor.execute(query)
        messages = self.cursor.fetchall()

        your_response_times = []
        their_response_times = []

        for i in range(1, len(messages)):
            current = messages[i]
            previous = messages[i - 1]

            if current[1] == previous[1]:
                continue

            time_diff = (current[0] - previous[0]) / NANOSECONDS / 60  # minutes

            if time_diff > 60:
                continue

            if current[1] == 1:
                your_response_times.append(time_diff)
            else:
                their_response_times.append(time_diff)

        your_avg = sum(your_response_times) / len(your_response_times) if your_response_times else 0
        their_avg = sum(their_response_times) / len(their_response_times) if their_response_times else 0

        return {"you": round(your_avg, 1), "them": round(their_avg, 1)}

    def get_longest_silence(self) -> dict:
        """Find the longest gap between messages."""
        query = f"""
            WITH ordered_messages AS (
                SELECT
                    m.date as current_date,
                    LAG(m.date) OVER (ORDER BY m.date) as prev_date
                {self._base_query()}
            )
            SELECT
                prev_date,
                current_date,
                (current_date - prev_date) / 1000000000.0 / 3600 as hours_gap
            FROM ordered_messages
            WHERE prev_date IS NOT NULL
            ORDER BY hours_gap DESC
            LIMIT 1
        """
        self.cursor.execute(query)
        result = self.cursor.fetchone()
        if result:
            return {
                "start": format_datetime(apple_to_datetime(result[0])),
                "end": format_datetime(apple_to_datetime(result[1])),
                "hours": round(result[2], 1),
            }
        return {}

    def get_top_emojis(self, limit: int = 15) -> list[dict]:
        """Get most used emojis."""
        query = f"""
            SELECT m.text
            {self._base_query("AND m.text IS NOT NULL")}
        """
        self.cursor.execute(query)
        messages = self.cursor.fetchall()

        emoji_counter = Counter()
        for (text,) in messages:
            if text:
                emojis = EMOJI_PATTERN.findall(text)
                for emoji_group in emojis:
                    for char in emoji_group:
                        emoji_counter[char] += 1

        return [{"emoji": emoji, "count": count} for emoji, count in emoji_counter.most_common(limit)]

    def get_milestones(self) -> list[dict]:
        """Find dates when message milestones were hit."""
        query = f"""
            WITH numbered_messages AS (
                SELECT
                    ROW_NUMBER() OVER (ORDER BY m.date) as msg_number,
                    m.date
                FROM message m
                JOIN handle h ON m.handle_id = h.ROWID
                WHERE h.id LIKE '%{self.phone_number}%'
            )
            SELECT msg_number, date
            FROM numbered_messages
            WHERE msg_number IN (10000, 25000, 50000, 75000, 100000, 150000, 200000, 250000, 300000, 400000, 500000)
        """
        self.cursor.execute(query)
        return [
            {"count": count, "date": format_datetime(apple_to_datetime(date)).split(" at")[0]}
            for count, date in self.cursor.fetchall()
        ]

    def get_all_stats(self) -> dict:
        """Collect all statistics."""
        print("Extracting iMessage statistics...")

        totals = self.get_total_messages()
        days_texting = len(set(
            row[0] for row in self.cursor.execute(f"""
                SELECT strftime('%Y-%m-%d', datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime'))
                {self._base_query()}
            """).fetchall()
        ))

        print(f"  Total messages: {totals['total']:,}")

        stats = {
            "meta": {
                "year": self.year,
                "generatedAt": datetime.now().isoformat(),
                "daysTexting": days_texting,
            },
            "classics": {
                "totalMessages": totals["total"],
                "youSent": totals["you"],
                "themSent": totals["them"],
                "avgPerDay": round(totals["total"] / max(days_texting, 1)),
                "byMonth": self.get_messages_by_month(),
                "busiestDays": self.get_busiest_days_of_week(),
                "peakHours": self.get_peak_hours(),
                "busiestSingleDays": self.get_busiest_single_days(),
                **self.get_first_last_message(),
            },
            "love": {
                "iLoveYou": self.get_i_love_you_count(),
                "heartReactions": self.get_heart_reactions(),
                "emojis": [
                    {"emoji": "♥️", **self.get_emoji_count("♥️")},
                    {"emoji": "😘", **self.get_emoji_count("😘")},
                    {"emoji": "🥰", **self.get_emoji_count("🥰")},
                    {"emoji": "🫶", **self.get_emoji_count("🫶")},
                ],
                "petNames": [
                    {"name": "baby", **self.get_word_phrase_count("baby")},
                    {"name": "babe", **self.get_word_phrase_count("babe")},
                    {"name": "my love", **self.get_word_phrase_count("my love")},
                ],
            },
            "patterns": {
                "avgResponseTime": self.get_response_times(),
                "doubleTexts": self.get_double_texts(),
                "longestSilence": self.get_longest_silence(),
            },
            "media": {
                "attachments": self.get_attachments(),
                "voiceMemos": self.get_voice_memos(),
                "links": self.get_links(),
                "reactions": self.get_reactions(),
            },
            "wordStats": {
                "laughing": [
                    {"style": "haha", **self.get_word_phrase_count("haha")},
                    {"style": "lol", **self.get_word_phrase_count("lol")},
                    {"style": "😂", **self.get_emoji_count("😂")},
                ],
                "questions": self.get_questions(),
                "allCaps": self.get_all_caps(),
                "topEmojis": self.get_top_emojis(),
            },
            "milestones": self.get_milestones(),
            "lateNight": {
                **self.get_late_night_messages(),
                "morningFirst": self.get_morning_first(),
                "goodnightLast": self.get_goodnight_last(),
            },
        }

        print("  Done!")
        return stats

    def close(self):
        """Close database connection."""
        self.conn.close()


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Extract iMessage statistics for your year in review",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python imessage_wrapped.py --phone 5551234567 --year 2025
    python imessage_wrapped.py --phone 5551234567 --year 2025 --db ~/Desktop/chat.db
    python imessage_wrapped.py --phone 5551234567 --year 2025 --output my_stats.json
        """,
    )
    parser.add_argument("--phone", required=True, help="Contact's phone number (digits only, e.g., 5551234567)")
    parser.add_argument("--year", type=int, default=datetime.now().year, help="Year to analyze (default: current year)")
    parser.add_argument("--db", default="~/Library/Messages/chat.db", help="Path to chat.db (default: ~/Library/Messages/chat.db)")
    parser.add_argument("--output", "-o", default="imessage_wrapped.json", help="Output JSON file (default: imessage_wrapped.json)")

    args = parser.parse_args()

    db_path = Path(args.db).expanduser()
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        print("\nTip: Copy your chat.db first:")
        print("  cp ~/Library/Messages/chat.db ~/Desktop/chat.db")
        print("\nThen run:")
        print(f"  python imessage_wrapped.py --phone {args.phone} --db ~/Desktop/chat.db")
        return 1

    print(f"\niMessage Wrapped {args.year}")
    print("=" * 40)
    print(f"Database: {db_path}")
    print(f"Contact: {args.phone}")
    print(f"Year: {args.year}")
    print()

    try:
        stats = iMessageStats(str(db_path), args.phone, args.year)
        data = stats.get_all_stats()
        stats.close()

        output_path = Path(args.output)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"\nStats saved to: {output_path.absolute()}")
        print(f"\nQuick summary:")
        print(f"  Total messages: {data['classics']['totalMessages']:,}")
        print(f"  You sent: {data['classics']['youSent']:,}")
        print(f"  They sent: {data['classics']['themSent']:,}")
        print(f"  'I love you' count: {data['love']['iLoveYou']['total']:,}")
        print(f"  Days texting: {data['meta']['daysTexting']}")

    except sqlite3.OperationalError as e:
        print(f"Error: {e}")
        print("\nThis might be a permissions issue. Try copying the database first:")
        print("  cp ~/Library/Messages/chat.db ~/Desktop/chat.db")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
```

---

## License

MIT License — Feel free to use, modify, and share.

---

_Happy Wrapping!_
