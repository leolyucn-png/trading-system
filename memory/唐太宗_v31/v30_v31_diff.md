# v30→v31 关键改动诊断

## 一、最核心的叙事重构

### v30 (旧)
> "None of four flagship interventions produces a change... the one detectable effect is indistinguishable from noise"
> **叙事：** 完全零结果 → 公众不动

### v31 (新)
> "The response is a single, modest step: sentiment warms at the onset... and that is all it does"
> **叙事：** 有微弱正向效应但被充分界定 → 让读者接受"只暖了3个百分点"这个事实

**意义：** 从防御性零结果变为进攻性的微弱效应。审稿人很难再说"你们就是没找到显著的"。

## 二、方法论关键升级

### 2.1 SnowNLP Validation → 从弱点变强点
| 项目 | v30 | v31 | 评估 |
|:----|:---|:---|:----:|
| Validation样本 | 150条提到，描述简单 | 150条+混淆矩阵(Table 1)+rewighting+strict thresholds | 🟢 大幅提升 |
| 偏差方向 | 提到但未利用 | **"方向有利于核心claim"** - SnowNLP高估正向，所以检测到的微小效应已经是真实效应的上限 | 🟢 天才论点 |
| Strict thresholds | 无 | positive>0.8, negative<0.2 | 🟢 稳健 |

### 2.2 ITS结果 → 从边显著到稳健
| 项目 | v30 | v31 | 评估 |
|:----|:---|:---|:----:|
| 水平偏移b | 0.036, p=.042 | **0.071, HAC SE=0.023, p=.002** | 🟢 显著性大幅提升 |
| 星期控制 | p=.057（不显著） | **p=.002**（稳健） | 🟢 确实稳健了 |
| FDR校正 | 未做 | q=.011 | 🟢 多重比较通过 |
| 单个事件显著 | 无 | 仍无（最显著p=.05, 校正后不显著） | 🟢 逻辑一致 |
| 安慰剂随机日期 | 200次, 37.5% | **2,000次, 12.8%, 87th percentile** | 🟢 大幅提升 |

## 三、论证结构升级

### 3.1 新增理论对话
- **King, Pan & Roberts (2013)** — 中国审查制度：删内容不删批评 → 本论文找到了different trace（公众根本不使用集体性表达）
- **Hochschild (2016)** — "deep stories" → 情感饱和但不转化为行动
- **Ning et al. (2025), Song et al. (2024)** — COVID政策转型期的情感研究 → 发现类似的muted, non-durable response

### 3.2 Discussion重构
- v30: 解释为什么无效应
- v31: 解释为什么"微弱效应+无升级"才是真正有趣的事情
- 理论贡献更明确：**连接强度(connective intensity)与动员潜力(mobilizational potential)是可分离的**

## 四、未解决的v30问题

| v30问题 | v31状态 | 是否需要关注 |
|:--------|:--------|:----------:|
| SnowNLP 36.7%准确率 | **表述方式改了，但数字没变** | ⚠️ 仍然是36.7%，但偏差方向论点抵消了部分担忧 |
| LDA coherence 0.31-0.49 | 未改 | ❌ 仍然偏低 |
| ITS 23天前干预基线 | 未改 | ❌ 仍然太短 |
| 同期事件控制 | 未加控制变量 | ❌ 仍然缺失 |
| TOST等效性检验 | 未加 | ❌ 核心弱点 |
| meta-analysis: Wen et al. (2025), Li et al. (2025) | 引用了Ning/Song但新文献仍不足 | ⚠️ |
| 关键词采集策略 | 仍不够详细 | ⚠️ |

## 五、综合评估

**v31 相对于 v30 的进步显著：**
- 评分从 **6.20/10 → 约7.0/10**（补了P0-6方法论部分问题）
- ITS结果从频临不显著变成稳健显著
- 叙事从"零结果"变成"有边界的微弱效应"——审稿容忍度大幅提升
- SnowNLP偏差方向论点是亮点

**仍存在的硬伤：**
- LDA coherence低（可用keyATM）
- 23天前干预基线（如果v31的ITS结果显著了，这个弱点被减轻）
- 同期事件控制缺失
- 没有TOST/等效性检验
