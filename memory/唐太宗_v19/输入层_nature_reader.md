# 唐太宗 v3.0 输入层 + nature-reader 分析

> **论文路径:** /Users/lyu/.openclaw/workspace/memory/A股_顶刊重构_v19_text.txt
> **分析日期:** 2026-06-15
> **分析技能:** nature-reader / paper-summarize + hypothesis-generator + literature-scanner

---

## === skill 1: nature-reader / paper-summarize ===

### 更新后标题

**Affective Publics under Policy Shocks: Skeptical Inertia in Chinese Retail Investors' Social-Media Response to Macroeconomic Interventions**

---

### 一、核心论题（Core Thesis）

**Thesis Statement:**
Macroeconomic policy interventions function as affective events that summon a public on Chinese social media, yet this public's collective feeling does not respond to even the most intensive stimulus. The public is intensely present and densely networked but neither deliberates nor mobilizes, settling into a configuration the paper terms **skeptical inertia** — a durable, experience-hardened wariness that intensive policy can stir into activity but cannot move in its affective direction.

**核心论点陈述（中文）：**
宏观经济政策干预不仅是经济事件，更是情感事件（affective events），它们会在中国社交媒体上召唤出特定的公众（public）。然而，即便面对2024年9月至2025年1月间中国A股市场有史以来最密集的刺激政策周期，该公众的集体情感并未被有效移动。该公众虽然高度在场、密集互联，但既不协商（deliberate）也不动员（mobilize），陷入一种论文称之为 **怀疑性惯性（skeptical inertia）** 的持久状态——经验锤炼出的警惕使得政策可以激发其活动（参与量飙升）却无法改变其情感方向。

**Central counterintuitive claim:**
情感可以构成并维系一个公众，却从未使其动员——demobilized affective public 是理论的一个边界条件（boundary condition），而非理论的失败案例。

---

### 二、理论与文献定位（Theoretical & Literature Positioning）

#### 2.1 核心理论框架

| 理论支柱 | 来源 | 论文定位 |
|:---------|:-----|:---------|
| **Affective Publics** | Papacharissi (2015, 2016) | 主框架。帕帕查理希的情感公众理论——以情感而非理性协商维系的网络化形成。论文将其从"动员性"拓展至"非动员性"边界条件 |
| **Exit / Voice / Loyalty** | Hirschman (1970) | 辅助框架。Hirschman的经典三元组——退出、发声、忠诚。论文提出第四种模式：**skeptical inertia**，它既非退出（公众始终在场），亦非发声（几乎不协商、不异议），也不是忠诚（不基于认同与信任，而基于希望与失望的悬置对峙） |
| **Emotional Contagion** | Fowler & Christakis (2008); Kramer et al. (2014) | 微观机制。情感在网络中传播的机制，为集体情感何以同步但不转化提供潜在解释 |
| **Platform Affordances** | boyd (2010); Gillespie (2014); van Dijck, Poell & de Waal (2018); Bucher & Helmond (2018); Poell, Nieborg & van Dijck (2019) | 方法论与解释框架。新浪微博的可见性算法、话题聚合、内容审查如何塑造了该公众的情感表达 |
| **Networked Publics** | boyd (2010); Papacharissi (2015) | 辅助框架。持久性( persistence )、可缩放性( scalability )、可搜索性( searchability )如何重组公众的集结方式 |
| **Risk Society** | Beck (1992) | 延伸解释。在普遍的决策不确定性下，个体转向媒介化集体来阐释和感受自己无法计算的后果 |
| **Behavioral Finance** | Baker & Wurgler (2007); Li & Ahn (2024); Cookson, Engelberg & Mullins (2023); Duan, Liu & Wang (2021) | 被批判性对话的对象。行为金融学将sentiment视为市场价格的标量预测指标；论文将其重新框架化为public的联结组织 |

#### 2.2 关键文献对话

**与Papacharissi的对话：**
- 继承：情感公众的核心定义——情感而非论证是联结的纽带
- 拓展：paradigmatic cases（Tahrir, Occupy, #BLM）都是情感推动行动；论文展示边界案例——情感可以构成公众却从未动员
- 修正：Papacharissi的"connective yet not necessarily collective action"原文将此视为contingent shortfall；论文证明此gap可以是公众的settled condition
- 提出：**connective intensity与mobilizational potential是可分离的维度**

**与Hirschman的对话：**
- 继承：exit/voice/loyalty是组织衰退情境下理性选择的三元模型
- 突破：中国A股散户公众占据一个三元组未覆盖的位置——在场但不发声，参与但不行动，既不是退出也不是异议
- 提出skeptical inertia作为第四种模式：held in place not by loyalty but by a standoff between hope and disaffection

