from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LEDGER_FIELDS = [
    "date",
    "match_id",
    "competition",
    "stage",
    "home_team",
    "away_team",
    "kickoff_bjt",
    "prediction",
    "confidence",
    "result",
    "correct",
    "error_reason",
    "lesson",
    "report_path",
]

ROLES = [
    {
        "id": "fact-checker",
        "name": "事实核验员",
        "file": "agents/01-fact-checker.md",
        "mission": "只核验事实，不做预测。确认赛程、时间、状态、球队名称、场地和来源可靠性。",
    },
    {
        "id": "data-analyst",
        "name": "数据分析师",
        "file": "agents/02-data-analyst.md",
        "mission": "只从近期状态、历史数据、xG、进攻防守指标、排名和交锋记录分析。",
    },
    {
        "id": "tactical-analyst",
        "name": "战术分析师",
        "file": "agents/03-tactical-analyst.md",
        "mission": "从阵型、关键对位、风格克制、定位球和比赛节奏分析。",
    },
    {
        "id": "news-researcher",
        "name": "新闻情报员",
        "file": "agents/04-news-researcher.md",
        "mission": "查找最新伤停、停赛、发布会、天气、轮换和突发消息。",
    },
    {
        "id": "risk-officer",
        "name": "风险官",
        "file": "agents/05-risk-officer.md",
        "mission": "专门反驳主流结论，寻找冷门、平局、信息偏差和过度自信。",
    },
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def load_matches(path: Path) -> list[dict[str, Any]]:
    data = load_json(path)
    if isinstance(data, dict):
        matches = data.get("matches", [])
    else:
        matches = data
    if not isinstance(matches, list):
        raise ValueError("fixtures file must contain a list or an object with a 'matches' list")
    return [m for m in matches if isinstance(m, dict)]


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "match"


def match_id(match: dict[str, Any]) -> str:
    if match.get("match_id"):
        return str(match["match_id"])
    day = match_day(match) or "unknown-date"
    home = str(match.get("home_team", "home"))
    away = str(match.get("away_team", "away"))
    return slugify(f"{day}-{home}-vs-{away}")


def match_day(match: dict[str, Any]) -> str:
    kickoff = str(match.get("kickoff_bjt") or match.get("date_bjt") or match.get("kickoff") or "")
    return kickoff[:10]


def filter_matches(matches: list[dict[str, Any]], day: str) -> list[dict[str, Any]]:
    return [m for m in matches if match_day(m) == day]


def match_title(match: dict[str, Any]) -> str:
    return f"{match.get('home_team', 'Home')} vs {match.get('away_team', 'Away')}"


def render_match_block(match: dict[str, Any]) -> str:
    sources = match.get("source_urls") or []
    if isinstance(sources, str):
        sources = [sources]
    sources_text = "\n".join(f"- {url}" for url in sources) or "- No source URL provided"
    return f"""## Match Context

- match_id: {match_id(match)}
- competition: {match.get("competition", "FIFA World Cup")}
- stage: {match.get("stage", "")}
- kickoff_bjt: {match.get("kickoff_bjt", "")}
- home_team: {match.get("home_team", "")}
- away_team: {match.get("away_team", "")}
- venue: {match.get("venue", "")}
- status: {match.get("status", "")}
- notes: {match.get("notes", "")}

## Source URLs

{sources_text}
"""


def render_role_prompt(match: dict[str, Any], role: dict[str, str], lessons: str) -> str:
    role_prompt = read_text(ROOT / role["file"])
    return f"""# {role["name"]} Task

{render_match_block(match)}

## Role Mission

{role["mission"]}

## Reusable Lessons

{lessons or "No lessons yet."}

## Role Prompt

{role_prompt}

## Output Requirement

请只输出这个角色负责的分析报告。必须标记来源；无法确认的信息要写“不确定”；不要输出最终总预测，除非你的角色模板要求给出倾向。
"""


def render_swarm_prompt(day: str, matches: list[dict[str, Any]], lessons: str) -> str:
    match_list = "\n".join(
        f"- {match_id(m)}: {match_title(m)}, {m.get('kickoff_bjt', '')}, {m.get('stage', '')}, {m.get('venue', '')}"
        for m in matches
    )
    role_list = "\n".join(f"- {role['name']}: {role['mission']}" for role in ROLES)
    controller = read_text(ROOT / "agents/00-master-controller.md")
    synthesis = read_text(ROOT / "agents/06-synthesis-editor.md")
    return f"""# World Cup Prediction Swarm Prompt

日期：{day}

请基于下面的比赛列表，为每场比赛启动五个独立 Agent 并行分析，最后生成一份世界杯预测日报。

## 比赛列表

{match_list}

## Agent 分工

{role_list}

## 可复用教训

{lessons or "暂无历史教训。"}

## 主控规则

{controller}

## 最终日报格式

{synthesis}

## 强制要求

1. 先由事实核验员确认赛程和比赛状态。
2. 每个 Agent 独立分析，不要互相复制结论。
3. 所有事实必须带来源或标记“不确定”。
4. 风险官必须明确反驳主流判断。
5. 最终预测只能使用 home_win、draw、away_win。
6. 每场比赛必须输出置信度、主要依据、反对依据、最大风险和赛前二次确认项。
7. 不输出赌博建议。
"""


def render_report_draft(day: str, matches: list[dict[str, Any]]) -> str:
    rows = "\n".join(
        f"| {match_title(m)} | {m.get('kickoff_bjt', '')} | {m.get('stage', '')} | {m.get('venue', '')} | 待填 | 待填 | 待填 | 待填 | 待填 |"
        for m in matches
    )
    prediction_rows = "\n".join(
        f"| {match_title(m)} | 待填 | 待填 | 待填 | 待填 | 待填 |"
        for m in matches
    )
    return f"""# {day} 世界杯预测日报草稿

## 今日比赛

| 比赛 | 北京时间 | 阶段 | 场地 | 事实风险 | 数据倾向 | 战术倾向 | 新闻倾向 | 风险官意见 |
|---|---|---|---|---|---|---|---|---|
{rows}

## 最终预测

| 比赛 | 预测 | 置信度 | 主要依据 | 最大风险 | 赛前二次确认项 |
|---|---|---|---|---|---|
{prediction_rows}

## 今日总体风险

- 待填

## 赛后复盘入口

赛后将真实比分写入 `data/results.json`，再运行：

```powershell
python .\\scripts\\score_results.py --results .\\data\\results.json --date {day}
```
"""


def ensure_ledger_entries(day: str, matches: list[dict[str, Any]], report_path: Path) -> None:
    ledger_path = ROOT / "memory/ledger.csv"
    ledger_path.parent.mkdir(parents=True, exist_ok=True)

    existing_rows: list[dict[str, str]] = []
    existing_keys: set[tuple[str, str]] = set()
    if ledger_path.exists() and ledger_path.read_text(encoding="utf-8").strip():
        with ledger_path.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                existing_rows.append(row)
                existing_keys.add((row.get("date", ""), row.get("match_id", "")))

    report_rel = report_path.relative_to(ROOT).as_posix()
    for match in matches:
        key = (day, match_id(match))
        if key in existing_keys:
            continue
        existing_rows.append(
            {
                "date": day,
                "match_id": match_id(match),
                "competition": str(match.get("competition", "FIFA World Cup")),
                "stage": str(match.get("stage", "")),
                "home_team": str(match.get("home_team", "")),
                "away_team": str(match.get("away_team", "")),
                "kickoff_bjt": str(match.get("kickoff_bjt", "")),
                "prediction": "",
                "confidence": "",
                "result": "",
                "correct": "",
                "error_reason": "",
                "lesson": "",
                "report_path": report_rel,
            }
        )

    with ledger_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=LEDGER_FIELDS)
        writer.writeheader()
        for row in existing_rows:
            writer.writerow({field: row.get(field, "") for field in LEDGER_FIELDS})


