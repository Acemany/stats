#!/usr/bin/python3

from asyncio import gather, run
from os import getenv, path, mkdir

from aiohttp import ClientSession

from github_stats import Stats


async def generate_overview(s: Stats) -> None:
    """
    Generate an SVG badge with summary statistics
    :param s: Represents user's GitHub statistics
    """
    with open('templates/overview.svg', 'r', encoding='utf-8') as f:
        output = f.read()

    output = output\
        .replace("{{ name }}", await s.name)\
        .replace("{{ stars }}", f"{await s.stargazers:,}")\
        .replace("{{ forks }}", f"{await s.forks:,}")\
        .replace("{{ contributions }}", f"{await s.total_contributions:,}")\
        .replace("{{ lines_changed }}", f"{sum(await s.lines_changed):,}")\
        .replace("{{ views }}", f"{await s.views:,}")\
        .replace("{{ repos }}", f"{len(await s.repos):,}")

    with open('generated/overview.svg', 'w', encoding='utf-8') as f:
        f.write(output)


async def generate_languages(s: Stats) -> None:
    """
    Generate an SVG badge with summary languages used
    :param s: Represents user's GitHub statistics
    """
    with open('templates/languages.svg', 'r', encoding='utf-8') as f:
        output = f.read()

    progress = ""
    lang_list = ""
    sorted_languages = sorted(
        (await s.languages).items(),
        reverse=True,
        key=lambda t: t[1].get("size")
    )
    delay_between = 150
    for i, (lang, data) in enumerate(sorted_languages):
        color = data.get("color")
        color = color if color is not None else "#000000"
        progress += (
            f'<span style="background-color: {color};'
            f'width: {data.get("prop", 0):0.3f}%;" '
            f'class="progress-item"></span>'
        )
        lang_list += f"""
<li style="animation-delay: {i * delay_between}ms;">
<svg xmlns="http://www.w3.org/2000/svg" class="octicon" style="fill:{color};"
viewBox="0 0 16 16" version="1.1" width="16" height="16"><path
fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8z"></path></svg>
<span class="lang">{lang}</span>
<span class="percent">{data.get("prop", 0):0.2f}%</span>
</li>

"""

    output = output\
        .replace(r"{{ progress }}", progress)\
        .replace(r"{{ lang_list }}", lang_list)

    with open('generated/languages.svg', 'w', encoding='utf-8') as f:
        f.write(output)


async def main() -> None:
    """
    Generate all badges
    """
    access_token = getenv("ACCESS_TOKEN")
    if not access_token:
        # access_token = getenv("GITHUB_TOKEN")
        raise ValueError("A personal access token is required to proceed!")
    user = getenv("GITHUB_ACTOR")
    if user is None:
        raise RuntimeError("Environment variable GITHUB_ACTOR must be set.")
    exclude_repos = getenv("EXCLUDED")
    excluded_repos = (
        {x.strip() for x in exclude_repos.split(",")} if exclude_repos else None
    )
    exclude_langs = getenv("EXCLUDED_LANGS")
    excluded_langs = (
        {x.strip() for x in exclude_langs.split(",")} if exclude_langs else None
    )
    # Convert a truthy value to a Boolean
    raw_ignore_forked_repos = getenv("EXCLUDE_FORKED_REPOS")
    ignore_forked_repos = not not\
        raw_ignore_forked_repos and raw_ignore_forked_repos.strip().lower() != "false"

    if not path.isdir("generated"):
        mkdir("generated")

    async with ClientSession() as session:
        s = Stats(
            user,
            access_token,
            session,
            exclude_repos=excluded_repos,
            exclude_langs=excluded_langs,
            ignore_forked_repos=ignore_forked_repos,
        )
        await gather(generate_languages(s), generate_overview(s))


if __name__ == "__main__":
    run(main())
