# 🦁 A股论文v37 · IJoC投稿终版 — 全系统评审报告

> 日期：2026-06-19 | 评审系统：龙虾组织 × Nature × 唐太宗v3.0 × 李世民
> 稿件：A股_IJoC投稿终版_v37_1.docx | 目标期刊：International Journal of Communication (IJoC)

---

### 🛠️ 技能清单
```
✅ nature-writing — Nature风格写作评估
✅ nature-polishing — 学术润色审计
✅ 唐太宗v3.0 (15技能) — 全流程评估
   ✅ paper-summarize — 骨架提取
   ✅ paper-review — 对抗式审查
   ✅ citation-audit — 参考文献审计
   ✅ research-design — 方法论评估
   ✅ deep-audit — 深度方法论审计
   ✅ literature-scanner — 文献定位
   ✅ hypothesis-generator — 假说评估
   ✅ causal-audit — 因果推断
   ✅ diagram-maker — 可视化评估
   ✅ academic-writing — 学术写作
✅ 龙虾模块 — 未发酵信号/前瞻识别
✅ 李世民计划 — 科研管理体系
```

---

# 第一编 · 📋 龙虾组织评审
## 🦞 领先埋伏视角：未发酵信号 & 前瞻发现

### 1.1 这个版本与v1的核心差异（龙虾视角的关键发现）

v37相比v1的投资者情感论文（5.5/10），发生了质的飞跃：

| 维度 | v1版本（6/4） | v37版本（IJoC终版） | 升级幅度 |
|:----|:------------|:------------------|:-------:|
| 标题 | Investor sentiment dynamics under… | Feeling That Does Not Move | 🏆 **换脑级** |
| 理论框架 | 无明确理论 | Affective Publics (Papacharissi) + Hirschman Exit/Voice | 🏆 新建 |
| 核心概念 | 无 | **Skeptical Inertia（原创概念）** | 🏆 最值钱 |
| 研究设计 | 描述性趋势 | 中断时间序列 + 安慰剂检验 | 🏆 设计 |
| 情感工具验证 | 无 | 人工验证（150条，93.3%一致率）+ 偏差校正 | 🏆 方法论 |
| 表达类型学 | 无 | 4类双编码（Krippendorff's α=0.847） | 🏆 新质数据 |
| 参考文献 | 45条，格式问题多 | 质量更高，APA格式规范 | 🟢 改善 |

**龙虾评估：这已经不是那篇5.5的论文了。这是全新论文——理论上重新武装、方法上加了牙齿、概念上有了原创贡献。**

### 1.2 未发酵的潜在弱点（龙虾前瞻信号）

以下是我发现的「还没被市场注意到的」弱点——现在修复，审稿人就不会发现：

**🔥【未发酵】问题1：表达类型学4类间的互斥性存疑**
- 你的代码本定义"Information sharing" vs "Market expectation"——但一个"市场预期类"评论（如"明天券商必涨"）同时包含信息分享（引用政策）和情感宣泄（希望涨）。编码时很难干净分开。
- 建议：在方法部分明确说明"当评论可归入多类时，按主导意图编码"，并报告多类比例

**🔥【未发酵】问题2：中断时间序列的"无效应"≠真正的零效应**
- ITS检测的是一个阶跃变化——也就是说，如果政策效果是渐进展开的（而非一天之内），ITS会漏掉
- 你的结论说"不出所料，这个步骤几乎消失了"。但如果情感变化是linar trend change而不是level shift呢？ITS默认模型只测了level shift+slope change并存
- 建议：补充一个"仅slope change"模型作为鲁棒性检验

**🔥【未发酵】问题3：Skeptical Inertia是否真的与Censorship可区分？**
- 你论文中有一段很好的论证（Section 5）区分了demobilization和censorship，但这段论证目前完全依赖逻辑推演而非数据
- 审稿人很可能追问：你能用实际数据证明这不是删帖的结果吗？你观察到了多少比例的评论被删除/不可见？
- 建议：补充平台删除率数据或引用King, Pan & Roberts (2013)的具体数字作为佐证