**与行为金融学的对话：**
- 批判：sentiment被工具化为价格预测器，极少追问公众自身在做什么
- 转向：从"哪些方向？"（集市预测）到"情感公众如何围绕国家行动集结、调谐、分散？"
- 恢复情感的社会性和公众性维度

---

### 三、数据与方法（Data & Method）

#### 3.1 数据

| 维度 | 细节 |
|:-----|:------|
| **数据源** | 新浪微博（Sina Weibo），非专业投资者主导的泛化社交平台 |
| **时间窗口** | 2024年9月1日 — 2025年1月28日（5个月，123天） |
| **原始采集** | 98,717条原始评论 |
| **清洗后** | 85,770条（去重、去广告、去非实质性字符串、中文分词后） |
| **分析样本** | 85,630条（一个细微数字差异，85,770与85,630间可能是进一步过滤） |
| **分层验证** | 150条机器评分分层抽样进行人工验证 |
| **表达分类** | 400条按阶段分层随机抽样（每阶段100条）进行人工双人编码 |

#### 3.2 情感评分方法

| 工具 | 说明 | 局限 |
|:----|:-----|:-----|
| **SnowNLP** | 基于词典+模型的中文工具，返回[0,1]连续分值 | 正负精度低（正类precision 14%）；系统性高估正向情感；大量反讽被误读为积极 |
| **阈值** | positive > 0.6, negative < 0.4, neutral ∈ [0.4, 0.6] | 对称设定 |
| **人工验证** | 2位编码员独立标注150条分层层样本（Krippendorff's α = .892） | 校正后估计：正18%, 负35%, 中47% |
| **严格阈值** | positive > 0.8, negative < 0.2的稳健性检验 | 同样模式 |

#### 3.3 主题建模

- **方法**: Latent Dirichlet Allocation (LDA), k=4 per stage
- **工具**: gensim (LdaModel)
- **参数**: α=0.1, β=0.01, 20 passes, 400 iterations
- **评价**: C_v coherence = 0.31–0.49（较低，因评论简短口语化）
- **稳健性**: k=10时coherence ~0.43，但主题碎片化为positioning-and-flows的变体；保留k=4

#### 3.4 表达类型学编码

| 类别 | 定义 | 示例 |
|:-----|:-----|:------|
| **Information sharing** | 传递事实（政策细节、数据） | "央行降准0.5个百分点" |
| **Policy evaluation** | 评估政策有效性/真诚性 | "没用，机构在跑" |
| **Market expectation** | 预测/定位未来市场方向 | "三天内不收回这根阴线，牛就是假的" |
| **Emotional venting** | 表达感受（损失、焦虑、黑色幽默） | "亏了15%要涨20%才能回本" |
| **Other/mixed** | 无法单一归类的残余项 | — |

#### 3.5 因果识别设计

**三层次验证：**

1. **ITS (Interrupted Time-Series) 单断点模型**
   - 断点：2024年9月24日（密集刺激期起点）
   - 因变量：日度平均情感值
   - 估计：截距位移 + 斜率变化
   - 标准误：Newey-West (HAC)
   - 结果：小幅度上升截距位移（b=0.036, p=.042），但控制星期效应后不显著（p=.057）；斜率无变化（p=.74）

2. **四事件逐事件估计**
   - 9月24日降息降准：p=.09
   - 9月26日政治局会议：p=.72
   - 10月8日发改委发布会：p=.38
   - 11月8日化债方案：p=.45
   - **均不显著**

3. **安慰剂检验**
   - 200个随机非事件日期重新估计位移
   - 真实估计值被37.5%的安慰剂断点超过
   - 真实值低于安慰剂分布的第95百分位
   - 结论：可检测的唯一效应与日常波动无异

---

### 四、核心发现（Core Findings）

#### Finding 1: 情感不响应 —— 政策冲击未改变集体情感

**（支持RQ1的核心发现）**

- 四个旗舰政策事件均未产生统计显著的情感变化
- 安慰剂检验确认唯一"效应"与噪声无法区分
- 情感强度（affective intensity）完全不移动（b=0.001, p=.89）
- 参与量（comment volume）剧烈波动（CV=0.49），但情感强度几乎平坦（CV=0.029）—— 人群到了但情感温度不变
- 情感序列自相关（AR(1)=0.23）：今天的情感由昨天主导，非当天政策

#### Finding 2: 公众做什么而非协商

**（支持RQ2的核心发现）**

