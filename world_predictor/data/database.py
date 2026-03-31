"""SQLite persistence layer for World Predictor.

Stores simulation snapshots, daily metrics, news archive, and agent state
so the system can survive restarts and provide historical trend data.
"""

import json
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from world_predictor.config import db_config

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, path: Optional[str] = None):
        self.path = path or db_config()["path"]
        self._conn: Optional[sqlite3.Connection] = None
        self._init_db()

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.path)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
        return self._conn

    def _init_db(self):
        """Create tables if they don't exist."""
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS daily_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                country TEXT NOT NULL,
                day INTEGER NOT NULL,
                economic_sentiment REAL,
                social_cohesion REAL,
                political_stability REAL,
                average_optimism REAL,
                average_risk_aversion REAL,
                revolution_risk REAL DEFAULT 0.0,
                dominant_reaction TEXT,
                reaction_distribution TEXT,  -- JSON
                consensus TEXT,             -- JSON
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(country, day)
            );

            CREATE TABLE IF NOT EXISTS news_archive (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                source_name TEXT,
                source_politics REAL,
                source_credibility REAL,
                category TEXT,
                region TEXT,
                impact REAL,
                url TEXT,
                content TEXT,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS simulation_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                country TEXT NOT NULL,
                current_day INTEGER NOT NULL,
                agent_count INTEGER,
                state_json TEXT,  -- serialized agent summary stats
                saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(country)
            );

            CREATE INDEX IF NOT EXISTS idx_metrics_country_day ON daily_metrics(country, day);
            CREATE INDEX IF NOT EXISTS idx_news_category ON news_archive(category);
            CREATE INDEX IF NOT EXISTS idx_news_region ON news_archive(region);
            CREATE INDEX IF NOT EXISTS idx_news_fetched ON news_archive(fetched_at);
        """)
        self.conn.commit()

    # ---- Daily Metrics ----

    def save_daily_metrics(self, country: str, day: int, metrics: Dict, reactions: Dict, consensus: Dict):
        """Save daily simulation metrics for a country."""
        self.conn.execute("""
            INSERT OR REPLACE INTO daily_metrics
            (country, day, economic_sentiment, social_cohesion, political_stability,
             average_optimism, average_risk_aversion, revolution_risk,
             dominant_reaction, reaction_distribution, consensus)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            country, day,
            metrics.get("economic_sentiment"),
            metrics.get("social_cohesion"),
            metrics.get("political_stability"),
            metrics.get("average_optimism"),
            metrics.get("average_risk_aversion"),
            metrics.get("revolution_risk", 0.0),
            reactions.get("dominant"),
            json.dumps(reactions.get("distribution", {})),
            json.dumps(consensus),
        ))
        self.conn.commit()

    def get_metrics_history(self, country: str, days: int = 30) -> List[Dict]:
        """Get historical metrics for a country."""
        rows = self.conn.execute("""
            SELECT * FROM daily_metrics
            WHERE country = ?
            ORDER BY day DESC
            LIMIT ?
        """, (country, days)).fetchall()
        return [dict(r) for r in reversed(rows)]

    def get_latest_metrics(self, country: str) -> Optional[Dict]:
        """Get most recent metrics for a country."""
        row = self.conn.execute("""
            SELECT * FROM daily_metrics
            WHERE country = ?
            ORDER BY day DESC
            LIMIT 1
        """, (country,)).fetchone()
        return dict(row) if row else None

    def get_all_latest_metrics(self) -> Dict[str, Dict]:
        """Get latest metrics for all countries."""
        rows = self.conn.execute("""
            SELECT dm.* FROM daily_metrics dm
            INNER JOIN (
                SELECT country, MAX(day) as max_day
                FROM daily_metrics
                GROUP BY country
            ) latest ON dm.country = latest.country AND dm.day = latest.max_day
        """).fetchall()
        return {row["country"]: dict(row) for row in rows}

    # ---- News Archive ----

    def save_news_items(self, items: List[Any]):
        """Archive news items."""
        for item in items:
            self.conn.execute("""
                INSERT INTO news_archive
                (title, source_name, source_politics, source_credibility,
                 category, region, impact, url, content)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item.title, item.source.name, item.source.politics,
                item.source.credibility, item.category, item.region,
                item.impact, item.url, item.content[:1000],
            ))
        self.conn.commit()

    def search_news(self, category: Optional[str] = None, region: Optional[str] = None,
                    limit: int = 50) -> List[Dict]:
        """Search news archive with filters."""
        query = "SELECT * FROM news_archive WHERE 1=1"
        params: list = []
        if category:
            query += " AND category = ?"
            params.append(category)
        if region:
            query += " AND region = ?"
            params.append(region)
        query += " ORDER BY fetched_at DESC LIMIT ?"
        params.append(limit)
        rows = self.conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def get_news_stats(self) -> Dict:
        """Get news archive statistics."""
        row = self.conn.execute("""
            SELECT COUNT(*) as total,
                   COUNT(DISTINCT category) as categories,
                   COUNT(DISTINCT region) as regions,
                   MIN(fetched_at) as earliest,
                   MAX(fetched_at) as latest
            FROM news_archive
        """).fetchone()
        return dict(row)

    # ---- Simulation State ----

    def save_simulation_state(self, country: str, day: int, agent_count: int, summary: Dict):
        """Save simulation checkpoint for restart recovery."""
        self.conn.execute("""
            INSERT OR REPLACE INTO simulation_state
            (country, current_day, agent_count, state_json)
            VALUES (?, ?, ?, ?)
        """, (country, day, agent_count, json.dumps(summary)))
        self.conn.commit()

    def get_simulation_state(self, country: str) -> Optional[Dict]:
        """Get saved simulation state for a country."""
        row = self.conn.execute("""
            SELECT * FROM simulation_state WHERE country = ?
        """, (country,)).fetchone()
        return dict(row) if row else None

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None
