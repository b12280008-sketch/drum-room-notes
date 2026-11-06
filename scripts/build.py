#!/usr/bin/env python3
"""Validate practice cards and build the static GitHub Pages site."""

import argparse
import html
import json
import re
from pathlib import Path
from string import Template


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs"
TEMPLATES = ROOT / "src" / "templates"
TRACKS = {"hat": "Hi-hat", "snare": "軍鼓", "kick": "大鼓"}
MARKS = {"x": ("hit", "x", "敲擊"), "X": ("accent", "X", "重音"), "-": ("rest", "−", "休止")}
FIELDS = {"slug", "order", "title", "level", "tempo", "summary", "pattern", "steps", "checkpoint"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def valid_text(value, maximum):
    return isinstance(value, str) and 1 <= len(value) <= maximum and value == value.strip() and "\n" not in value


def validate_card(card, path):
    require(isinstance(card, dict) and card.keys() == FIELDS, "卡片欄位須與 AGENTS.md 一致")
    slug = card["slug"]
    require(isinstance(slug, str) and 2 <= len(slug) <= 48 and re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", slug), "slug 格式錯誤")
    require(path.stem == slug, "檔名需與 slug 相同")
    require(type(card["order"]) is int and 1 <= card["order"] <= 999, "order 須為 1 至 999 的整數")
    require(type(card["tempo"]) is int and 40 <= card["tempo"] <= 180, "tempo 須為 40 至 180 的整數")
    require(card["level"] in ("基礎", "進階"), "level 須為基礎或進階")
    for field, maximum in {"title": 28, "summary": 100, "checkpoint": 110}.items():
        require(valid_text(card[field], maximum), f"{field} 須為 1 至 {maximum} 字的單行文字")
    steps = card["steps"]
    require(isinstance(steps, list) and len(steps) == 3 and all(valid_text(step, 90) for step in steps), "steps 須有三個單行步驟，每句最多 90 字")
    pattern = card["pattern"]
    require(isinstance(pattern, dict) and pattern.keys() == TRACKS.keys(), "pattern 須包含 hat、snare、kick")
    for track, notes in pattern.items():
        require(isinstance(notes, str) and re.fullmatch(r"[xX-]{16}", notes), f"{track} 須為 16 格節奏，符號使用 x、X、-")
    return card


def load_cards():
    cards = []
    for path in sorted((ROOT / "content").glob("*.json")):
        try:
            cards.append(validate_card(json.loads(path.read_text(encoding="utf-8")), path))
        except ValueError as error:
            raise ValueError(f"{path.name} · {error}") from error
    require(cards, "至少需有一張練習卡")
    for key in ("order", "title"):
        require(len({card[key] for card in cards}) == len(cards), f"練習卡的 {key} 不可重複")
    return sorted(cards, key=lambda card: card["order"])


def template(name, **data):
    return Template((TEMPLATES / name).read_text(encoding="utf-8")).substitute(data)


def score(card):
    labels = [label for beat in "1234" for label in (beat, "e", "&", "a")]
    columns = range(16)
    headers = []
    for step in columns:
        group = " beat-start" if step % 4 == 0 else ""
        headers.append(f'<th scope="col" data-step="{step}" class="count{group}">{html.escape(labels[step])}</th>')
    rows = []
    for instrument, name in TRACKS.items():
        cells = []
        for step in columns:
            note = card["pattern"][instrument][step]
            style, symbol, description = MARKS[note]
            group = " beat-start" if step % 4 == 0 else ""
            cells.append(f'<td class="{style}{group}" data-step="{step}" data-hit="{note}"><span aria-hidden="true">{symbol}</span><span class="sr-only">{description}</span></td>')
        rows.append(f'<tr data-instrument="{instrument}"><th scope="row">{name}</th>{"".join(cells)}</tr>')
    title = html.escape(card["title"])
    return f'<table class="score"><caption class="sr-only">{title}的一小節節奏譜</caption><thead><tr><th scope="col">鼓件</th>{"".join(headers)}</tr></thead><tbody>{"".join(rows)}</tbody></table>'


def render_base(title, description, home, content, player=False):
    script = f'<script defer src="{home}assets/player.js"></script>' if player else ""
    return template("base.html", page_title=html.escape(title), description=html.escape(description),
                    home=home, content=content, extra_script=script)


def render_home(cards):
    items = []
    for card in cards:
        url = f'practice/{card["slug"]}/'
        title = html.escape(card["title"])
        items.append(f'''<article class="practice-card">
  <div class="card-meta"><span class="card-number">{card['order']:02}</span><span class="level">{card['level']}</span></div>
  <h3><a href="{url}">{title}</a></h3>
  <p>{html.escape(card['summary'])}</p>
  <div class="card-bottom"><span class="tempo-tag">{card['tempo']} BPM</span><a href="{url}" aria-label="練習{title}">開始練習 <span aria-hidden="true">↗</span></a></div>
</article>''')
    first = cards[0]
    # The cover shows the first card's full grid, compressed with CSS.
    content = template("home.html", example_title=html.escape(first["title"]), example_tempo=first["tempo"],
                       example_score=score(first), card_count=len(cards), cards="\n".join(items))
    return render_base("鼓房筆記 · 爵士鼓練習卡", "一頁一張爵士鼓練習卡，從節奏譜和合成示範開始練。", "./", content)


def render_practice(card, following):
    title = html.escape(card["title"])
    summary = html.escape(card["summary"])
    next_link = ""
    if following:
        next_title = html.escape(following["title"])
        next_link = f'<a class="next" href="../{following["slug"]}/">下一張 · {next_title} →</a>'
    content = template("practice.html", number=f'{card["order"]:02}', title=title, summary=summary,
                       level=card["level"], tempo=card["tempo"], score=score(card),
                       steps="".join(f"<li>{html.escape(step)}</li>" for step in card["steps"]),
                       checkpoint=html.escape(card["checkpoint"]), next_link=next_link)
    return render_base(f'{card["title"]} · 鼓房筆記', card["summary"], "../../", content, player=True)


def build_files(cards):
    files = {Path(".nojekyll"): b"", Path("index.html"): render_home(cards).encode("utf-8")}
    for index, card in enumerate(cards):
        following = cards[index + 1] if index + 1 < len(cards) else None
        files[Path("practice") / card["slug"] / "index.html"] = render_practice(card, following).encode("utf-8")
    for asset in sorted((ROOT / "src" / "assets").iterdir()):
        if asset.is_file():
            files[Path("assets") / asset.name] = asset.read_bytes()
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="比對 docs/ 與預期輸出，不寫檔")
    args = parser.parse_args()
    try:
        cards = load_cards()
        files = build_files(cards)
    except (OSError, ValueError) as error:
        parser.exit(1, f"建置失敗 · {error}\n")

    actual = {path.relative_to(OUTPUT) for path in OUTPUT.rglob("*") if path.is_file()}
    if args.check:
        outdated = sorted(path for path, data in files.items() if path not in actual or (OUTPUT / path).read_bytes() != data)
        extra = sorted(actual - files.keys())
        if outdated or extra:
            mismatches = ", ".join(str(path) for path in [*outdated, *extra])
            parser.exit(1, f"docs/ 需要重建 · {mismatches}\n")
        print(f"檢查通過 · {len(cards)} 張練習卡及 {len(files)} 個網站檔案")
        return

    # docs/ is reserved for generated files. Load and validate every card first.
    for path in actual - files.keys():
        (OUTPUT / path).unlink()
    for path, data in files.items():
        destination = OUTPUT / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists() or destination.read_bytes() != data:
            destination.write_bytes(data)
    print(f"建置完成 · {len(cards)} 張練習卡，輸出到 docs/")


if __name__ == "__main__":
    main()