表达类型分析：
| 类型 | 占比 |
|:-----|:-----|
| **Emotional venting** | ~36% |
| **Market expectation** | ~34% |
| **Policy evaluation** | ~5% |
| **Information sharing** | <2% |

- **中位数评论长度: 13个字符**；57.9%不足15字符
- **说理性语言**（因为、原因、分析）：仅出现在3.2%评论中
- **第一人称单数**（我买了/我亏了/我被套了）：出现的频率是第一人称复数（我们/一起/团结）的约30倍
- **集体行动语言**：<0.1%
- **明确不信任**（被收割/空话）：<1%
- 该公众不质疑国家行为，不呼吁集体行动，将政策迅速转化为私人的损益计算

**阶段转移：**
- 政策前：预测性表达主导（~45%）
- 政策后：情感宣泄稳步上升（从~20%到观察阶段的~50%）
- 公众从"对着期待的未来定位"转向"集体表达未实现未来的失望"

#### Finding 3: 边界条件 —— 情感公众可以是去动员化的

**（支持RQ3的核心发现）**

- Papacharissi的范本案例（Tahrir, Occupy）中情感→连接→行动；
- 本文展示情感→连接∧¬行动（情感构成并维系公众但从不动员）
- **Connective intensity 与 mobilizational potential 是可分离的维度**
- 去动员化的情感公众因其非动员性而**更具持久性**（durable precisely because demobilized）
- 公众的情感框架是**个体化且结果导向的**（what I bought, what I lost），阻止了个体损失转化为集体行动的语言条件
- 在Hirschman的术语中：个体化的、结果导向的框架是阻止voice而不刺激exit的机制——"我的损失"而非"我们的处境"，没有通向集体抗议的自然路径，但也无理由退出

---

### 五、理论贡献（Theoretical Contributions）

#### 贡献1：Affective Publics 理论的边界条件

- 情感可以构成并维系公众却不使其动员 → 理论的范围条件被明确化
- 情感驱动的公众不必然是 "waiting to tip into action"
- 情感与行动之间的链接是有条件的（conditional on framing）

#### 贡献2：提出 "Skeptical Inertia" 作为第四种公众反应模式

- Hirschman(1970)的Exit/Voice/Loyalty三元组之外
- 定义：持久在场但不发声，既不退出也不异议，被希望与失望的悬置对峙所固定
- 不是 weaker voice，不是 loyalty variant，而是 **distinct fourth mode**

#### 贡献3：Connective Intensity 与 Mobilizational Potential 可分离

- 两个维度的提出：情感联结的强度（高） vs. 动员潜力（低）
- 高联结-低动员的公众是其理论的明确边界

#### 贡献4：方法论的透明可复现模板

- 情感分析 + 主题建模 + 人工验证表达类型 + ITS准实验设计 + 安慰剂检验
- 将大规模评论语料读作情感公众在政治-经济事件周围集结的trace
- 明确平台边界条件

---

### 六、边界条件（Boundary Conditions / Limitations）

| 边界 | 具体内容 |
|:-----|:---------|
| **识别策略边界** | 准实验而非实验设计；ITS+安慰剂支持零效应的因果解读，但阶段间描述性对比应仅视为关联而非因果 |
| **平台边界** | 新浪微博的可见性算法、推荐流、审查与自我审查塑造了可观察的情感；不推广至专业投资平台或被平台压制的反应 |
| **测量边界** | SnowNLP仅返回极性（polarity）而非表达类型（venting, irony, solidarity）；反讽被系统性误读；绝对比例应视为inditative而非精确值 |
| **主题模型边界** | 连贯性较低（0.31–0.49），标签是研究者辅助的解释而非完全数据驱动的分类 |
| **公众异质性边界** | 将投资者视为单一公众；未区分价值投资者、动量交易者、短线参与者 |

---

## === skill 2: hypothesis-generator ===

### 从三个核心发现生成可检验的竞争性假说

#### 假说生成原则

以下竞争性假说（competing hypotheses）基于论文的三个核心发现，分别提出alternative explanations，并用Popperian原则表述为"原则上可被证伪"的陈述。每个假说均附检验策略与所需数据。

---

##### 发现1：政策冲击不改变集体情感（零效应）

**H₁_Original：** 政策冲击不改变公众集体情感，因为公众已进入"怀疑性惯性"的循环——反复失望形成经验性警觉，即使密集刺激也不足以打破基线。

**竞争性假说 H₁a：聚合噪音假说（Aggregation Artifact Hypothesis）**

