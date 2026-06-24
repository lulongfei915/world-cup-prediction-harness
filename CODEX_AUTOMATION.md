# 如何在 Codex 上自动化实现世界杯预测

本文档说明如何把本地 `world-cup-prediction-harness` 接入 Codex 自动化，让它每天自动生成世界杯预测，并在赛后自动复盘。

## 1. 是否必须使用本地 harness

本地 harness 不是绝对必要。

如果只是临时预测一两场比赛，可以直接让 Codex 联网搜索赛程、伤停、数据和新闻，然后给出分析。

但如果目标是长期运行一个“每天预测、赛后复盘、持续改进”的系统，本地 harness 是有必要的。它负责保存三个关键东西：

- `data/fixtures.json`：当天有哪些比赛，以及赛程事实来源。
- `memory/ledger.csv`：每场比赛的预测账本。
- `memory/lessons.md`：赛后复盘沉淀出的经验。

没有本地 harness，Codex 每天都会更像是“第一次预测”。有了 harness，它可以带着历史错误和经验继续下一轮。

## 2. 自动化总体架构

推荐把 Codex 自动化拆成两条流水线：

```text
赛前预测自动化
  -> 获取当天赛程
  -> 核验事实
  -> 更新 fixtures.json
  -> 生成多 Agent 任务包
  -> 执行五个 Agent 分析
  -> 输出预测日报
  -> 写入 ledger.csv

赛后复盘自动化
  -> 获取真实比分
  -> 写入 results.json
  -> 运行评分脚本
  -> 更新 ledger.csv
  -> 总结错误原因
  -> 更新 lessons.md
```

这两条自动化合在一起，形成闭环：

```text
赛程核验 -> 多 Agent 分析 -> 预测日报 -> 真实结果 -> 账本评分 -> 错题复盘 -> 教训回流
```

## 3. 本地项目入口

项目目录：

```powershell
D:\agent开发\world-cup-prediction-harness
```

核心文件：

```text
data/fixtures.json
memory/ledger.csv
memory/lessons.md
scripts/run_harness.py
scripts/score_results.py
```

每日生成任务包：

```powershell
cd D:\agent开发\world-cup-prediction-harness
python .\scripts\run_harness.py --date 2026-06-24
```

赛后评分：

```powershell
python .\scripts\score_results.py --results .\data\results.json --date 2026-06-24
```

## 4. 赛前预测自动化

### 4.1 触发时间

建议每天早上运行一次，或者在当天第一场比赛开赛前 3-6 小时运行。

例如：

```text
每天 08:00，北京时间
```

如果比赛分布在深夜，也可以增加一次下午检查：

```text
每天 16:00，北京时间
```

### 4.2 自动化任务

Codex 需要完成以下工作：

1. 进入 `D:\agent开发\world-cup-prediction-harness`。
2. 联网获取今天世界杯赛程。
3. 优先使用 FIFA、ESPN、赛事官方信息源核验比赛。
4. 更新 `data/fixtures.json`。
5. 运行 `scripts/run_harness.py` 生成当天任务包。
6. 读取 `runs/YYYY-MM-DD/swarm-prompt.md`。
7. 按五个 Agent 分工完成分析。
8. 生成预测日报。
9. 将最终预测写入 `memory/ledger.csv`。
10. 输出当日摘要。

### 4.3 可直接复制给 Codex Automation 的 Prompt

```text
进入 D:\agent开发\world-cup-prediction-harness。

请自动完成今天的世界杯赛前预测：

1. 联网获取今天的世界杯比赛赛程，日期以北京时间为准。
2. 优先使用 FIFA 官方、ESPN Soccer、赛事官方渠道等可靠来源核验赛程。
3. 更新 data/fixtures.json，字段必须包括：
   - match_id
   - competition
   - stage
   - kickoff_bjt
   - home_team
   - away_team
   - venue
   - status
   - source_urls
   - notes
4. 运行：
   python .\scripts\run_harness.py --date 今天日期
5. 读取 runs/今天日期/swarm-prompt.md。
6. 按照 swarm-prompt.md 执行五个 Agent 分析：
   - 事实核验员
   - 数据分析师
   - 战术分析师
   - 新闻情报员
   - 风险官
7. 汇总生成 reports/今天日期-world-cup-prediction.md。
8. 将每场比赛最终预测写入 memory/ledger.csv，prediction 只能使用 home_win、draw、away_win。
9. 输出今日预测摘要，包括：
   - 比赛
   - 预测
   - 置信度
   - 主要依据
   - 最大风险
   - 赛前需要二次确认的信息

要求：
- 不要凭记忆补赛程。
- 没有核验来源的比赛不要预测。
- 所有关键结论必须带来源或标记为推理。
- 不输出赌博建议。
```

