#!/usr/bin/env python3
"""
Migrate data from SQLite to PostgreSQL for Open WebUI
Handles schema differences between older SQLite and newer PostgreSQL versions
"""

import sqlite3
import psycopg2
import sys
import os
from datetime import datetime

SQLITE_DB = "webui.db"
POSTGRES_HOST = "localhost"
POSTGRES_PORT = "5432"
POSTGRES_DB = "openwebui"
POSTGRES_USER = "openwebui_user"
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD")

if not POSTGRES_PASSWORD:
    print("ERROR: POSTGRES_PASSWORD environment variable not set")
    print("Usage: POSTGRES_PASSWORD='your_password' python3 migrate_sqlite_to_postgres.py")
    sys.exit(1)

def connect_sqlite():
    """Connect to SQLite database"""
    conn = sqlite3.connect(SQLITE_DB)
    conn.row_factory = sqlite3.Row
    return conn

def connect_postgres():
    """Connect to PostgreSQL database"""
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )
    return conn

def migrate_auth(sqlite_conn, pg_conn):
    """Migrate auth table"""
    print("Migrating auth table...")
    sqlite_cur = sqlite_conn.cursor()
    pg_cur = pg_conn.cursor()

    sqlite_cur.execute("SELECT id, email, password, active FROM auth")
    rows = sqlite_cur.fetchall()

    for row in rows:
        active = bool(row['active']) if row['active'] is not None else True
        pg_cur.execute(
            "INSERT INTO auth (id, email, password, active) VALUES (%s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
            (row['id'], row['email'], row['password'], active)
        )

    pg_conn.commit()
    print(f"  Migrated {len(rows)} auth records")

def migrate_user(sqlite_conn, pg_conn):
    """Migrate user table"""
    print("Migrating user table...")
    sqlite_cur = sqlite_conn.cursor()
    pg_cur = pg_conn.cursor()

    sqlite_cur.execute("SELECT * FROM user")
    rows = sqlite_cur.fetchall()

    for row in rows:
        pg_cur.execute(
            """INSERT INTO "user" (id, name, email, role, profile_image_url,
               last_active_at, updated_at, created_at, api_key, settings, info, oauth_sub)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (id) DO NOTHING""",
            (
                row['id'], row['name'], row['email'], row['role'],
                row['profile_image_url'], row['last_active_at'], row['updated_at'],
                row['created_at'], row['api_key'], row['settings'], row['info'],
                row['oauth_sub'] if 'oauth_sub' in row.keys() else None
            )
        )

    pg_conn.commit()
    print(f"  Migrated {len(rows)} user records")

def migrate_chat(sqlite_conn, pg_conn):
    """Migrate chat table"""
    print("Migrating chat table...")
    sqlite_cur = sqlite_conn.cursor()
    pg_cur = pg_conn.cursor()

    sqlite_cur.execute("SELECT * FROM chat")
    rows = sqlite_cur.fetchall()

    for row in rows:
        archived = bool(row['archived']) if row['archived'] is not None else False
        pinned = bool(row['pinned']) if 'pinned' in row.keys() and row['pinned'] is not None else False

        pg_cur.execute(
            """INSERT INTO chat (id, user_id, title, chat, archived, created_at,
               updated_at, share_id, pinned, meta, folder_id)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (id) DO NOTHING""",
            (
                row['id'], row['user_id'], row['title'], row['chat'],
                archived, row['created_at'], row['updated_at'],
                row['share_id'] if 'share_id' in row.keys() else None,
                pinned,
                row['meta'] if 'meta' in row.keys() else None,
                row['folder_id'] if 'folder_id' in row.keys() else None
            )
        )

    pg_conn.commit()
    print(f"  Migrated {len(rows)} chat records")

