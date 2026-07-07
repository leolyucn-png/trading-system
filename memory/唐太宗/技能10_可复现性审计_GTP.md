# 技能⑩ reproducibility-stamp — 可复现性审计

## GTP论文：Game-Triggered Pilgrimage (GTP)

---

## 1. 数据公开性审计

### 1.1 数据层级

| 层级 | 内容 | 可公开性 | 障碍 |
|:----|:-----|:--------:|:----|
| L0 | 989原始小红书图片 | ❌ 困难 | 版权归属小红书用户，非研究者所有。即使仅公开URL，小红书对爬虫的法律立场不明确 |
| L1 | 616张最终编码图片 | ❌ 困难 | 同上，包含用户肖像和可能的地理位置信息 |
| L2 | 编码数据集（.csv） | ⚠️ 可行但有约束 | 可以公开去标识化的编码矩阵（每行=图片ID的hash，每列=13维度编码值+类型标注+遗址类型） |
| L3 | 编码手册 | ✅ 可公开 | 编码指南、操作定义、示例图片描述 |
| L4 | 分析代码 | ✅ 可公开 | Python/R脚本用于所有统计计算 |

### 1.2 最低公开标准（推荐）

建议在GitHub或OSF上公开：

```
gtp-reproducibility/
├── README.md               # 项目概述 + 数据获取说明
├── data/
│   ├── coding_scheme.md    # 编码手册（含每维度操作定义）
│   ├── coded_data_anonymized.csv  # 去标识化编码矩阵
│   └── sample_images/      # 5-10张去标识示意图（仅无面部特征）
├── analysis/
│   ├── 01_descriptive.R    # 描述统计
│   ├── 02_chisquare.R      # χ²检验
│   ├── 03_figures.R        # 图表重现
│   └── 04_supplementary.R  # 敏感性分析
├── output/
│   └── figures/            # 所有图表
└── paper/
    └── manuscript.pdf
```

**关键约束声明：** "Due to platform terms of service and user privacy, raw images cannot be shared. The anonymized coding matrix and complete coding scheme are provided to enable full analytical reproducibility."

---

## 2. 编码方案可复现性（Grounded Theory Process）

### 2.1 扎根理论过程审计

| 阶段 | 论文中记录 | 评估 | 应包含 |
|:----|:----------|:----|:------|
| 开放编码（Open Coding） | ⚠️ 部分记录 | 未展示初始代码表（preliminary code list） | 至少50-100个初始代码的完整列表 |
| 轴向编码（Axial Coding） | ⚠️ 部分记录 | 未展示类别之间的关联假设 | 编码范式的图示（条件→现象→情境→策略→后果） |
| 选择编码（Selective Coding） | ⚠️ 部分记录 | 核心类别确定为4种类型，但未展示从轴向代码到核心类别的收敛过程 | 选择编码的决策树或矩阵 |

### 2.2 严重不足

**缺少"编码演变日志"**。一篇可复现的扎根理论论文应包含：

```markdown
# 编码演变（示例）
Round 1 (open coding, n=100 images): 87 initial codes
  → 合并相似项（如"举手机":"holding phone"→"smartphone use"）
Round 2 (axial, n=300): 14 categories → 6 thematic clusters
  → 删除2个低密度类别（<3% coverage）
Round 3 (selective, n=616): 4 core types
  → 决策：为什么将"举手机拍照"和"对着手机做手势"合并为Game-Marker而非分开？
```

**没有这个记录，本质上无法从原始数据重新推导出4种类型。**

### 2.3 可复现性等级

```
可复现性等级：█░░░░░░░░░ 2/10

可以用编码手册在新数据上应用编码 → 中等
可以从原始图片重新推导出同类编码 → 困难
可以从原始图片重新推导出相同4种类型 → 几乎不可能
```

---

## 3. Inter-Coder Reliability 审计

### 3.1 报告现状

| 指标 | 报告值 | 评估 |
|:----|:------|:----|
| 总Kappa | 0.82 | ✅ 优秀（Landis & Koch: almost perfect） |
| Per-dimension Kappa | 未报告 | ❌ 严重缺失 |
| 编码者数量 | 未明确 | ❌ 无法判断 |
| 重叠编码样本比例 | 未报告 | ❌ 无法判断是否充分 |
| 编码前训练过程 | 未报告 | ❌ 无法判断 |

### 3.2 Per-dimension Kappa 缺失的影响

假设有13个编码维度，总Kappa 0.82 可能掩盖以下情况：

| 情景 | 可能 | 影响 |
|:----|:----|:-----|
| 10个维度Kappa>0.9，3个维度<0.4 | ✅ 很可能 | 总体0.82但"姿势类型""手势方向"维度一致性差 |
| 高Kappa维度占大多数样本 | ✅ 可能 | "是否出现建筑"容易编码（Kappa=0.95），"情感表达"困难（Kappa=0.31） |
| 仅对样本子集计算Kappa | ⚠️ 可能 | 如果只对编码者分歧大的子集计算，Kappa会被低估 |

**Per-dimension缺失的可复现性影响：** 严重。读者无法判断哪些维度是关键发现（4种类型分类）的支撑，哪些维度是辅助性的。如果关键维度的Kappa低至0.4-0.6，整个类型学结论的可靠性受到质疑。