### 1.3 龙虾评级

| 维度 | 评分 | 说明 |
|:----|:---:|:-----|
| 概念新颖性 | 9/10 | Skeptical Inertia是真正的原创贡献 |
| 方法论严谨性 | 8/10 | 有验证、有检验，但ITS局限性需补 |
| 理论贡献 | 9/10 | 为Affective Publics设定边界条件——这是顶级期刊要的 |
| 可投稿性 | 7/10 | 补以上3个未发酵问题后可达9/10 |

---

# 第二编 · 📘 Nature Writing 评估
## 🔬 Nature级别写作：结构、节奏、论证链

### 2.1 总体评估

论文达到了Nature Communications级别的写作水准。核心优势：

**✅ 标题顶级：** "Feeling That Does Not Move"——简洁、有记忆点、精准传达悖论。符合Nature系的"curiosity with credibility"原则

**✅ 摘要完美遵循"漏斗结构"：**
```
context → gap → approach → key finding → implication → boundary
```
每一步都有，信息密度高。特别欣赏最后一句用"precisely because they are demobilized"翻转预期

**✅ Hourglass结构执行到位：**
- Introduction: Broad (affective publics) → Narrow (our case, RQs) ✅
- Discussion: Narrow (our findings) → Broad (implications for theory) ✅

### 2.2 需要优化的问题

**⚠️ 问题1：Introduction篇幅过长（-3,500词）**
Nature级别的introduction不建议超过~2,000词。你的introduction有约3,500词，其中Section 2.5（investor publics on Chinese social media）可以大幅压缩。
- 建议：将2.5压缩为1段，核心信息（behavioral finance literature对sentiment的发现）整合到2.2或2.4末尾

**⚠️ 问题2：Section 3.3（Sentiment scoring）技术细节过多**
- 你花了约600词描述SnowNLP的validation过程。虽然这是论文的方法论亮点，但阅读节奏被打断
- 建议：主体保留300词+confusion matrix，详细的validation protocol移到appendix

**⚠️ 问题3：被动语态偏多**
- Nature-style倾向于主动语态+"we"为主语
- 多处如"The bias runs in a consistent direction"——可以改为"We find that the bias runs consistently..."

### 2.3 段落级检查

选取Section 4.1（The empirical heart）做段落诊断：
```
段落1（结果呈现）: ITS回归结果 ✅ 清晰
段落2（偏差校正）: 校正后结果 ✅ 有力
段落3（单个事件分析）: 无一个事件显著 ✅ 非常有力
段落4（安慰剂检验）: 12.8%的假阳性 ✅ 透明
段落5（稳健性检验）: 各种threshold ✅ 完整
段落6（结论段）: "skeptical inertia"定义 ✅ 强劲收尾
```

**段落结构评分：9.5/10**——每个段落一个核心信息，Sentence-to-sentence关系清晰，最后一段收得准。

### 2.4 Nature Writing 评分

| 维度 | 评分 | 说明 |
|:----|:---:|:-----|
| 标题 | 9/10 | 好，可再加副标题补充context |
| 摘要 | 9/10 | 完整漏斗结构，信息密度高 |
| Introduction | 7/10 | 偏长，2.5可压 |
| 结果叙述 | 9/10 | 段落结构优秀，证据链完整 |
| Discussion | 8/10 | 充分但可以更简洁 |
| 结论 | 8/10 | 清晰但可以加1句未来方向 |
| 整体 | 8.3/10 | 已到高水平，微调即可接近Nature子刊级别 |

---

# 第三编 · 🏯 唐太宗v3.0 · 15技能全流程评审

## 阶段1：输入评估

### 1.1 Data-finder ✅
- 数据源:Sina Weibo, 85,630条
- 时间窗口:2024.09-2025.01
- 来源明确，采集方法透明
- **建议：** 补充平台2024年月活数据的最新引用（文中引用Sina Weibo 2024，建议提供访问日期和URL）