def migrate_document(sqlite_conn, pg_conn):
    """Migrate document table (handle schema difference - no id column in postgres)"""
    print("Migrating document table...")
    sqlite_cur = sqlite_conn.cursor()
    pg_cur = pg_conn.cursor()

    sqlite_cur.execute("SELECT collection_name, name, title, filename, content, user_id, timestamp FROM document")
    rows = sqlite_cur.fetchall()

    for row in rows:
        pg_cur.execute(
            """INSERT INTO document (collection_name, name, title, filename, content, user_id, timestamp)
               VALUES (%s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (collection_name) DO NOTHING""",
            (
                row['collection_name'], row['name'], row['title'],
                row['filename'], row['content'], row['user_id'], row['timestamp']
            )
        )

    pg_conn.commit()
    print(f"  Migrated {len(rows)} document records")

def migrate_tag(sqlite_conn, pg_conn):
    """Migrate tag table"""
    print("Migrating tag table...")
    sqlite_cur = sqlite_conn.cursor()
    pg_cur = pg_conn.cursor()

    sqlite_cur.execute("SELECT * FROM tag")
    rows = sqlite_cur.fetchall()

    for row in rows:
        # Handle optional columns
        tag_id = row['id']
        tag_name = row['name']
        user_id = row['user_id'] if 'user_id' in row.keys() else None
        # PostgreSQL uses 'meta' instead of 'data'
        meta = row['data'] if 'data' in row.keys() else (row['meta'] if 'meta' in row.keys() else None)

        pg_cur.execute(
            """INSERT INTO tag (id, name, user_id, meta)
               VALUES (%s, %s, %s, %s)
               ON CONFLICT (id, user_id) DO NOTHING""",
            (tag_id, tag_name, user_id, meta)
        )

    pg_conn.commit()
    print(f"  Migrated {len(rows)} tag records")

def migrate_chatidtag(sqlite_conn, pg_conn):
    """Migrate chatidtag table"""
    print("Migrating chatidtag table...")
    sqlite_cur = sqlite_conn.cursor()
    pg_cur = pg_conn.cursor()

    sqlite_cur.execute("SELECT * FROM chatidtag")
    rows = sqlite_cur.fetchall()

    for row in rows:
        # Handle optional columns
        timestamp = row['timestamp'] if 'timestamp' in row.keys() else None

        pg_cur.execute(
            """INSERT INTO chatidtag (id, tag_name, chat_id, user_id, timestamp)
               VALUES (%s, %s, %s, %s, %s)
               ON CONFLICT (id) DO NOTHING""",
            (row['id'], row['tag_name'], row['chat_id'], row['user_id'], timestamp)
        )

    pg_conn.commit()
    print(f"  Migrated {len(rows)} chatidtag records")

def migrate_file(sqlite_conn, pg_conn):
    """Migrate file table"""
    print("Migrating file table...")
    sqlite_cur = sqlite_conn.cursor()
    pg_cur = pg_conn.cursor()

    try:
        sqlite_cur.execute("SELECT * FROM file")
        rows = sqlite_cur.fetchall()

        for row in rows:
            pg_cur.execute(
                """INSERT INTO file (id, user_id, hash, filename, data, meta, created_at, updated_at, path)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT (id) DO NOTHING""",
                (
                    row['id'],
                    row['user_id'] if 'user_id' in row.keys() else None,
                    row['hash'] if 'hash' in row.keys() else None,
                    row['filename'] if 'filename' in row.keys() else None,
                    row['data'] if 'data' in row.keys() else None,
                    row['meta'] if 'meta' in row.keys() else None,
                    row['created_at'] if 'created_at' in row.keys() else None,
                    row['updated_at'] if 'updated_at' in row.keys() else None,
                    row['path'] if 'path' in row.keys() else None
                )
            )

        pg_conn.commit()
        print(f"  Migrated {len(rows)} file records")
    except Exception as e:
        print(f"  Warning: Could not migrate file table: {e}")
        print(f"  Skipping file table...")

