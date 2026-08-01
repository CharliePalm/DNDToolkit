import json
import os
from pathlib import Path
from typing import List
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
INPUT_PATH = ROOT / "fixtures" / "icons.html"
OUTPUT_PATH = ROOT / "artifacts" / "icons.json"


def parse_icon_ids(html_path: Path) -> List[str]:
    with html_path.open("r", encoding="utf-8") as handle:
        soup = BeautifulSoup(handle.read(), "html.parser")

    icon_ids: List[str] = []
    for container in soup.select(".icon"):
        svg = container.find("svg")
        if svg is not None and svg.has_attr("id"):
            icon_ids.append(svg["id"])

    return icon_ids


def main() -> None:
    icon_ids = parse_icon_ids(INPUT_PATH)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as handle:
        json.dump(icon_ids, handle, indent=2)
        handle.write("\n")


if __name__ == "__main__":
    main()