### 1.2 Literature-scanner ✅
- 覆盖Affective Publics（Papacharissi）、平台研究（boyd, Gillespie, van Dijck）、行为金融（Baker & Wurgler, Tetlock）、情绪传染（Fowler & Christakis, Kramer）、中国社交媒体（Yang, King et al.）
- **缺漏：** 建议补充以下方向文献：
  - De Long et al. (1990, DSSW模型)——关于噪声交易者情感的经典论文（在behavioral finance文献中常被引用但你文中没有）
  - Barber & Odean (2008)——散户过度交易行为
  - 关于"情感极化"的更近期论文（情感极化×政策事件的交叉）

### 1.3 Hypothesis-generator ✅
- 论文本身不是假说驱动型，而是探索+理论建构型
- 三个RQ对应分析框架，RQ设计合理，从描述到解释再到理论推演
- **评价：** 符合传播学顶刊的研究问题设计规范

## 阶段2：分析评估（5技能并行）

### 2.1 Paper-summarize（骨架提取）
```
核心论题: 政策事件作为情感事件，调动了affective public，但情感被调动不代表公众被调动——Skeptical Inertia
数据: 85,630条Weibo评论
方法: SnowNLP + LDA + 人工验证(150条) + 表达类型学(400条双编码) + ITS + 安慰剂检验
核心发现: 原始2.7pp提升→校正后近零；无单个政策事件显著影响
理论贡献: 为Affective Publics理论设定边界条件——情感可以bind但不move
靶向期刊: IJoC（传播学Q2）
```

### 2.2 Paper-review（对抗式审查·拒稿风险矩阵）

| 风险维度 | 风险等级 | 具体问题 |
|:--------|:-------:|:--------|
| 理论贡献 | 🟢 低 | Skeptical Inertia原创性强，边界条件论点清晰 |
| 方法论 | 🟡 中 | ITS检测的是level shift—若情感是渐进change则漏检；SnowNLP校正假设误差率跨阶段稳定 |
| 逻辑一致性 | 🟢 低 | 全文论证链完整：RQ1(描述)→RQ2(纹理)→RQ3(理论) |
| 伦理/数据 | 🟢 低 | 声明了伦理豁免；数据来源正当 |
| 写作质量 | 🟢 低 | 高水平学术英文 |
| **综合拒稿风险** | **🟢 低（20-30%）** | **主要风险在：ITS设计局限+可能被质疑data snooping** |

### 2.3 Citation-audit（参考文献审计）

| 检查项 | 状态 | 说明 |
|:------|:----|:----|
| 引用完整性 | ⚠️ 缺若干篇 | 见上文Literature-scanner建议 |
| 格式合规 | ✅ | APA 7th，格式整体规范 |
| 文献重复 | ✅ 未发现 | — |
| 正文引用了但参考文献缺 | ⚠️ 未完全验证 | — |
| 参考文献中有未在正文引用 | ⚠️ 未完全验证 | — |
| **综合** | **🟢 良好** | **主要缺De Long et al. (1990)和Barber & Odean (2008)** |

### 2.4 Research-design（方法论评估）

| 维度 | 评分 | 说明 |
|:----|:---:|:-----|
| RQ与方法的对齐 | 9/10 | RQ1→ITS, RQ2→表达类型学+LDA, RQ3→理论推演 |
| 样本充分性 | 8/10 | 85,630条充足；ITS用123天df=117 |
| 情感工具验证 | 9/10 | 最亮眼的亮点之一，人工验证+校正 |
| 定性部分 | 8/10 | 400条双编码，α=0.847优秀 |
| 安慰剂检验 | 9/10 | 2,000次随机检验，87th百分位→诚实的报告 |
| 局限性明确 | 9/10 | Section 6优秀——不说"我们要改进"，说"这就是我们的边界" |
| **综合** | **8.7/10** | **方法轮上最扎实的部分** |

### 2.5 Deep-audit（深度方法论审计）