def run(day: str, fixtures_path: Path) -> Path:
    matches = filter_matches(load_matches(fixtures_path), day)
    if not matches:
        raise SystemExit(f"No matches found for {day} in {fixtures_path}")

    lessons = read_text(ROOT / "memory/lessons.md") if (ROOT / "memory/lessons.md").exists() else ""
    run_dir = ROOT / "runs" / day
    prompts_dir = run_dir / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)

    for match in matches:
        for role in ROLES:
            filename = f"{match_id(match)}-{role['id']}.md"
            write_text(prompts_dir / filename, render_role_prompt(match, role, lessons))

    write_text(run_dir / "swarm-prompt.md", render_swarm_prompt(day, matches, lessons))
    report_path = run_dir / "daily-report-draft.md"
    write_text(report_path, render_report_draft(day, matches))
    ensure_ledger_entries(day, matches, report_path)
    return run_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a World Cup prediction harness task pack.")
    parser.add_argument("--date", default=date.today().isoformat(), help="Target date in YYYY-MM-DD, using Beijing-time fixture dates.")
    parser.add_argument("--fixtures", default=str(ROOT / "data/fixtures.json"), help="Path to fixtures JSON.")
    args = parser.parse_args()

    run_dir = run(args.date, Path(args.fixtures).resolve())
    print(f"Generated harness run: {run_dir}")


if __name__ == "__main__":
    main()

