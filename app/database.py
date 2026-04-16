import sqlite3

from flask import g, current_app


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app):
    with app.app_context():
        db = get_db()
        db.executescript("""
            CREATE TABLE IF NOT EXISTS tables (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS columns (
                id TEXT PRIMARY KEY,
                table_id TEXT NOT NULL,
                name TEXT NOT NULL,
                type TEXT NOT NULL CHECK (type IN ('string', 'number', 'boolean')),
                position INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (table_id) REFERENCES tables(id) ON DELETE CASCADE,
                UNIQUE (table_id, name)
            );

            CREATE TABLE IF NOT EXISTS rows (
                id TEXT PRIMARY KEY,
                table_id TEXT NOT NULL,
                data TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (table_id) REFERENCES tables(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_columns_table_id ON columns(table_id);
            CREATE INDEX IF NOT EXISTS idx_rows_table_id ON rows(table_id);
        """)
        db.commit()
        close_db()
