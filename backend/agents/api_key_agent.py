"""
Playwright MCP Agent — Autonomous API Key Registration.

Uses Playwright (via MCP) to navigate API portals, fill signup forms,
and extract API keys. Saves keys to .env file.

Prerequisites:
  - Claude Code with Playwright MCP server configured
  - Google Chrome / Chromium installed
  - GOOGLE_EMAIL env var set for OAuth flows

Usage:
  python -m agents.api_key_agent

This is designed to be run interactively with Claude Code MCP,
not as a standalone script. The agent loop requires Claude API access.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
LOG_DIR = PROJECT_ROOT / "backend" / "docs" / "api_specs"

# API portals that need registration
API_PORTALS = [
    {
        "name": "fred",
        "url": "https://fred.stlouisfed.org/docs/api/api_key.html",
        "env_key": "FRED_API_KEY",
        "method": "form_signup",
        "notes": "Fill email + name, key shown on page after confirmation",
    },
    {
        "name": "eia",
        "url": "https://www.eia.gov/opendata/register.php",
        "env_key": "EIA_API_KEY",
        "method": "form_signup",
        "notes": "Email + org name, key sent via email",
    },
    {
        "name": "alpha_vantage",
        "url": "https://www.alphavantage.co/support/#api-key",
        "env_key": "ALPHA_VANTAGE_API_KEY",
        "method": "simple_form",
        "notes": "Just email, key shown immediately",
    },
    {
        "name": "iex_cloud",
        "url": "https://iexcloud.io/cloud-login#/register",
        "env_key": "IEX_CLOUD_API_KEY",
        "method": "google_oauth",
        "notes": "Google OAuth signup, key in dashboard",
    },
    {
        "name": "companies_house",
        "url": "https://developer.company-information.service.gov.uk/",
        "env_key": "COMPANIES_HOUSE_API_KEY",
        "method": "form_signup",
        "notes": "UK gov portal, email + app name",
    },
    {
        "name": "libraries_io",
        "url": "https://libraries.io/login",
        "env_key": "LIBRARIES_IO_API_KEY",
        "method": "github_oauth",
        "notes": "Login with GitHub, key in settings",
    },
    {
        "name": "the_news_api",
        "url": "https://www.thenewsapi.com/account/register",
        "env_key": "THE_NEWS_API_KEY",
        "method": "google_oauth",
        "notes": "Google OAuth, key in dashboard",
    },
    {
        "name": "builtwith",
        "url": "https://api.builtwith.com/",
        "env_key": "BUILTWITH_API_KEY",
        "method": "form_signup",
        "notes": "Free tier, email signup",
    },
    {
        "name": "bls",
        "url": "https://data.bls.gov/registrationEngine/",
        "env_key": "BLS_API_KEY",
        "method": "form_signup",
        "notes": "Email + org, key sent via email",
    },
]


def save_key_to_env(env_key: str, value: str) -> None:
    """Append or update an API key in the .env file."""
    if not ENV_FILE.exists():
        ENV_FILE.write_text(f"{env_key}={value}\n")
        return

    lines = ENV_FILE.read_text().splitlines()
    updated = False
    for i, line in enumerate(lines):
        if line.startswith(f"{env_key}="):
            lines[i] = f"{env_key}={value}"
            updated = True
            break

    if not updated:
        lines.append(f"{env_key}={value}")

    ENV_FILE.write_text("\n".join(lines) + "\n")
    logger.info("Saved %s to .env", env_key)


def get_pending_portals() -> list[dict]:
    """Return portals that don't have a key set yet."""
    pending = []
    for portal in API_PORTALS:
        current = os.environ.get(portal["env_key"], "")
        if not current:
            pending.append(portal)
    return pending


def generate_mcp_config() -> dict:
    """Generate MCP config for Playwright server."""
    return {
        "mcpServers": {
            "playwright": {
                "command": "npx",
                "args": ["-y", "@anthropic-ai/mcp-playwright"],
                "env": {
                    "PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH": os.environ.get(
                        "PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH",
                        "/usr/bin/google-chrome",
                    )
                },
            }
        }
    }


def save_run_log(results: list[dict]) -> Path:
    """Save execution log."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"agent_run_{timestamp}.json"
    log_path.write_text(json.dumps({
        "timestamp": timestamp,
        "results": results,
        "total": len(results),
        "success": sum(1 for r in results if r.get("status") == "ok"),
    }, indent=2))
    return log_path


# ── CLI Entry Point ──

if __name__ == "__main__":
    pending = get_pending_portals()
    if not pending:
        print("All API keys are already configured!")
    else:
        print(f"\n{len(pending)} API keys missing:\n")
        for p in pending:
            print(f"  - {p['name']:20s} | {p['env_key']:30s} | {p['method']}")
        print(f"\nTo register automatically, run this with Claude Code MCP.")
        print(f"MCP config: {json.dumps(generate_mcp_config(), indent=2)}")
