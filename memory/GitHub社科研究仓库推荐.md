# 📦 GitHub 社科研究仓库 — 深度分析 & 唐太宗李世民整合方案

> 更新：2026-06-11 01:00
> 方法：逐个仓库读 README → 提取可复用模块 → 映射到现有体系

---

## 🏗️ 仓库一：AERS（Auto-Empirical Research Skills）
**链接：** https://github.com/brycewang-stanford/Auto-Empirical-Research-Skills
**规模：** 1,072 skills vendored · 64个集合 · 335个工具 · 23,000+ skills 生态

### 核心架构：四层

#### A. 旗舰：4套完整实证流水线 Skills（同级且互补）

| Skill | 语言栈 | 适用场景 |
|:----|:------|:--------|
| `00-Full-empirical-analysis-skill_StatsPAI` | Agent-native Python DSL | 默认首选，900+函数 |
| `00.1-Full-empirical-analysis-skill_Python` | Python 传统计量栈 | pandas+statsmodels+linearmodels |
| `00.2-Full-empirical-analysis-skill_Stata` | Stata | reghdfe+ivreg2+csdid+sdid |
| `00.3-Full-empirical-analysis-skill_R` | R tidyverse | fixest+did+bacondecomp+sandwich |

每套走同一个 8 步循环：
> data cleaning → variable construction → descriptives → diagnostics → estimation → robustness → mechanism/heterogeneity → publication-ready tables & figures

#### B. 科研写作专用集合（与唐太宗直接对标）

| 集合ID | 来源 | Skills | 内容 | 唐太宗映射 |
|:----|:-----|:---:|:-----|:---|
| `01-lishix520` | academic-paper-skills | 2 | 哲学/跨学科论文从提纲到投稿 | 🗺️ paper-summarize 加强版 |
| `02-luwill` | research-skills | 3 | 医学影像综述 | 📄 综述类用 |
| `03-K-Dense-AI` | claude-scientific-skills | 4 | **假设生成**/方法设计/文献检索 | 🔥 唐太宗缺这步！ |
| `04-K-Dense-AI` | claude-scientific-writer | 8 | 引用管理/文献综述/方法/结果写作 | 🗺️ citation + academic-writing |
| `05-kthorn` | research-superpower | 10 | 文献检索+筛选+摘要+引用追踪 | 🗺️ 扩展 literature-review |
| `06-fuhaoda` | stats-paper-writing | 1 | LaTeX统计论文写作+审稿回复 | 🗺️ paper-review 回应函 |
| `07-Orchestra` | AI-Research-SKILLs | 3 | 学术绘图/论文阅读/代码审查 | 🗺️ diagram-maker 加强 |
| `09-meleantonio` | awesome-econ-ai-stuff | 17 | 面板数据/IV/DiD/匹配/ML因果 | 🔥 量化方法 |
| `15-Felpix-Studios` | **social-science-research** | 12 | **全流程社科数据分析(R/Python)** | ⚡ 直接对接！ |
| `16-hsantanna88` | clo-author | 10 | 端到端数据分析+写作 | 🗺️ 综合 |

#### C. 因果推断工具（335个工具）

6大类：
1. **因果推断/处理效应库**（32个）：DoWhy, EconML, CausalML, DoubleML, grf/causal forest...
2. **计量经济/准实验库**（170个）：fixest, did, synth, rdrobust, csdid...
3. **因果发现/结构学习**（25个）
4. **自主研究agent**（51个）
5. **MCP 服务器**（48个）
6. **基准测试/数据集**（9个）

#### D. 质量保障体系

- **5个数值 benchmark**（每次重新计算gold值，不可伪造）：
  - LaLonde 1986 / Dehejia-Wahba 1999：观测数据对比RCT
  - Card 1995：IV教育回报（0.131 IV vs 0.075 OLS）
  - 交错DID（TWFE偏差检测）
  - 断点回归
  - Bad-control陷阱检测
- **安全审计**：52/52 CLEAN
- **eval-harness**：17个场景 / 95个评分项目

---

## 🧠 仓库二：cntext（中文计算社会科学文本分析）
**链接：** https://github.com/hiDaDeng/cntext

### 6大模块
| 模块 | 功能 | 投资者情感论文可替换？ |
|:----|:-----|:---|
| **IO** | 14个函数：读pdf/docx/txt、繁转简、文本清洗 | ✅ |
| **Stats** | 词频/可读性/情感/语义品牌/EPU不确定性 | ✅ 替代SnowNLP |
| **Plot** | 中文可视化/词分布图 | ✅ |
| **Model** | Word2Vec/GloVe/SoPmi/词嵌入评估 | ✅ 替代gensim单独调用 |
| **Mind** ⚡ | **WEPA语义投影**：生成概念轴→文本投影→心理构念测量 | 🔥 核心差异化 |
| **LLM** | 内置prompt的结构化LLM文本分析 | 🆕 |

### WEPA（词嵌入投影法）
- **理论驱动**：用理论定义锚定词（正/负极），非data-driven
- **可解释**：不是黑箱情感分数，是"该文本在某个概念轴上的位置"
- **1行代码**：`ct.wepa(wv, text, poswords, negwords, lang)`
- **出版级**：有完整复现demo + manuscript
- **社会科学的正确姿势**：不是"这段文本正面吗"→是"这段文本在'权力距离'轴上偏哪边"

---

## 🔬 仓库三：Awesome-LLM-in-Social-Science
**链接：** https://github.com/ValueByte-AI/Awesome-LLM-in-Social-Science

