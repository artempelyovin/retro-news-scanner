import json
from typing import Any


def create_tables(conn) -> None:
    cur = conn.cursor()
    cur.execute(
        """
CREATE TABLE IF NOT EXISTS news
(
    id             INTEGER PRIMARY KEY,
    url            TEXT NOT NULL,
    title          TEXT NOT NULL,
    content        TEXT NOT NULL,
    published_date TEXT NOT NULL,
    created_at     TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at     TEXT DEFAULT CURRENT_TIMESTAMP
);
"""
    )
    cur.execute(
        """
CREATE TABLE IF NOT EXISTS prompts
(
    id         INTEGER PRIMARY KEY,
    text       TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""
    )
    cur.execute(
        """
CREATE TABLE IF NOT EXISTS news_evaluations
(
    id          INTEGER PRIMARY KEY,
    news_id     INTEGER NOT NULL,
    model       TEXT    NOT NULL,
    prompt_id   INTEGER NOT NULL,
    scores      TEXT    NOT NULL,
    final_score REAL    NOT NULL,
    created_at  TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (news_id) REFERENCES news (id) ON DELETE CASCADE,
    FOREIGN KEY (prompt_id) REFERENCES prompts (id) ON DELETE CASCADE
);
"""
    )

    cur.execute(
        """
CREATE TRIGGER IF NOT EXISTS update_news_timestamp
AFTER UPDATE ON news
BEGIN
    UPDATE news SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
"""
    )
    cur.execute(
        """
CREATE TRIGGER IF NOT EXISTS update_prompts_timestamp
AFTER UPDATE ON prompts
BEGIN
    UPDATE prompts SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
"""
    )
    cur.execute(
        """
CREATE TRIGGER IF NOT EXISTS update_news_evaluations_timestamp
AFTER UPDATE ON news_evaluations
BEGIN
    UPDATE news_evaluations SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
            """
    )
    conn.commit()


def add_prompt(conn, prompt: str) -> None:
    cur = conn.cursor()
    cur.execute("INSERT INTO prompts (text) VALUES (?);", (prompt,))
    conn.commit()


def add_news_evaluation(conn, news_id: int, model: str, prompt_id: int, scores: str, final_score: float) -> None:
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO news_evaluations (news_id, model, prompt_id, scores, final_score)  VALUES (?, ?, ?, ?, ?);",
        (news_id, model, prompt_id, scores, final_score),
    )
    conn.commit()


def get_prompt_by_id(conn, prompt_id) -> str | None:
    cur = conn.cursor()
    cur.execute("SELECT text FROM prompts WHERE id = ?; ", (prompt_id,))
    row = cur.fetchone()
    return row[0] if row else None


def get_news_without_evaluation(conn, limit: int = 100) -> list[tuple[Any, ...]]:
    cur = conn.cursor()
    cur.execute(
        "SELECT news.* "
        "FROM news "
        "LEFT JOIN news_evaluations ON news.id = news_evaluations.news_id WHERE "
        "news_evaluations.news_id IS NULL LIMIT ?;",
        (limit,),
    )
    rows = cur.fetchall()
    return rows