> **假说**：微博用户评论中可检测到的政策冲击情感效应不为零，但被跨用户群体的异质性反应互相抵消——积极反应者与消极反应者同时增加，使得日度均值（以及以均值为基础的情感强度）保持不变。

- **Popperian可检验性**：如果跨评论情感分布的双峰性（bimodality）在政策事件后的短时间内显著增加，而均值同时保持稳定，则H₁a得到支持。
- **检验策略**：对每个政策事件7天窗口内的情感得分分布，计算Hartigan's dip statistic 或 bimodality coefficient (BC)，与事件前基准分布比较。若BC显著上升但均值不变，则支持H₁a。
- **所需数据**：已有85,630条评论的微观情感得分值（SnowNLP scores）；需要未聚合到日度的单条评论情感数据。

**竞争性假说 H₁b：测量不敏感假说（Measurement Insensitivity Hypothesis）**

> **假说**：SnowNLP的低分类精度（正类precision仅14%）和系统性高估正向情感，使得真实存在的情感变化被测量误差掩盖——特别是在反讽和黑色幽默密集的A股讨论语境中，情感信号的信噪比过低。

- **Popperian可检验性**：如果使用针对金融反讽语境训练的BERT/GPT情感模型（fine-tuned on Chinese stock market irony corpus），政策事件日的情感变化大于SnowNLP版本且达到统计显著，则H₁b得到支持。
- **检验策略**：构建Chinese Stock Market Irony Corpus（CSMIC），微调Chinese BERT或ChatGLM情感分类模型，重新评分全部85,630条评论，重复ITS分析。
- **所需数据**：现有语料的人工反讽标注（论文已有150条验证样本及10条讽刺性discordant cases可以作为种子数据）。

**竞争性假说 H₁c：平台干预假说（Platform Curation Hypothesis）**

> **假说**：微博的平台算法（推荐流、热搜）和内容审查机制在政策事件期间有系统性偏倚——倾向展示中立或弱负面的表达以维持"可控"舆论面貌，从而在采集端人为压缩了情感方差，使政策冲击时期的真实情感波动不可见。

- **Popperian可检验性**：如果微博API在同一政策事件期间的公开可见评论与后台全量评论的情感分布有系统性差异（全量数据更极化或更情绪化），则H₁c得到支持。
- **检验策略**：通过微博内部数据或第三方镜像（如爬取所有回复而非仅热门评论），比较同一政策事件窗口内"高可见性"评论（热搜/推荐位）与"低可见性"评论的情感分布差异；或重复分析在专业投资者平台（雪球/Xueqiu）上的对应时间段数据——后者审查力度不同。
- **所需数据**：多层级可见性数据（热搜vs非热搜）或跨平台可比数据集（微博vs雪球）。

---

##### 发现2：公众以情绪宣泄和预期表达为主，极少协商或信息分享

**H₂_Original：** 该公众之所以不协商、不移情，是因为它在情感上被经验性警觉锁定，将政策事件迅速转化为私人损益计算，缺乏将感受框架化为集体行动的语言条件。

**竞争性假说 H₂a：平台短期形态假说（Platform Brevity Hypothesis）**

> **假说**：评论短（中位数13字符）、不协商，不是因为情感锁定，而是因为微博平台形态的约束——其信息流交互模式天然不利于说理性表达，而偏好快速情感信号。如果将同样的用户群迁移到架构不同的平台（如长文论坛、私密群组），同一公众在政策事件后的表达将以信息分享和协商为主。

- **Popperian可检验性**：如果在同一政策周期中，来自雪球（长帖/讨论串模式）的A股投资者评论，其平均长度显著大于微博内容，且信息分享+政策评估占比不低于情绪宣泄占比，则H₂a得到支持。
- **检验策略**：采集雪球（Xueqiu）在同一时间段（2024年9月–2025年1月）的A股讨论帖，使用同样的表达类型编码方案（Krippendorff's α可靠性确认），跨平台比较四类表达的占比分布。
- **所需数据**：雪球API或爬虫在同一时间窗口内的帖子和评论数据。

**竞争性假说 H₂b：学科迁移假说（Analyst Capture Hypothesis）**

> **假说**：在微博金融讨论区，以情感为主的表达恰恰是理性、信息丰富的——散户投资者通过情感暗号（sarcasm, gallows humor, coded allusions）传递非正式市场分析，避免被监管系统识别为"非法投资咨询"，从而在表面上呈现为情绪宣泄，实际上承载了实质性信息交换。

