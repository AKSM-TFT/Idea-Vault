# Idea Vault — MCP Server

> A Model Context Protocol (MCP) server for saving, browsing, and managing project ideas — backed by PostgreSQL and deployable to Railway.

---

## What Is This?

**Idea Vault** is a lightweight MCP server that gives AI assistants (like Claude) persistent memory for your project ideas. Instead of ideas getting lost in conversation history, they're stored in a structured PostgreSQL database and can be saved, listed, read, or deleted via natural language commands.

Each idea is stored with a title, slug, structured markdown content, and a brief summary — making it easy to browse and retrieve later.

---

## Features

- **Save ideas** — Store project concepts with a structured markdown template (problem statement, tech stack, roles, payments, challenges, tags)
- **List ideas** — Browse an index of all saved ideas with summaries and dates
- **Read ideas** — Retrieve the full content of any idea by its slug
- **Delete ideas** — Remove ideas from the vault
- **PostgreSQL-backed** — Persistent storage with `UPSERT` support (re-saving updates the existing entry)
- **Railway-ready** — Designed to deploy in one click with a managed Postgres addon

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Runtime | Python 3.x |
| MCP Framework | [`mcp`](https://pypi.org/project/mcp/) v1.28.0 (FastMCP / SSE transport) |
| Database | PostgreSQL via `psycopg2` v2.9.12 |
| Deployment | Railway (Procfile-based) |
| Protocol | Model Context Protocol (SSE) |

---

## Deploy on Railway

### Prerequisites
- A [Railway](https://railway.app) account
- This repository pushed to GitHub

### Steps

1. **Create a new Railway project** from your GitHub repo:
   - Go to [railway.app/new](https://railway.app/new)
   - Select **Deploy from GitHub repo** and pick this repository

2. **Add a PostgreSQL database**:
   - In your Railway project, click **+ New** → **Database** → **Add PostgreSQL**
   - Railway will automatically inject a `DATABASE_URL` environment variable into your service

3. **Set environment variables** (if not auto-injected):
   ```
   DATABASE_URL=postgresql://user:password@host:port/dbname
   PORT=8080
   ```

4. **Deploy** — Railway will detect the `Procfile` and run:
   ```
   web: python server.py
   ```

5. **Copy your public URL** from the Railway dashboard (e.g. `https://idea-vault-production.up.railway.app`).

### Connecting to Claude (or any MCP client)

Add the server to your MCP client config using the SSE endpoint:

```json
{
  "mcpServers": {
    "idea-vault": {
      "url": "https://your-railway-url.up.railway.app/sse"
    }
  }
}
```

> The database table is auto-created on first run via `init_db()` — no manual migrations needed.

---

## 🖥 Frontend

A companion web frontend for browsing and managing your Idea Vault visually is available here:

**[Idea Vault Frontend — GitHub](https://github.com/AKSM-TFT/Idea-Vault-Web)**

---

## Project Structure

```
idea-vault/
├── server.py          # MCP server — all tools and DB logic
├── requirements.txt   # Python dependencies
├── Procfile           # Railway process definition
└── README.md
```

---

## Idea Content Structure

When saving an idea, the `content` field must follow this markdown template:

```markdown
# Project Title

## Problem Statement
What problem this solves and why it matters.

## Summary
What the project is and how it works.

## Roles
- Role Name — description of responsibilities

## Payments
- Payment method

## Tech Stack
- Technology 1, Technology 2

## Key Challenges
- Challenge 1

## Tags
`tag-one` `tag-two` `tag-three`
```

---

## License

MIT
