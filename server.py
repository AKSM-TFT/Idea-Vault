import os
import re
import json
import logging
import sys
from mcp.server.fastmcp import FastMCP

# Setup clean logging to stderr so it never corrupts the protocol channels
logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler(sys.stderr)])
logger = logging.getLogger("IdeasVault")

# Match the working demo's port structure (defaulting to 8080)
PORT = int(os.environ.get('PORT', 8080))
mcp = FastMCP("Ideas Vault Manager", port=PORT)

CONFIG_FILE = os.path.expanduser("~/.idea_vault_config.json")

def get_vault_dir() -> str:
    env_dir = os.environ.get("IDEA_VAULT_DIR")
    if env_dir:
        return env_dir

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                saved_dir = config.get("vault_dir")
                if saved_dir and os.path.exists(saved_dir):
                    return saved_dir
        except Exception:
            pass
            
    default_dir = os.path.expanduser("~/Idea-Vault/Vault")
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump({"vault_dir": default_dir}, f)
    except Exception:
        pass
        
    return default_dir

VAULT_DIR = get_vault_dir()
INDEX_FILE = os.path.join(VAULT_DIR, "00_index.md")

os.makedirs(VAULT_DIR, exist_ok=True)
if not os.path.exists(INDEX_FILE):
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write("# 💡 My Project Ideas Vault\n\nWelcome to your ideas index.\n\n")

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(re.compile(r'[^\w\s-]'), '', text)
    return re.sub(re.compile(r'[-\s]+'), '-', text) + ".md"

@mcp.tool()
def save_project_idea(title: str, content: str, brief_summary: str) -> str:
    """
    Saves a project idea to the Idea Vault as a Markdown file.

    Use this tool when the user says: save, store, remember, log, or add to vault.

    The `content` parameter MUST follow this exact Markdown structure:

    # <Title>

    ## Problem Statement
    What problem this solves and why it matters.

    ## Summary
    What the project is and how it works.

    ## Roles
    - Role Name — description of responsibilities
    - Role Name — description of responsibilities

    ## Payments
    - Payment method 1
    - Payment method 2

    ## Tech Stack
    - Technology 1, Technology 2, Technology 3

    ## Key Challenges
    - Challenge 1
    - Challenge 2

    ## Tags
    `tag-one` `tag-two` `tag-three`

    The `brief_summary` should be a single sentence describing the idea (used in the index).
    The `title` should be the plain project name without formatting.

    Always construct the full `content` string in this format before calling this tool.
    Never call this tool with a partial or freeform `content` value.
    """
    filename = slugify(title)
    file_path = os.path.join(VAULT_DIR, filename)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    with open(INDEX_FILE, "a", encoding="utf-8") as f:
        f.write(f"* **[{title}]({filename})**: {brief_summary}\n")

    return f"Success! Created '{filename}' and updated your central index."

@mcp.resource("file://ideas/index")
def get_ideas_index() -> str:
    """Provides the contents of the central 00_index.md file containing all logged ideas."""
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        return f.read()

@mcp.tool()
def read_specific_idea_file(filename: str) -> str:
    """Reads the contents of a specific idea markdown file from the vault."""
    clean_filename = os.path.basename(filename)
    file_path = os.path.join(VAULT_DIR, clean_filename)
    
    if not os.path.exists(file_path):
        return f"Error: File '{clean_filename}' not found in the vault."
        
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    logger.info(f"Starting Idea Vault MCP Server on port {PORT}...")
    try:
        # Explicitly run as an SSE transport server
        mcp.run(transport="sse")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        sys.exit(1)