- **Popperian可检验性**：如果将情感性表达（如"被收割了"）与后续实际交易行为（如换手率增加、对应板块资金流出）联系起来，发现情绪性表达的某些类别与未来市场走向显著相关，则H₂b得到支持。
- **检验策略**：建立评论级情感-交易行为链接——将每条含有情绪宣泄表达的评论聚类后，与该评论提出的具体市场判断（隐含的、暗语式的）与t+1到t+5的板块实际表现进行外推比较。
- **所需数据**：需要关联评论中隐含的投资方向判断与对应板块/个股的实际价格走势；需要更精细的评论级主题标注。

**竞争性假说 H₂c：政治表达替代假说（Muting Hypothesis）**

> **假说**：缺乏明确的政策评估和异议不是"情感锁定"的结果，而是内容审查下理性成本收益计算的结果：明确的政策批评导致删帖或账号风险，所以用户将批评转化为讽刺和体化的情感宣泄。如果审查压力降低，政策评估类的表达将显著上升。

- **Popperian可检验性**：如果在一个审查压力显著不同的时期（如中国市场的"政策宽松期"、或跨平台对比审查力度较弱的海外华人投资者论坛），政策评估类表达占比显著提升，则H₂c得到支持。
- **检验策略**：选取可比的A股政策事件但发生在审查周期不同阶段的语料；或对比微博与海外华人投资者论坛（如WallStreetBets中文版、Reddit的r/ChinaStocks）在同一政策事件后的表达差异。
- **所需数据**：跨平台（跨境）的可比政策事件数据。

---

##### 发现3：情感公众可以是去动员化的——connective intensity与mobilizational potential可分离

**H₃_Original：** A股公众是一个高联结-低动员的情感公众，其非动员性使其更具持久性；情感框架的个体化和结果导向阻止了集体行动的转化。

**竞争性假说 H₃a：集体行动可见度假说（Collective Action Visibility Hypothesis）**

> **假说**：该公众并非不具有动员潜力，而是其动员发生在论文观测窗口之外——社交媒体上的情感表达是被识别和感受到的，但动员行为（如联合抵制IPO、集体撤资运动）被平台迅速压制，在可见语料中被快速删除，因此"不存在"是审查的产物而非公众的事实状态。

- **Popperian可检验性**：如果在同一时间段，同一平台上有其他领域的集体行动可见（如在微博上可见的消费者集体维权、粉丝集体行动等），且A股投资者领域没有类似的可见集体行动，而审查力度在'财经'板块与'社会'板块之间无系统性差异，则H₃a面临挑战。
- **检验策略**：在同时段微博数据中，系统搜索集体行动相关关键词（如"联合维权"、"一起抵制"、"集体投诉"）在不同板块的分布频率；同时使用Wayback Machine检查被删除的历史讨论记录。
- **所需数据**：带删除追踪能力的微博纵向数据集。

**竞争性假说 H₃b：触发阈值假说（Threshold Trigger Hypothesis）**

> **假说**：connective intensity与mobilizational potential并非永久分离，而是呈现非线性关系——只有情感强度超过某个阈值时动员才会触发。论文观察到的窗口期内强度始终低于阈值，但若政策效果更极端（如市场单日暴跌超过20%），或外部叠加事件（如券商破产、银行挤兑），动员将发生。

- **Popperian可检验性**：如果在一个更极端的中国市场冲击事件中（如2015年股灾、2016年熔断），同一平台上的公众展示出可观察的集体行动动员（如联合呼吁、组织化维权），则H₃b得到支持——connective intensity与mobilizational potential确实可分离，但仅存在于特定强度范围内。
- **检验策略**：选取2015年6–8月或2016年1月（熔断）作为历史案例，在同一平台（微博）进行可比分析：情感强度+表达类型+集体行动语言，对比2024–2025年窗口。
- **所需数据**：微博2015–2016年同类型窗口的历史数据。

**竞争性假说 H₃c：学习效应假说（Learning Habituation Hypothesis）**

> **假说**：2024–2025年的"非动员"状态不是情感公众的固有特征，而是已被先前政策经验"消化"了——2015年股灾后散户经历了动员（维权抗议）→失望→精力消耗的周期，至2024年已进入厌倦期。如果在政策周期更早的阶段（如2024年9月的第一次密集刺激），动员潜力仍然存在但在数据中被遗忘。

- **Popperian可检验性**：如果在2024年9月24日第一次政策冲击前1–2周内，微博讨论中的集体行动语言（"我们""一起""联合"）的频率显著高于政策冲击后，且在2024年9月24日当天瞬时出现一个小幅动员峰值后迅速衰减，则H₃c得到支持——确实存在动员潜力的短暂爆发但很快被"学习效应"吸收。
- **检验策略**：逐日追踪集体行动语言频率的时间序列，聚焦2024年9月10日至10月10日窗口，使用更细粒度的时间粒度（小时级或分钟级）检测瞬时动员峰值。
- **所需数据**：更高时间分辨率的评论数据，特别关注2024年9月窗口内的子小时级汇总。

