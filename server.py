import os
import re
import json
import logging
import sys
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler(sys.stderr)])
logger = logging.getLogger("IdeasVault")

PORT = int(os.environ.get('PORT', 8080))
mcp = FastMCP("Ideas Vault Manager", port=PORT)

DATABASE_URL = os.environ.get("DATABASE_URL")


def get_db():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ideas (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL UNIQUE,
            slug TEXT NOT NULL UNIQUE,
            content TEXT NOT NULL,
            brief_summary TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()
    cur.close()
    conn.close()
    logger.info("Database initialized.")


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(re.compile(r'[^\w\s-]'), '', text)
    return re.sub(re.compile(r'[-\s]+'), '-', text)


@mcp.tool()
def save_project_idea(title: str, content: str, brief_summary: str) -> str:
    """
    Saves a project idea to the Idea Vault in a PostgreSQL database.

    Use this tool when the user says: save, store, remember, log, or add to vault.

    The `content` parameter MUST follow this exact Markdown structure:

    # <Title>

    ## Problem Statement
    What problem this solves and why it matters.

    ## Summary
    What the project is and how it works.

    ## Roles
    - Role Name — description of responsibilities

    ## Payments
    - Payment method 1

    ## Tech Stack
    - Technology 1, Technology 2

    ## Key Challenges
    - Challenge 1

    ## Tags
    `tag-one` `tag-two` `tag-three`

    The `brief_summary` should be a single sentence (used in the index).
    The `title` should be the plain project name without formatting.

    Always construct the full `content` string in this format before calling this tool.
    Never call this tool with a partial or freeform `content` value.
    """
    slug = slugify(title)
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO ideas (title, slug, content, brief_summary)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (slug) DO UPDATE
            SET content = EXCLUDED.content,
                brief_summary = EXCLUDED.brief_summary,
                updated_at = NOW()
        """, (title, slug, content, brief_summary))
        conn.commit()
        return f"Success! Idea '{title}' saved to the vault."
    except Exception as e:
        conn.rollback()
        return f"Error saving idea: {str(e)}"
    finally:
        cur.close()
        conn.close()


@mcp.tool()
def list_ideas() -> str:
    """
    Lists all saved ideas in the Idea Vault.
    Returns a summary index of all ideas including title, slug, brief summary, and date saved.
    Use this when the user asks to see, list, or browse their saved ideas.
    """
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT title, slug, brief_summary, created_at FROM ideas ORDER BY created_at DESC")
        rows = cur.fetchall()
        if not rows:
            return "No ideas saved yet."
        index = "# 💡 Idea Vault Index\n\n"
        for row in rows:
            date = row['created_at'].strftime("%b %d, %Y")
            index += f"- **{row['title']}** (`{row['slug']}`): {row['brief_summary']} — _{date}_\n"
        return index
    finally:
        cur.close()
        conn.close()


@mcp.tool()
def read_idea(slug: str) -> str:
    """
    Reads the full content of a specific idea from the Idea Vault by its slug.
    Use this when the user wants to view, read, or retrieve a specific saved idea.
    The slug is the hyphenated lowercase version of the title (e.g. 'water-station-delivery-pos-system').
    """
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT title, content, created_at FROM ideas WHERE slug = %s", (slug,))
        row = cur.fetchone()
        if not row:
            return f"Error: No idea found with slug '{slug}'. Use list_ideas to see available ideas."
        return row['content']
    finally:
        cur.close()
        conn.close()


@mcp.tool()
def delete_idea(slug: str) -> str:
    """
    Deletes a specific idea from the Idea Vault by its slug.
    Use this when the user asks to remove or delete a saved idea.
    The slug is the hyphenated lowercase version of the title.
    Always confirm with the user before deleting.
    """
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM ideas WHERE slug = %s RETURNING title", (slug,))
        row = cur.fetchone()
        conn.commit()
        if not row:
            return f"Error: No idea found with slug '{slug}'."
        return f"Idea '{row['title']}' deleted from the vault."
    except Exception as e:
        conn.rollback()
        return f"Error deleting idea: {str(e)}"
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    init_db()
    logger.info(f"Starting Idea Vault MCP Server on port {PORT}...")
    try:
        mcp.run(transport="sse")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        sys.exit(1)