## 5. 赛后复盘自动化

### 5.1 触发时间

建议每天最后一场比赛结束后运行。

如果不想精确维护比赛结束时间，可以每天固定早上运行，复盘前一天已经结束的比赛。

例如：

```text
每天 10:00，北京时间，复盘前一天比赛
```

### 5.2 自动化任务

Codex 需要完成以下工作：

1. 进入 `D:\agent开发\world-cup-prediction-harness`。
2. 联网获取已经结束比赛的真实比分。
3. 写入 `data/results.json`。
4. 运行 `scripts/score_results.py`。
5. 更新 `memory/ledger.csv`。
6. 分析错误预测。
7. 将可复用教训写入 `memory/lessons.md`。
8. 输出赛后复盘摘要。

### 5.3 可直接复制给 Codex Automation 的 Prompt

```text
进入 D:\agent开发\world-cup-prediction-harness。

请自动完成世界杯赛后复盘：

1. 联网获取指定日期已经结束的世界杯比赛真实比分，日期以北京时间为准。
2. 优先使用 FIFA 官方、ESPN Soccer、赛事官方渠道等可靠来源核验比分。
3. 写入 data/results.json，格式为：
   {
     "results": [
       {
         "match_id": "...",
         "home_score": 0,
         "away_score": 0
       }
     ]
   }
4. 运行：
   python .\scripts\score_results.py --results .\data\results.json --date 指定日期
5. 检查 memory/ledger.csv 中每场比赛的 prediction、result、correct。
6. 对预测错误的比赛补充 error_reason。
7. 将可复用教训追加到 memory/lessons.md。
8. 输出赛后复盘摘要，包括：
   - 复盘日期
   - 总比赛数
   - 命中数
   - 命中率
   - 错误比赛
   - 错误原因
   - 下一轮需要调整的规则

要求：
- 不要凭记忆补比分。
- 没有可靠来源的比分不要写入结果。
- 复盘要区分“事实错误”“数据误判”“新闻遗漏”“风险低估”“随机波动”。
```

## 6. Codex 自动化建议配置

建议建立两个 Codex Cron Automation。

### 6.1 World Cup Daily Prediction

用途：每天生成赛前预测。

建议配置：

```text
名称：World Cup Daily Prediction
类型：cron
工作目录：D:\agent开发\world-cup-prediction-harness
运行时间：每天 08:00，北京时间
任务：使用第 4.3 节的 Prompt
```

### 6.2 World Cup Result Review

用途：每天赛后复盘并更新教训库。

建议配置：

```text
名称：World Cup Result Review
类型：cron
工作目录：D:\agent开发\world-cup-prediction-harness
运行时间：每天 10:00，北京时间
任务：使用第 5.3 节的 Prompt
```

## 7. 文件如何流转

### 赛前

```text
Codex 联网查赛程
  -> data/fixtures.json
  -> scripts/run_harness.py
  -> runs/YYYY-MM-DD/swarm-prompt.md
  -> reports/YYYY-MM-DD-world-cup-prediction.md
  -> memory/ledger.csv
```

### 赛后

```text
Codex 联网查比分
  -> data/results.json
  -> scripts/score_results.py
  -> memory/ledger.csv
  -> memory/review-YYYY-MM-DD.md
  -> memory/lessons.md
```

## 8. 最小可用版本

如果你不想使用完整项目，最小版本只需要这些文件：

```text
data/fixtures.json
agents/*.md
memory/ledger.csv
memory/lessons.md
scripts/run_harness.py
scripts/score_results.py
```

其中最不能删的是：

- `memory/ledger.csv`
- `memory/lessons.md`

因为它们负责保存历史判断和复盘经验。

## 9. 注意事项

1. 不要让 Codex 凭记忆预测世界杯。
2. 赛程、比分、伤停、停赛必须联网核验。
3. `prediction` 字段只使用 `home_win`、`draw`、`away_win`。
4. 置信度不要滥用 80 分以上。
5. 平局必须单独分析，不能当成剩余概率。
6. 风险官必须认真反驳主流判断。
7. 错误预测要写明原因，否则系统不会真正进步。
8. `lessons.md` 要保持简短、可复用、可被下一轮调用。

## 10. 推荐工作方式

第一阶段可以先手动运行：

```powershell
python .\scripts\run_harness.py --date 2026-06-24
```

确认日报和账本格式符合预期后，再交给 Codex Automation 每天跑。

不要一开始就全自动。先手动跑 1-2 天，检查：

- 赛程是否准确。
- Agent 分析是否有来源。
- 预测是否正确写入账本。
- 赛后评分是否能跑通。
- 错题是否能沉淀成有效教训。

稳定后，再开启每天自动执行。