**核心发现：以上所有方法轮评估都指向一个弱点——ITS对渐进变化的敏感性**

```
你使用了: Y_t = β₀ + β₁T + β₂D + β₃(T×D) + ε_t
          其中D=1 for post-9/24, T=time trend
          
这个模型检测两个东西：
  - β₂: level shift（阶跃）  
  - β₃: slope change（趋势变化）

你报告了β₂显著（原始），β₃未显著或未报告？
如果未报告β₃，我强烈建议补充"β₃不显著"的说明——否则审稿人会问
```

**第二个深层问题：情感的正自相关（AR(1)=0.23）**

你提到了这个自相关（Section 4.1末尾），说明你意识到了。但：如果每天的情感≈87%来自前一天，ITS的误差项之间就不是独立的。你用Newey-West HAC SE来处理是对的——建议明确写"HAC校正到lag=5"等具体参数。

## 阶段3：执行层（条件触发）

### 3.1 Data-analysis
- 复现性评估：方法描述详细（ITS公式、LDA参数、阈值），可复现性高
- 需要补充：SnowNLP版本号、jieba版本号、random seed设置

### 3.2 Text-analysis-cn (cntext WEPA)
- 文中未使用cntext WEPA（仍用SnowNLP）——但你做了人工验证作为替代
- 用WEPA替代SnowNLP可以作为一种methodological contribution说明（或放到future work）

### 3.3 Topic-modeling (keyATM)
- 文中仍用LDA（c_v=0.31-0.49）——你诚实报告了低coherence
- 这是论文的一个明确弱点。建议：用keyATM或至少做一个5-10话题的keyATM sensitivity analysis

### 3.4 Causal-audit
- ITS设计不能严格证明因果——你诚实地称之为"quasi-experimental"
- 安慰剂检验是好做法
- 没有工具变量、没有RD设计——对于传播学论文，ITS+安慰剂是合理的上限

## 阶段4：辩论矩阵

### 核心矛盾发现

| 技能对 | 矛盾 | 解决 |
|:------|:----|:----|
| paper-review vs research-design | 理论贡献高但ITS可能漏检 | 补充slope-only模型 |
| deep-audit vs 结论 | 自相关会削弱ITS的效力 | 你已经提到HAC SE，再加说明 |
| citation-audit vs literature | 缺De Long et al. | 补上（参考文献中加一篇） |

### 统一修改清单

**🔴 P0（必须改，不改有拒稿风险）：**
1. 补充ITS的"仅slope change"模型作为robustness check
2. 明确报告β₃（slope change）是否显著
3. 说明HAC SE的lag选择（lag=5？Newey-West默认？）

**🟡 P1（建议改，提升质量）：**
4. 补充De Long et al. (1990)和Barber & Odean (2008)到参考文献
5. 对LDA低coherence的讨论加一段keyATM的可行性展望
6. 表达类型学代码本加"主导意图"规则说明

**🟢 P2（可改可不改，锦上添花）：**
7. 2.5节压缩为1段
8. 3.3节的部分细节移入Appendix
9. 多处量化主动语态（we find / we observe）

## 阶段5：输出

### 5.1 Diagram-maker评估

当前图表（按文中引用顺序）：
- Figure 1 — 情感vs评论量时间序列 ✅ 核心图，好
- Figure 2 — 情感比例按阶段 ✅ 有效展示distribution
- Figures 3-6 — LDA话题词各阶段 ✅ 标准呈现
- Figure 7 — 话题随时间变化 ✅ 好
- Figure 8 — 原始vs校正后情感 ✅ **最核心图**

**建议增补：**
- Figure 9 — ITS结果可视化（intervention effect + counterfactual），这是审稿人最想看到的

### 5.2 综合评分

| 唐太宗维度 | 评分 |
|:---------|:---:|
| 理论贡献 | 9/10 |
| 方法论质量 | 8.5/10 |
| 逻辑一致性 | 9/10 |
| 写作/呈现 | 8/10 |
| 参考文献 | 7.5/10 |
| **综合** | **8.4/10** |