---

### 假说与论文对话小结

| 竞争性假说 | 挑战的对象 | 可被论文现有数据部分回答？ | 需要的新数据 |
|:-----------|:-----------|:---------------------------|:-------------|
| H₁a 聚合假说 | Finding 1（零效应） | 是，已有微观数据 | 未聚合的评论级情感得分 |
| H₁b 测量不敏感假说 | Finding 1（零效应） | 部分，已有验证样本 | 反讽语料微调的情感模型 |
| H₁c 平台干预假说 | Finding 1（零效应） | 否 | 多层级可见性或跨平台数据 |
| H₂a 平台短期形态假说 | Finding 2（表达类型） | 否 | 雪球等长文平台同期数据 |
| H₂b 学科迁移假说 | Finding 2（表达类型） | 否 | 更精细的评论级暗号标注 |
| H₂c 政治表达替代假说 | Finding 2（表达类型） | 否 | 跨审查周期的数据 |
| H₃a 集体行动可见度假说 | Finding 3（去动员） | 否 | 带删除追踪的数据 |
| H₃b 触发阈值假说 | Finding 3（去动员） | 否 | 历史金融危机数据 |
| H₃c 学习效应假说 | Finding 3（去动员） | 是，但需小时级粒度 | 更高时间分辨率的重采样 |

---

## === skill 3: literature-scanner ===

### 文献定位完整性评估

#### 3.1 文献覆盖的强度

| 评估维度 | 评价 |
|:---------|:------|
| **情感公众理论** (Papacharissi) | ⭐⭐⭐⭐⭐ **极其完整**。从核心专著到期刊论文均有引用，包括Papacharissi 2015专著和2016 journal article。论文的全文定位就是对该理论的扩展与边界条件化 |
| **Exit / Voice / Loyalty** (Hirschman) | ⭐⭐⭐⭐ **较强**。1970年经典清晰引用且是核心理论对话对象。可增强：更近期的Hirschman scholarship扩展（如关于neglect的研究）；第四种模式已有先例文献（如"loyalty as inertia"的讨论） |
| **情感传播/情绪传染** (Kramer et al.; Fowler & Christakis) | ⭐⭐⭐⭐ **较强**。引用了标志性研究并明确指出其设计争议；可作为micro-mechanism的构建完整 |
| **平台可供性** (boyd; van Dijck et al.) | ⭐⭐⭐⭐⭐ **极其完整**。覆盖了boyd 2010经典，van Dijck, Poell & de Waal 2018的platform society，Gillespie 2014的algorithmic relevance，Bucher & Helmond 2018的affordances，Poell, Nieborg & van Dijck 2019的platformisation——这一区块是论文方法论解释层的坚实支撑 |
| **网络公众理论** | ⭐⭐⭐⭐ **较强**。但可考虑纳入Bennett & Segerberg (2012)的connective action理论——与本文的"情感联结而非集体行动"话题高度相关，且在正文中未被引用（仅在参考文献中出现）。这一缺失值得注意 |
| **行为金融学** (Baker & Wurgler; Duan et al.; Li & Ahn; Cookson et al.) | ⭐⭐⭐⭐ **较强**。核心文献覆盖完整，但可增加Tetlock (2007)的media sentiment开创性工作（见参考文献）和关于retail investor attention的经典研究（如Da, Engelberg & Gao 2011） |
| **中国网络社会/审查研究** (Yang) | ⭐⭐⭐ **中等**。仅引用Yang (2009)较早期的Internet activism研究。最近的数字威权主义/平台治理文献（如King, Pan & Roberts 2013/2017; Roberts 2018; Chen & Yang 2019）未被纳入。在依赖审查假设时（self-censorship shaping expression），这构成一个gap |
| **散户行为研究** | ⭐ **薄弱**。虽然领域是行为金融学对话，但论文几乎未引用关于散户（retail investors）行为本身的研究（如Barber, Odean等人的经典研究；中国散户特有的行为偏差文献如高频交易、追涨杀跌、注意力驱动交易等）。这与论文声称理解"散户公众"的雄心形成对比 |
| **舆论与公共领域理论** (Habermas); 网络舆论的最新批判性评估 (Ojala & Ripatti-Torniainen) | ⭐⭐⭐ **中等**。引用了Ojala & Ripatti-Torniainen (2024)对networked publics理论的批判，但Habermas的public sphere或deliberative democracy的传统未充分建立对话 |