### 7大分类（全论文索引）
| 分类 | 核心内容 | 与我们的关系 |
|:----|:-----|:---|
| **Survey** | 26篇综述 | 找文献/写Introduction时直接查 |
| **Evaluating: Value** | LLM价值观评测 | DES论文（算法平台文化价值）🟢 |
| **Evaluating: Personality** | LLM人格评测 | 数字文化研究 🟡 |
| **Evaluating: Morality** | LLM道德评测 | 🟡 |
| **Evaluating: Opinion** | LLM观点评测 | 投资者情感 🟢 |
| **Alignment** | 多元对齐 | 方法学参考 |
| **Simulation** | LLM社会模拟 | 如果用agent-based 🟢 |

### 关键论文（直接相关）
- `Nature Human Behavior` 两篇LLM+社会科学
- `PNAS` "Can Generative AI improve social science?"
- ACL 2024 `ValueBench`：价值观评测基准
- NeurIPS 2024最佳论文 `PRISM`：跨文化对齐数据集

---

## 📊 仓库四：keyATM（Keyword Assisted Topic Models）
**链接：** https://github.com/keyATM/keyATM
**类型：** R包

### 与LDA的区别
| | LDA | keyATM |
|:--|:----|:-----|
| 主题定义 | 完全无监督 | **研究者用关键词引导** |
| 结果可解释性 | 低（概率分布） | **高**（因为主题有语义锚定） |
| 适用场景 | 探索性 | 验证性/半监督 |
| 论文友好度 | 中 | 高（审稿人更喜欢可解释的结果） |

### 投资者情感论文应用
当前论文用 SnowNLP + LDA → 可以升级为 cntext（情感）+ keyATM（主题）
= 更严谨的方法论 + 更强的审稿竞争力

---

## 🧪 仓库五：eDSL（Expected Parrot）
**链接：** https://github.com/expectedparrot/edsl
**类型：** Python库 + 免费平台

- 用 AI agent 做 **调查和实验**
- 定义 agent 人格特征 → 批量跑调查
- 支持 piping/skip-logic
- 自动缓存 + 可复现
- 免费 Coop 平台共享结果

### DES论文延伸
可以用 eDSL 做一个小规模验证：用不同人格的 AI agent 模拟"数字接触行为"，验证 DES 框架的预测

---

## 🏛️ 仓库六：awesome-computational-social-science
**链接：** https://github.com/gesiscss/awesome-computational-social-science

### 核心价值：CSS 全景地图

| 分类 | 关键资源 |
|:----|:-----|
| **Books** | 28本（含Salganik BIT BY BIT, González-Bailón Decoding, Grimmer Text as Data） |
| **Conferences** | 14个（IC2S2, ICWSM, WebSci, COMPTEXT...） |
| **Journals** | CSS发表渠道 + 软件发表渠道 |
| **Software** | R/Python 完整清单 |
| **Courses** | SICSS, NLP+CSS 201 教程 |

### 与DES论文投稿匹配
- 投稿方向看 `Journals for Software Submissions` 
- 会议投稿看 `Conferences`（IC2S2/COMPTEXT非常适合DES方法论）

---

## 🔗 仓库七：CoBRA
**链接：** https://github.com/AISmithLab/CoBRA
**CHI 2026 Best Paper 🏆**

### 核心架构
```
研究者指定目标偏差 → CoBRA通过经典实验测量 → 迭代调整agent → 可控偏差
```

三大控制方法：Prompt Engineering / Representation Engineering / Fine-tuning
支持偏差：权威效应/从众效应/确认偏差/框架效应

### 与DES的关系
DES的核心概念之一是"算法平台如何塑造接触模式"→ CoBRA提供了实验验证框架

---

## 📋 唐太宗·完整整合方案

### Phase 1：直接补缺（现在就能用）
```
唐太宗现有                    ← AERS/GitHub补充

① paper-summarize            ← 01-lishix520 combo skill
② nature-paper-review        ← 06-fuhaoda stats writing + reviewer reply
③ nature-citation            ← 04-K-Dense-AI citation-management
④ research-design-helper     ← 03-K-Dense-AI hypothesis-generation
⑤ diagram-maker              ← 07-Orchestra academic-plotting
```

### Phase 2：新能力补充（新增skills）
```
⑥ 因果推断稽核（全新）      ← AERS StatsPAI + DoWhy/EconML
   - 自动检查identification strategy
   - 验证假设是否成立
   - 给出 robustness check 建议

⑦ 文本方法论升级（投资者情感论文用）
   - SnowNLP → cntext WEPA（理论驱动的心理构念测量）
   - LDA → keyATM（关键词引导的可解释主题模型）

⑧ 文献全景扫描仪（全新）
   ← AERS research-superpower + Awesome-LLM-SS 论文索引
   - 输入RQ → 输出结构化文献地图
   - 自动标注gap

⑨ 可复现性审计（全新）
   - 检查数据/代码是否可复现
   - 对标AERS benchmark（每次重算gold value）
```

### Phase 3：参考架构（以后需要时调用）
```
⑩ AI agent 社会实验      ← eDSL
⑪ 社会模拟               ← CoBRA
⑫ 中文政策不确定性       ← cntext EPU/FEPU
⑬ 方法论学习入口         ← awesome-computational-social-science
```

---

## 🎯 立即行动项

### P0（本周可做）
1. ~~逛完所有仓库~~ ✅
2. 从 AERS 提取 03-K-Dense-AI hypothesis-generation → 整合到唐太宗扩展技能
3. 用 cntext WEPA 重跑投资者情感论文的情感分析 → 看效果差异

### P1（下周）
4. 从 AERS 提取 causal-inference 稽核 → 新建技能
5. 试 keyATM → 对比 LDA 主题建模结果

### P2（长期储备）
6. eDSL 做 DES 框架验证实验
7. CoBRA 框架学习