---

# 第四编 · 👑 李世民计划 — 科研管理评估

## 4.1 论文历史回顾

| 日期 | 版本 | 状态 | 评分 |
|:----|:----|:----|:---:|
| 6/4 | v1（投资者情感） | 唐太宗首次评审 | 5.5/10 |
| 6/11 | 唐太宗v3.0升级 | 方法论升级路径确认 | — |
| 6/19 | **v37** | **IJoC投稿终版** | **8.4/10** |

**从5.5到8.4：这个版本的变化相当于换了篇论文。**
理论上从"无框架→Affective Publics"，方法从"描述→准实验+验证"，概念从"无→Skeptical Inertia"。

## 4.2 投稿策略评估

### IJoC匹配度分析

| 维度 | 匹配度 | 说明 |
|:----|:-----:|:----|
| 话题匹配度 | 🟢 高 | 传播学的数字媒体/情感/平台研究，完全在IJoC scope内 |
| 方法论 | 🟢 高 | 计算传播学方法是IJoC近年偏好的方向 |
| 理论贡献 | 🟢 高 | 设定理论边界条件是IJoC这种理论导向期刊喜欢的 |
| 中国数据 | 🟡 中 | 这是优势（独特数据）也可能是审稿限制（部分审稿人不熟悉中国语境） |
| 靶向期刊定位 | 🟢 高 | IJoC明确欢迎"communication research from underrepresented regions" |

**投稿策略结论：** IJoC是合适的靶向——Q2期刊但影响力高。如果被拒，下一个可考虑：
- **Plan B:** Social Media + Society (SSCI Q1)——更贴合，但要求更高的平台分析深度
- **Plan C:** Convergence (SSCI Q2)——已投过DES论文，熟悉
- **Plan D:** Information, Communication & Society (SSCI Q1)——完美的理论配对，但竞争激烈

## 4.3 科研体系诊断

**朱元璋+唐太宗+龙虾的协同效果：**
- ✅ 唐太宗15技能 + 龙虾前瞻视角 = 比传统peer review更全面
- ✅ 理论+方法+写作+文献的全覆盖
- ⚠️ 当前过程耗时较长（全系统评审耗时约30分钟）→ 可优化为半自动化

**本次系统级改进建议：**
1. 论文v37 → v38只需要改P0问题（约2小时）即可提交
2. IJoC审稿周期通常8-12周，提交后应该开始下一个项目
3. 下个项目建议：利用本文Weibo数据做一篇更方法论的论文（对比SnowNLP/WEPA/Lexicon-based的性能论），可投Journal of Computational Social Science

---

# 总结：综合评价

## 五维雷达图

```
                   理论贡献 (9/10)
                    /
                   /
    参考文献 (7/10)  ——— 方法论 (8.5/10)
                |     |
    写作质量 (8/10) ——— IJoC匹配度 (8/10)
```

## 一句话

> **v37已经不是那篇5.5分的论文了。这是一个理论上重新武装、方法上加了牙齿、概念上做了原创贡献的8.4分稿件。补3个P0问题，就可以提交了。**

## 关键行动项

| 优先级 | 事项 | 估计时间 |
|:-----:|:----|:-------:|
| 🔴 P0 | 补充ITS slope-only模型检验 | 30分钟 |
| 🔴 P0 | 明确报告β₃ + HAC lag参数 | 15分钟 |
| 🔴 P0 | 补充De Long et al. (1990) | 10分钟 |
| 🟡 P1 | 表达类型学代码本补充说明 | 20分钟 |
| 🟡 P1 | 2.5节压缩 | 30分钟 |
| 🟡 P1 | 主动语态修改全文 | 45分钟 |
| 🟢 P2 | keyATM敏感性分析（可选） | 2小时 |
| 🟢 P2 | 加Figure 9 ITS可视化 | 1小时 |
| **合计** | **P0 = 55分钟，全算 = 5.5小时** | |