#### 3.2 Gap陈述评估

论文的gap陈述出现在Section 2.5末尾：

> "Yet this literature has a characteristic blind spot. Because its dependent variable is almost always the market—returns, volatility, turnover—it treats sentiment instrumentally, as a predictor to be extracted and validated against price, and rarely asks what the public is doing in its own right..."

**强度评估：**

| 标准 | 评估 | 评价 |
|:-----|:-----|:------|
| **明确性** | ⭐⭐⭐⭐ | 清晰陈述了行为金融学将sentiment工具化、忽略公众自身行为的盲点 |
| **空间范围** | ⭐⭐⭐ | 主要针对行为金融学文献。但论文声称填补的更大gap（情感公众理论的边界条件），在gap陈述中更间接——需要从"communication-side question"中推导 |
| **原创性** | ⭐⭐⭐⭐⭐ | 将sentiment重新框架化为公众的connective tissue而非市场预测器，是一个有力的gap定位 |
| **可操作性** | ⭐⭐⭐⭐ | gap导向了明确的研究问题和可操作的分析策略（从predictor转向公众形成、调谐、分散） |

**增强建议：**

1. **明确双重gap定位**：当前gap陈述主要针对行为金融学（literature gap），但论文更大的gap——affective publics理论中"feeling can constitute a public without mobilizing it"的边界条件（theoretical gap）——在2.1节通过Ojala & Ripatti-Torniainen的批判引入，却在Gap陈述中未明确并置。建议在2.5节的Gap陈述中明确标识双重gap。

2. **作者已预见的文献覆盖不足**：
   - Bennett & Segerberg (2012)的connective action仅出现在参考文献，正文零引用——这构成了论文"connective action without collective action"论证的潜在文献支撑也在参考文献中
   - King, Pan & Roberts的censorship实证研究未被纳入，在依赖self-censorship假设时削弱了论证的文献根基
   - 散户行为文献的缺失，使论文对"散户公众"的描述在行为层面缺乏文献锚点

3. **方法论的文献支撑**：ITS + 安慰剂检验虽是标准工具，但论文未引用社交网络中ITS方法学的最新讨论（如在computational communication science中ITS的使用案例）。这更像是方法透明度的缺失而非gap。

#### 3.3 参考文献完整度评估

| 引用域 | 总引用数（约） | 典型覆盖 | 缺失的关键文献 |
|:-------|:---------------|:---------|:---------------|
| Affective publics / emotion in communication | 5 | Papacharissi 2015, 2016; Wahl-Jorgensen 2019; Ahmed 2004; Ojala & Ripatti-Torniainen 2024 | — |
| Platform affordances | 7 | boyd 2010; Gillespie 2014; Bucher & Helmond 2018; van Dijck et al. 2018; Poell et al. 2019; Hillis, Paasonen & Petit 2015 | — |
| Behavioral finance / market sentiment | 7 | Baker & Wurgler 2007; Duan et al. 2021; Li & Ahn 2024; Cookson et al. 2023; Tetlock 2007; Bollen et al. 2011; Gu & Kurov 2020 | Da, Engelberg & Gao (2011); Barber & Odean (2008); Grinblatt & Keloharju (2001) |
| Chinese Internet / censorship | 1 | Yang 2009 | King, Pan & Roberts (2013, 2017); Roberts (2018); Chen & Yang (2019); Stockmann (2013) |
| Connective action / networked publics | 1（仅参考文献） | Bennett & Segerberg 2012 | 正文无引用 |
| Public sphere / deliberation | 1 | Ojala & Ripatti-Torniainen 2024 | Habermas; Fraser; Benhabib |
| Retail investor behavior | 0 | — | Barber & Odean (2000, 2008); Kumar & Lee (2006); 中国散户行为文献 |

#### 3.4 综述性评估

**Ojala & Ripatti-Torniainen (2024)引用的深层含义：**

论文引用了Ojala & Ripatti-Torniainen (2024)对networked publics理论的批判（"research on networked and affective publics has too often detached itself from the longer theoretical tradition on what a public is and does—narrowing the concept to whatever circulates online"）。这一引用非常恰当地防御了潜在的理论批评，且恰好为论文自身的理论抱负（将deliberation, agency, mobilization重新置于中心）提供了逆写基础。

然而，该批判本质上要求论文走出"whatever circulates online"的理论舒适区，回到normative public sphere理论——但论文的展开更多停留在描述性分析（public是一种descriptive formation而非normative concept）。这是一个未被充分回应的理论挑战。

