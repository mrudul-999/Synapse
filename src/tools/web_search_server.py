# tools/web_search_server.py
#
# A minimal MCP server exposing one tool: web_search.
# Run standalone first to confirm it works before wiring it into LangGraph.

import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from tavily import TavilyClient

# Load TAVILY_API_KEY from .env
load_dotenv()

# Create the MCP server instance. The name shows up in MCP inspector/clients.
mcp = FastMCP("web-search")

# Create the Tavily client once, reused across calls.
tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])


@mcp.tool()
def web_search(query: str, max_results: int = 5) -> str:
    """
    Search the web for current information on a given query.

    Use this when you need up-to-date facts, news, or information
    that is not part of your training data.

    Args:
        query: The search query string.
        max_results: Max number of results to return (default 5).

    Returns:
        A formatted string of search results (title, url, snippet).
    """
    # Call Tavily's search API.
    response = tavily_client.search(query=query, max_results=max_results)

    # Format results into a single string the LLM can read.
    # (MCP tools return text/content blocks, not raw Python objects.)
    results = response.get("results", [])
    if not results:
        return f"No results found for query: {query}"

    formatted = []
    for r in results:
        formatted.append(
            f"Title: {r.get('title')}\n"
            f"URL: {r.get('url')}\n"
            f"Snippet: {r.get('content')}\n"
        )
    return "\n---\n".join(formatted)


if __name__ == "__main__":
    # stdio transport = the server runs as a subprocess your client spawns.
    # This is the right choice for local dev; you'd use http for a
    # server running independently (e.g. in Docker, reachable by URL).
    mcp.run(transport="stdio")