### 3.3 最低可复现标准

**对于视觉内容分析的inter-coder reliability，应报告：**

```
1. 每个编码维度的 Cohen's κ / Krippendorff's α
2. 百分比一致性（% agreement）以补充κ（|κ base-rate problem）
3. 重叠编码的样本量（ideally > 20% of total sample）
4. 编码者数（2人或更多人）
5. 是否进行了"编码者校准会议"及效果
6. Kappa的95%置信区间
```

### 3.4 当前GTP论文的差距

| 应报告 | 实际报告 | 差距严重性 |
|:------|:--------|:---------:|
| Per-dimension κ for 13 dimensions | 仅总κ=0.82 | 🔴 严重 |
| % agreement | 未报告 | 🔴 严重 |
| 重叠样本比例 (>20%) | 未报告 | 🟡 中等 |
| 编码者训练过程 | 未报告 | 🟡 中等 |
| κ的95% CI | 未报告 | 🟡 中等 |
| Disagreement resolution过程 | 可能部分 | 🟢 可接受 |

---

## 4. 最低可复现标准建议

### 4.1 黄金标准（目标论文发表）

```
□ 编码手册完整公开（含每维度操作定义+正反例）
□ 去标识化编码数据集公开（.csv/.xlsx）
□ 全部分析代码公开（R/Python）
□ 每个编码维度报告Krippendorff's α（≥0.667阈值）
□ 编码者培训→校准会议→再测试的完整流程记录
□ 在Supplementary Materials中展示编码演变日志
□ 提供敏感性分析：若去除最低κ维度，结论是否稳健？
□ 提供一个"决策日志"文档，记录所有分类和排除决策
```

### 4.2 最低可接受标准（GTP论文现状修复）

```
□ 至少补充每个编码维度的Cohen's κ
□ 公开匿名化的编码矩阵（13维+4类型+遗址类型）
□ 公开编码手册（含操作定义）
□ 提供编码过程中的代表性分歧案例
□ 公开所有描述统计和推断统计的分析脚本
□ 明确陈述哪些数据因版权/隐私无法公开
```

### 4.3 GitHub仓库应包含

```yaml
README.md:
  - 论文标题 + DOI/link
  - 数据可用性声明（哪些公开、哪些不公开及原因）
  - 环境要求（R/Python版本 + packages.txt/requirements.txt）
  - 快速重现命令

analysis/:
  - descriptive_stats.py — 生成Table数据
  - inter_coder_reliability.py — 各维度κ计算
  - chisquare_tests.py — 所有χ²检验
  - figures.py — 生成所有图表

data/:
  - coding_scheme.md
  - coded_data_anonymized.csv

docs/:
  - coding_protocol.pdf — 完整的编码协议
  - decision_log.md — 所有编码决策的日志
  - coder_training.md — 编码者培训流程
```

---

## 5. GPT论文 vs DES论文：可复现性对比

### 5.1 DES论文（多地点数字民族志）

DES（Digital Ethnography）:
- 多地点田野调查，访谈+参与观察
- 核心数据来自研究者-被研究者互动

| 可复现性维度 | DES | GTP |
|:-----------|:---|:----|
| 数据可获取 | ❌ 访谈录音/笔记含个人身份，几乎无法匿名公开 | ⚠️ 图片无法公开，但编码矩阵可完全匿名化 |
| 分析过程透明 | ❌ 民族志分析依赖研究者主体间性，不可能完全编码化 | ✅ 扎根理论提供结构化编码路径 |
| Inter-subjective agreement | ❌ 不可能（每人有不同田野经验） | ✅ 可通过ICR量化 |
| 假设检验 | ❌ 民族志不预设假设 | ⚠️ 其类型学本质是探索性但被呈现为分类 |
| 代码/脚本透明度 | ❌ 不适用 | ✅ 分析脚本可完全公开 |

### 5.2 对比结论

| 结论 | 说明 |
|:----|:-----|
| **GTP天然可复现性优于DES** | 视觉内容分析比民族志更适合标准化操作 |
| **GTP当前实现与潜力差距大** | 有结构化的编码数据+分析脚本→说可复现，但缺失per-dimension κ是关键硬伤 |
| **DES优势在于"人种志真实性"** | 如果你认可"研究者作为工具"的认识论，DES有不可替代的理解深度 |
| **GTP应追求"analytic reproducibility"** | 即使无法重新收集图片，至少可以让任何人用相同编码方案+编码矩阵→得到相同4种类型 |

### 5.3 可复现性评分

```
GTP论文当前可复现性评分: 4.5/10
  - 数据结构化: +3（编码框架存在）
  - 编码方案透明: +1（有过程描述但缺失关键细节）
  - ICR报告完整: -2（总κ可以，per-dim缺失）
  - 分析代码: 0（未知，假设未公开）
  - 数据公开: +1（编码矩阵可匿名化）
  - 附录/Supplement: +0.5（信息量不明）

修复后可达到: 7.5-8.0/10
  补充per-dim κ → +1.5
  公开编码矩阵 → +1.0
  公开分析代码 → +1.0
  更新编码手册 → +0.5
```