**结论性评估：**

| 维度 | 评分 | 注释 |
|:-----|:-----|:------|
| 核心理论框架文献 | ⭐⭐⭐⭐⭐ | Papacharissi + Hirschman的对话极强 |
| 平台/方法论文献 | ⭐⭐⭐⭐⭐ | 平台可供性文献覆盖全面 |
| 对话/跨学科文献 | ⭐⭐⭐ | 行为金融学对话扎实但散户行为文献缺失 |
| Gap陈述力度 | ⭐⭐⭐⭐ | 清晰、有力、可操作；双重gap定位可更明确 |
| 审查/中国政治文献 | ⭐⭐ | 显著薄弱，特别在依赖self-censorship假设时 |
| 集体行动/联结行动文献 | ⭐⭐ | Bennett & Segerberg在参考文献但正文零引用 |

**总体评估：** 文献定位在核心理论对话（affective publics + Hirschman）上极强，平台方法论文献覆盖堪称模范，但在中国政治语境（审查）和散户行为两方面的文献基础需要加强。Gap陈述清晰有力，但对论文自身真正的理论gap（theoretical boundary condition of affective publics）的表述可更显性化。

---

## === 综合评估总结 ===

### 论文体系表

```
          ┌─────────────────────────────────────────────┐
          │      Policy Announcements as Affective Events│
          └─────────────┬───────────────────────────────┘
                        │
                        ▼
          ┌─────────────────────────────────────────────┐
          │      Sina Weibo Affective Public             │
          │   (85,630 comments, 4 stages, 5 months)      │
          └─────────────┬───────────────────────────────┘
                        │
              ┌─────────┴──────────────┐
              ▼                        ▼
    ┌───────────────────┐  ┌────────────────────────┐
    │ RQ1: Does feeling │  │ RQ2: What does public  │
    │ respond to policy?│  │ do instead of respond? │
    └────────┬──────────┘  └───────────┬────────────┘
             │                         │
             ▼                         ▼
    ┌───────────────────┐  ┌────────────────────────┐
    │ ITS + Placebo:    │  │ Typology:              │
    │ NO response       │  │ Anticipation + Venting │
    │ (H₀ not rejected) │  │ >>> Deliberation       │
    └────────┬──────────┘  └───────────┬────────────┘
             │                         │
             └──────────┬──────────────┘
                        ▼
          ┌─────────────────────────────────────────────┐
          │        Skeptical Inertia                    │
          │  (4th mode beyond Exit/Voice/Loyalty)       │
          │  = Hope ↔ Disaffection standoff            │
          └─────────────────────┬───────────────────────┘
                                │
                                ▼
          ┌─────────────────────────────────────────────┐
          │ RQ3: Boundary Condition for Affective Publics│
          │   Connective Intensity ≠ Mobilizational      │
          │   Potential (separable dimensions)           │
          │   ⇒ Feeling can constitute a public          │
          │      without ever mobilizing it              │
          └─────────────────────────────────────────────┘
```

### Ontological 层级

```
Level 1: Policy Event Ontology
  ├── Type: 货币政策/政治局会议/发改委发布会/化债方案
  ├── Duration: 2024.09.01 – 2025.01.28 (5 months)
  ├── Scale: 4旗舰事件 + 持续政策周期
  └── Function: Affective Occasion (情感现场)

Level 2: Platform-Mediated Public Ontology
  ├── Platform: Sina Weibo (affordances: trending/recommendation/moderation)
  ├── Population: Retail investors (85,630 comments)
  ├── Register: Brief (median 13 chars), non-deliberative
  └── Expression: Anticipatory → Affective (forecast + vent = ~70%)

Level 3: Affective Structure Ontology
  ├── Valence: Shallow warming (0.45→0.48→0.46; not policy-driven)
  ├── Intensity: Flat (|s-0.5| ≈ 0.28; CV 0.029 vs volume CV 0.49)
  ├── Dispersion: Stable (SD ≈ 0.31; ~46% strongly polarized throughout)
  └── Autocorrelation: AR(1) = 0.23 (yesterday governs today, not announcements)

Level 4: Theoretical Concept Ontology
  ├── Skeptical Inertia: 4th mode of public response
  │   └── ≠ Exit, ≠ Voice, ≠ Loyalty
  │       └── Held by: hope-disaffection standoff
  ├── Demobilized Affective Public: Boundary condition
  │   └── High connective intensity, low mobilizational potential
  └── Individuated Framing: "my loss" → no "we" → no collective action
```
