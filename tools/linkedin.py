"""
LinkedIn browser automation via Playwright.

WARNING: Automating LinkedIn violates their Terms of Service (Section 8.2).
This is provided for personal productivity only. Use responsibly and sparingly
to minimize account risk.
"""
import asyncio
import json
import os
import time
from pathlib import Path

_SESSION_FILE = Path(__file__).parent.parent / "linkedin_session.json"
_HEADLESS = True


async def _get_page():
    from playwright.async_api import async_playwright

    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=_HEADLESS)
    context = await browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    )

    if _SESSION_FILE.exists():
        cookies = json.loads(_SESSION_FILE.read_text())
        await context.add_cookies(cookies)
    else:
        email = os.getenv("LINKEDIN_EMAIL")
        password = os.getenv("LINKEDIN_PASSWORD")
        if not email or not password:
            await browser.close()
            await pw.stop()
            raise RuntimeError(
                "LINKEDIN_EMAIL and LINKEDIN_PASSWORD must be set in .env, "
                "or run python setup.py to log in interactively."
            )
        login_page = await context.new_page()
        await login_page.goto("https://www.linkedin.com/login")
        await login_page.fill("#username", email)
        await login_page.fill("#password", password)
        await login_page.click('button[type="submit"]')
        await login_page.wait_for_url("**/feed/**", timeout=15000)
        cookies = await context.cookies()
        _SESSION_FILE.write_text(json.dumps(cookies))
        await login_page.close()

    page = await context.new_page()
    return pw, browser, context, page


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


async def _search_people_async(query: str, max_results: int = 5) -> str:
    pw, browser, context, page = await _get_page()
    try:
        url = f"https://www.linkedin.com/search/results/people/?keywords={query.replace(' ', '%20')}"
        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)

        cards = await page.query_selector_all(".entity-result__item")
        results = []
        for card in cards[:max_results]:
            name_el = await card.query_selector(".entity-result__title-text")
            subtitle_el = await card.query_selector(".entity-result__primary-subtitle")
            secondary_el = await card.query_selector(".entity-result__secondary-subtitle")
            link_el = await card.query_selector("a.app-aware-link")

            name = await name_el.inner_text() if name_el else "Unknown"
            subtitle = await subtitle_el.inner_text() if subtitle_el else ""
            secondary = await secondary_el.inner_text() if secondary_el else ""
            href = await link_el.get_attribute("href") if link_el else ""

            results.append(
                f"Name: {name.strip()}\n"
                f"Title: {subtitle.strip()}\n"
                f"Location: {secondary.strip()}\n"
                f"Profile: {href.split('?')[0] if href else 'N/A'}"
            )

        cookies = await context.cookies()
        _SESSION_FILE.write_text(json.dumps(cookies))
        return "\n\n".join(results) if results else "No people found."
    finally:
        await browser.close()
        await pw.stop()


async def _search_jobs_async(query: str, location: str = "", max_results: int = 5) -> str:
    pw, browser, context, page = await _get_page()
    try:
        loc_param = f"&location={location.replace(' ', '%20')}" if location else ""
        url = f"https://www.linkedin.com/jobs/search/?keywords={query.replace(' ', '%20')}{loc_param}"
        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)

        cards = await page.query_selector_all(".jobs-search__results-list li")
        results = []
        for card in cards[:max_results]:
            title_el = await card.query_selector("h3")
            company_el = await card.query_selector("h4")
            location_el = await card.query_selector(".job-search-card__location")
            link_el = await card.query_selector("a.base-card__full-link")

            title = await title_el.inner_text() if title_el else "Unknown"
            company = await company_el.inner_text() if company_el else ""
            loc = await location_el.inner_text() if location_el else ""
            href = await link_el.get_attribute("href") if link_el else ""

            results.append(
                f"Title: {title.strip()}\n"
                f"Company: {company.strip()}\n"
                f"Location: {loc.strip()}\n"
                f"Link: {href.split('?')[0] if href else 'N/A'}"
            )

        cookies = await context.cookies()
        _SESSION_FILE.write_text(json.dumps(cookies))
        return "\n\n".join(results) if results else "No jobs found."
    finally:
        await browser.close()
        await pw.stop()


async def _get_profile_async(profile_url: str) -> str:
    pw, browser, context, page = await _get_page()
    try:
        if not profile_url.startswith("http"):
            profile_url = f"https://www.linkedin.com/in/{profile_url}"
        await page.goto(profile_url, wait_until="domcontentloaded")
        await page.wait_for_timeout(2500)

        name_el = await page.query_selector("h1")
        headline_el = await page.query_selector(".text-body-medium.break-words")
        about_el = await page.query_selector("#about ~ div .display-flex span[aria-hidden='true']")

        name = await name_el.inner_text() if name_el else "Unknown"
        headline = await headline_el.inner_text() if headline_el else ""
        about = await about_el.inner_text() if about_el else ""

        experience_items = await page.query_selector_all("#experience ~ div .pvs-list__item--line-separated")
        exp_lines = []
        for item in experience_items[:5]:
            text_el = await item.query_selector("span[aria-hidden='true']")
            if text_el:
                exp_lines.append((await text_el.inner_text()).strip())

        cookies = await context.cookies()
        _SESSION_FILE.write_text(json.dumps(cookies))

        return (
            f"Name: {name.strip()}\n"
            f"Headline: {headline.strip()}\n"
            f"About: {about.strip()[:500]}\n"
            f"Experience:\n" + "\n".join(f"  - {e}" for e in exp_lines)
        )
    finally:
        await browser.close()
        await pw.stop()


def search_linkedin_people(query: str, max_results: int = 5) -> str:
    """Search LinkedIn for people by name, title, or keyword."""
    return _run(_search_people_async(query, max_results))


def search_linkedin_jobs(query: str, location: str = "", max_results: int = 5) -> str:
    """Search LinkedIn job postings."""
    return _run(_search_jobs_async(query, location, max_results))


def get_linkedin_profile(profile_url_or_slug: str) -> str:
    """Get details from a LinkedIn profile URL or username slug."""
    return _run(_get_profile_async(profile_url_or_slug))
