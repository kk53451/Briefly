"""샘플 뉴스 로더 및 공통 유틸."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
OUTPUTS = HERE / "outputs"
OUTPUTS.mkdir(exist_ok=True)


@dataclass
class SampleNews:
    category: str
    category_ko: str
    date: str
    articles: list[dict[str, str]]

    def as_joined_text(self, sep: str = "\n\n---\n\n") -> str:
        """generate_podcast / NotebookLM source 로 넣을 단일 문자열로 결합."""
        parts = []
        for idx, article in enumerate(self.articles, start=1):
            parts.append(f"[뉴스 {idx}] {article['title']}\n\n{article['content']}")
        return sep.join(parts)

    def as_individual_sources(self) -> list[tuple[str, str]]:
        """(title, content) 리스트. NotebookLM 처럼 소스 단위로 쪼개서 넣을 때 사용."""
        return [(a["title"], a["content"]) for a in self.articles]


def load_sample() -> SampleNews:
    path = HERE / "sample_news.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return SampleNews(
        category=data["category"],
        category_ko=data["category_ko"],
        date=data["date"],
        articles=data["articles"],
    )


class StopWatch:
    def __enter__(self) -> "StopWatch":
        self.start = time.perf_counter()
        return self

    def __exit__(self, *exc: Any) -> None:
        self.elapsed = time.perf_counter() - self.start


def out_path(name: str) -> Path:
    """outputs/{name} 절대경로 반환."""
    return OUTPUTS / name
