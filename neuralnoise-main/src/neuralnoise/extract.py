import asyncio
import logging
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from textwrap import dedent
from typing import AsyncIterator

import requests  # type: ignore
from langchain_community.document_loaders import (
    BSHTMLLoader,
    PyMuPDFLoader,
    TextLoader,
    YoutubeLoader,
)
from langchain_community.document_loaders.base import BaseLoader
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class Crawl4AILoader(BaseLoader):
    def __init__(
        self,
        url: str,
        css_selector: str | None = None,
    ) -> None:
        self.url = url
        self.css_selector = css_selector

    async def crawl(self, url: str, css_selector: str | None = None):
        from crawl4ai import AsyncWebCrawler

        async with AsyncWebCrawler(verbose=True) as crawler:
            result = await crawler.arun(
                url,
                css_selector=css_selector or "",
            )

        return result

    def _process_result(self, result):
        if result.markdown is None:
            raise ValueError(f"No valid content found at {self.url}")

        metadata: dict[str, str | None] = {  # type: ignore
            **(result.metadata or {}),
            "source": self.url,
        }

        return Document(page_content=result.markdown, metadata=metadata)

    async def alazy_load(self) -> AsyncIterator[Document]:
        """Load HTML document into document objects."""
        # First attempt loading with CSS selector if provided
        result = await self.crawl(self.url, self.css_selector)

        # Second attempt loading without CSS selector if first attempt failed
        if result.markdown is None and self.css_selector is not None:
            result = await self.crawl(self.url)

        yield self._process_result(result)


def get_best_loader(extract_from: str | Path) -> BaseLoader:
    match extract_from:
        case str() | Path() if os.path.isfile(extract_from):
            if os.path.splitext(extract_from)[1] == ".pdf":
                return PyMuPDFLoader(file_path=str(extract_from))
            else:
                return TextLoader(file_path=extract_from)
        case str() if extract_from.startswith("http"):
            if "youtube" in extract_from:
                video_id = YoutubeLoader.extract_video_id(extract_from)
                return YoutubeLoader(video_id=video_id)
            else:
                try:
                    return Crawl4AILoader(url=extract_from, css_selector="article")
                except Exception:
                    logger.warning(
                        dedent("""
                        Crawl4AI web loader didn't work. However, it's recommended for
                        better results. Install it with `pip install crawl4ai`.
                                   
                        Once installed, make sure to follow the instructions in their
                        repo: https://github.com/unclecode/crawl4ai
                                   
                        For example, you might need to run `playwright install` to
                        install utils for the crawlers to work.

                        Now I will use the default web loader using BeautifulSoup.
                    """)
                    )

                    html_content = requests.get(extract_from).text

                    with NamedTemporaryFile(
                        delete=False, mode="w", suffix=".html"
                    ) as f:
                        f.write(html_content)

                    loader = BSHTMLLoader(file_path=f.name)
                    f.close()
                    return loader
        case _:
            raise ValueError("Invalid input")


async def _extract_single_source(
    extract_from: str | Path, use_async: bool = True
) -> str:
    """Extract content from a single source with unified async/sync handling."""
    logger.info(f"Extracting content from {extract_from}")
    loader = get_best_loader(extract_from)

    docs = (
        await loader.aload()
        if use_async or isinstance(loader, Crawl4AILoader)
        else loader.load()
    )

    content_parts = []
    for doc in docs:
        if doc.metadata.get("title"):
            content_parts.append(f"\n\n# {doc.metadata['title']}\n\n")
        content_parts.append(doc.page_content.strip())

    return "".join(content_parts)


async def _extract_multiple_sources(
    sources: list[str | Path] | list[str] | list[Path], use_async: bool = True
) -> str:
    """Extract content from multiple sources and wrap them in document tags."""
    contents = await asyncio.gather(
        *[_extract_single_source(source, use_async=use_async) for source in sources]
    )

    return "\n\n".join(
        f"# Document START: {source}\n\n{content}\n\n# Document END: {source}\n\n"
        for source, content in zip(sources, contents)
    )


# Public API functions
async def aextract_content(
    extract_from: str | Path | list[str] | list[Path] | list[str | Path],
) -> str:
    """Async version of content extraction."""
    sources = [extract_from] if not isinstance(extract_from, list) else extract_from
    return await _extract_multiple_sources(sources, use_async=True)


def extract_content(
    extract_from: str | Path | list[str] | list[Path] | list[str | Path],
) -> str:
    """Sync version of content extraction."""
    sources = [extract_from] if not isinstance(extract_from, list) else extract_from
    return asyncio.run(_extract_multiple_sources(sources, use_async=False))