def migrate_model(sqlite_conn, pg_conn):
    """Migrate model table"""
    print("Migrating model table...")
    sqlite_cur = sqlite_conn.cursor()
    pg_cur = pg_conn.cursor()

    try:
        sqlite_cur.execute("SELECT * FROM model")
        rows = sqlite_cur.fetchall()

        for row in rows:
            is_active = bool(row['is_active']) if 'is_active' in row.keys() and row['is_active'] is not None else True

            pg_cur.execute(
                """INSERT INTO model (id, user_id, base_model_id, name, params, meta,
                   updated_at, created_at, is_active, access_control)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT (id) DO NOTHING""",
                (
                    row['id'],
                    row['user_id'] if 'user_id' in row.keys() else None,
                    row['base_model_id'] if 'base_model_id' in row.keys() else None,
                    row['name'] if 'name' in row.keys() else None,
                    row['params'] if 'params' in row.keys() else None,
                    row['meta'] if 'meta' in row.keys() else None,
                    row['updated_at'] if 'updated_at' in row.keys() else None,
                    row['created_at'] if 'created_at' in row.keys() else None,
                    is_active,
                    row['access_control'] if 'access_control' in row.keys() else None
                )
            )

        pg_conn.commit()
        print(f"  Migrated {len(rows)} model records")
    except Exception as e:
        print(f"  Warning: Could not migrate model table: {e}")
        print(f"  Skipping model table...")

def migrate_prompt(sqlite_conn, pg_conn):
    """Migrate prompt table"""
    print("Migrating prompt table...")
    sqlite_cur = sqlite_conn.cursor()
    pg_cur = pg_conn.cursor()

    try:
        sqlite_cur.execute("SELECT * FROM prompt")
        rows = sqlite_cur.fetchall()

        for row in rows:
            pg_cur.execute(
                """INSERT INTO prompt (command, user_id, title, content, timestamp)
                   VALUES (%s, %s, %s, %s, %s)
                   ON CONFLICT (command) DO NOTHING""",
                (
                    row['command'],
                    row['user_id'] if 'user_id' in row.keys() else None,
                    row['title'] if 'title' in row.keys() else None,
                    row['content'] if 'content' in row.keys() else None,
                    row['timestamp'] if 'timestamp' in row.keys() else None
                )
            )

        pg_conn.commit()
        print(f"  Migrated {len(rows)} prompt records")
    except Exception as e:
        print(f"  Warning: Could not migrate prompt table: {e}")
        print(f"  Skipping prompt table...")

def migrate_tool(sqlite_conn, pg_conn):
    """Migrate tool table"""
    print("Migrating tool table...")
    sqlite_cur = sqlite_conn.cursor()
    pg_cur = pg_conn.cursor()

    try:
        sqlite_cur.execute("SELECT * FROM tool")
        rows = sqlite_cur.fetchall()

        for row in rows:
            pg_cur.execute(
                """INSERT INTO tool (id, user_id, name, content, specs, meta,
                   valves, updated_at, created_at, access_control)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT (id) DO NOTHING""",
                (
                    row['id'],
                    row['user_id'] if 'user_id' in row.keys() else None,
                    row['name'] if 'name' in row.keys() else None,
                    row['content'] if 'content' in row.keys() else None,
                    row['specs'] if 'specs' in row.keys() else None,
                    row['meta'] if 'meta' in row.keys() else None,
                    row['valves'] if 'valves' in row.keys() else None,
                    row['updated_at'] if 'updated_at' in row.keys() else None,
                    row['created_at'] if 'created_at' in row.keys() else None,
                    row['access_control'] if 'access_control' in row.keys() else None
                )
            )

        pg_conn.commit()
        print(f"  Migrated {len(rows)} tool records")
    except Exception as e:
        print(f"  Warning: Could not migrate tool table: {e}")
        print(f"  Skipping tool table...")

