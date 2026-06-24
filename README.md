# World Cup Prediction Harness

一个用于世界杯比赛预测的多 Agent harness。它把“先核验事实，再分角色分析，最后记账复盘”的流程固化成本地项目，适合配合 Kimi Code `/swarm`、Codex、多 Agent 平台或人工专家一起使用。

## 1. 这个 harness 解决什么问题

世界杯预测容易出现三个问题：

- 事实没核准：赛程、开球时间、伤停、首发、场地、天气等基础信息有误。
- 单一视角过强：一个模型或一个分析师很容易被同一类信息带偏。
- 不能复盘：预测完就结束，无法知道自己为什么错，也无法让下一轮变好。

这个 harness 的设计目标是：

```text
事实核验 -> 五个 Agent 并行分析 -> 风险官反驳 -> 汇总预测 -> 写入账本 -> 赛后复盘 -> 教训回流
```

## 2. 目录结构

```text
world-cup-prediction-harness/
  README.md
  config.json
  agents/
    00-master-controller.md
    01-fact-checker.md
    02-data-analyst.md
    03-tactical-analyst.md
    04-news-researcher.md
    05-risk-officer.md
    06-synthesis-editor.md
  data/
    fixtures.json
    fixtures.sample.json
    results.sample.json
    sources.md
  memory/
    ledger.csv
    lessons.md
    mistakes.md
  reports/
  runs/
  scripts/
    run_harness.py
    score_results.py
```

## 3. 快速开始

进入项目目录：

```powershell
cd D:\agent开发\world-cup-prediction-harness
```

生成当天任务包：

```powershell
python .\scripts\run_harness.py --date 2026-06-24
```

生成结果会放在：

```text
runs/YYYY-MM-DD/
  swarm-prompt.md
  daily-report-draft.md
  prompts/
```

其中：

- `swarm-prompt.md`：可以直接复制给 Kimi Code `/swarm` 或其他多 Agent 执行器。
- `prompts/`：每场比赛、每个 Agent 的独立任务 prompt。
- `daily-report-draft.md`：最终日报草稿。
- `memory/ledger.csv`：预测账本，会自动追加待填的比赛行。

## 4. 准备赛程数据

编辑 `data/fixtures.json`，格式如下：

```json
{
  "matches": [
    {
      "match_id": "sample-001",
      "competition": "FIFA World Cup",
      "stage": "Group stage",
      "kickoff_bjt": "2026-06-24 22:00",
      "home_team": "Team A",
      "away_team": "Team B",
      "venue": "Stadium name",
      "status": "scheduled",
      "source_urls": [
        "https://www.fifa.com/",
        "https://www.espn.com/soccer/"
      ],
      "notes": "Replace this sample with verified fixture data."
    }
  ]
}
```

不要让模型凭空补赛程。先从官方或可信来源核验赛程，再填入 `fixtures.json`。

## 5. 五个核心 Agent

### 事实核验员

确认比赛是否真实存在、开球时间是否正确、球队名称是否一致、比赛状态是否可预测。

### 数据分析师

分析历史战绩、近期状态、进攻防守数据、Elo/FIFA 排名、xG、射门、控球、定位球等量化指标。

### 战术分析师

分析阵型、压迫强度、边路/中路倾向、转换进攻、防守弱点、关键对位。

### 新闻情报员

检查伤停、停赛、训练、主帅发布会、旅途、天气、舆情和突发消息。

### 风险官

专门反驳前面所有结论，识别冷门、平局、轮换、信息源偏差和过度自信。

## 6. 最终输出

每场比赛最终输出：

- 胜平负倾向：`home_win`、`draw`、`away_win`
- 置信度：0-100
- 主要依据
- 反对依据
- 最大风险
- 需要赛前二次确认的信息

## 7. 赛后评分

先把真实结果填入 `data/results.sample.json` 或新建 `data/results.json`：

```json
{
  "results": [
    {
      "match_id": "sample-001",
      "home_score": 2,
      "away_score": 1
    }
  ]
}
```

然后运行：

```powershell
python .\scripts\score_results.py --results .\data\results.sample.json --date 2026-06-24
```

脚本会更新 `memory/ledger.csv`，并生成 `memory/review-YYYY-MM-DD.md`。

## 8. 使用原则

1. 事实不确定时，不允许强行预测。
2. 所有关键结论必须带来源或明确说明是推理。
3. 多 Agent 的价值是暴露分歧，不是制造一致意见。
4. 风险官必须认真反驳，不能只做补充说明。
5. 预测写入账本后，赛后必须复盘。
6. 错题本中的教训要进入下一次分析。

