from duckduckgo_search import DDGS


def search_web(query: str, max_results: int = 5) -> str:
    """Search the web using DuckDuckGo."""
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=max_results))

    if not results:
        return "No results found."

    lines = []
    for r in results:
        lines.append(f"Title: {r.get('title', '')}\nURL: {r.get('href', '')}\nSummary: {r.get('body', '')}\n")

    return "\n".join(lines)