def migrate_knowledge(sqlite_conn, pg_conn):
    """Migrate knowledge table"""
    print("Migrating knowledge table...")
    sqlite_cur = sqlite_conn.cursor()
    pg_cur = pg_conn.cursor()

    try:
        sqlite_cur.execute("SELECT * FROM knowledge")
        rows = sqlite_cur.fetchall()

        for row in rows:
            pg_cur.execute(
                """INSERT INTO knowledge (id, user_id, name, description, data,
                   meta, updated_at, created_at, access_control)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT (id) DO NOTHING""",
                (
                    row['id'],
                    row['user_id'] if 'user_id' in row.keys() else None,
                    row['name'] if 'name' in row.keys() else None,
                    row['description'] if 'description' in row.keys() else None,
                    row['data'] if 'data' in row.keys() else None,
                    row['meta'] if 'meta' in row.keys() else None,
                    row['updated_at'] if 'updated_at' in row.keys() else None,
                    row['created_at'] if 'created_at' in row.keys() else None,
                    row['access_control'] if 'access_control' in row.keys() else None
                )
            )

        pg_conn.commit()
        print(f"  Migrated {len(rows)} knowledge records")
    except Exception as e:
        print(f"  Warning: Could not migrate knowledge table: {e}")
        print(f"  Skipping knowledge table...")

def migrate_function(sqlite_conn, pg_conn):
    """Migrate function table"""
    print("Migrating function table...")
    sqlite_cur = sqlite_conn.cursor()
    pg_cur = pg_conn.cursor()

    try:
        sqlite_cur.execute("SELECT * FROM function")
        rows = sqlite_cur.fetchall()

        for row in rows:
            is_active = bool(row['is_active']) if 'is_active' in row.keys() and row['is_active'] is not None else True
            is_global = bool(row['is_global']) if 'is_global' in row.keys() and row['is_global'] is not None else False

            pg_cur.execute(
                """INSERT INTO function (id, user_id, name, type, content, meta,
                   is_active, is_global, updated_at, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT (id) DO NOTHING""",
                (
                    row['id'],
                    row['user_id'] if 'user_id' in row.keys() else None,
                    row['name'] if 'name' in row.keys() else None,
                    row['type'] if 'type' in row.keys() else None,
                    row['content'] if 'content' in row.keys() else None,
                    row['meta'] if 'meta' in row.keys() else None,
                    is_active,
                    is_global,
                    row['updated_at'] if 'updated_at' in row.keys() else None,
                    row['created_at'] if 'created_at' in row.keys() else None
                )
            )

        pg_conn.commit()
        print(f"  Migrated {len(rows)} function records")
    except Exception as e:
        print(f"  Warning: Could not migrate function table: {e}")
        print(f"  Skipping function table...")

def main():
    """Main migration function"""
    print("=" * 60)
    print("Open WebUI SQLite to PostgreSQL Migration")
    print("=" * 60)
    print()

    if not os.path.exists(SQLITE_DB):
        print(f"ERROR: SQLite database '{SQLITE_DB}' not found")
        print("Make sure webui.db is in the current directory")
        sys.exit(1)

    print(f"SQLite database: {SQLITE_DB}")
    print(f"PostgreSQL: {POSTGRES_USER}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")
    print()

    try:
        sqlite_conn = connect_sqlite()
        pg_conn = connect_postgres()

        print("Connected to both databases successfully!")
        print()

        # Migrate tables in order (respecting foreign key constraints)
        migrate_auth(sqlite_conn, pg_conn)
        migrate_user(sqlite_conn, pg_conn)
        migrate_chat(sqlite_conn, pg_conn)
        migrate_tag(sqlite_conn, pg_conn)
        migrate_chatidtag(sqlite_conn, pg_conn)
        migrate_document(sqlite_conn, pg_conn)
        migrate_file(sqlite_conn, pg_conn)
        migrate_model(sqlite_conn, pg_conn)
        migrate_prompt(sqlite_conn, pg_conn)
        migrate_tool(sqlite_conn, pg_conn)
        migrate_knowledge(sqlite_conn, pg_conn)
        migrate_function(sqlite_conn, pg_conn)

        print()
        print("=" * 60)
        print("Migration completed successfully!")
        print("=" * 60)

        sqlite_conn.close()
        pg_conn.close()

    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        sys.exit(1)
    except psycopg2.Error as e:
        print(f"PostgreSQL error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
