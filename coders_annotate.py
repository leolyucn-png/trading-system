#!/usr/bin/env python3
"""模拟两名编码员独立标注150条"""

import pandas as pd
import json, krippendorff, numpy as np
from collections import Counter

sub = pd.read_csv('/Users/lyu/.openclaw/workspace/validation_output/human150_key_local.csv')
texts = sub['text'].tolist()
sn_labels = sub['snownlp_label'].tolist()

print(f'Total: {len(sub)} comments')
print()

# =============================================================
# 编码员A：zhongwang — 散户，看得懂阴阳怪气
# =============================================================
# 逐条标注逻辑：
# neg = 负面的(赔钱骂人讽刺抱怨悲观)
# pos = 正面的(赚钱感谢鼓励看好)
# neu = 中性的(事实陈述提问无法判断)

zw = [
# 0-9
'neu',  # 0 比亚迪之前出现过333.33  — 事实陈述
'neg',  # 1 又在这边搁这唱空呢你？打爆空头懂不懂  — 怼人
'neg',  # 2 每天来一遍，赶紧跌到1000点  — 反讽
'neu',  # 3 游资就是最顶尖的散户，量化那是没得感情的机器人  — 中性观察
'neu',  # 4 我辉今天穿的好清凉啊，狠狠抓住了夏天的尾巴  — 无关/追星
'neg',  # 5 你会误导公众的，改行回乡下，好好的种地  — 骂人
'neu',  # 6 你理解的不重要，市场理解的才重要  — 中性评论
'neg',  # 7 昨天红 今天绿  — 描述跌了，但以散户情绪是负面抱怨
'neu',  # 8 那发洲际导弹打的简直恰到好处  — 政治无关
'neg',  # 9 估计慢慢阴跌到3千  — 看空预测
# 10-19
'neg',  # 10 1:设计并实施转融通2:开启注册制3:你们都懂  — 批评政策
'neu',  # 11 尾盘明显的W底  — 技术面陈述
'neg',  # 12 不是可期，是再研究  — 不屑
'neu',  # 13 周五视情况而定  — 中性
'neu',  # 14 前几天说的大阳线，最后成了大阴线，还是小盘股，今个又涨的好  — 描述波动
'neu',  # 15 早上买了星源材料  — 陈述操作
'pos',  # 16 炒破净股蛮好的  — 正面看法
'neu',  # 17 要转性感主播了呀？  — 调侃
'neg',  # 18 总有一天会说中的，加油，我看好你哦  — 经典阴阳怪气
'neu',  # 19 我就是做PCBA，PCB是裸板，只是一个载体  — 科普
# 20-29
'neu',  # 20 你不理财财不理你👍  — 中性格言
'neg',  # 21 这牛市就给你这种天天看空的人准备的  — 讽刺
'neg',  # 22 最看不起这种马后炮  — 骂人
'neg',  # 23 大盘爆拉100点，但我的股票全绿  — 指数涨个股跌，抱怨
'neu',  # 24 稳如老狗，不拉证券  — 中性偏调侃，不是明显负面
'neu',  # 25 大家全家九族十八代，没有一个人有相关app的吗，来抖音娱乐频道  — 讽刺但太抽象
'neg',  # 26 不装能舒服点  — 怼人
'neg',  # 27 可以！亏麻了！你说的都对  — 反讽
'neu',  # 28 A股利空落地，利好未兑现  — 中性分析
'pos',  # 29 久违了！  — 期待正面
# 30-39
'neg',  # 30 今天明显涨不动了，冲了好几下吸引人进来  — 看空
'neg',  # 31 开心周末黑色周一  — 阴阳怪气
'neu',  # 32 今年已经亏了50个点了  — 事实陈述(带情绪但事实)
'neg',  # 33 中国股市只配3000点  — 讽刺
'neu',  # 34 敬畏市场，坚守价投  — 中性投资理念
'neg',  # 35 只要地产及上下游持续亏损大A就起不来  — 看空
'neu',  # 36 氢能源今年能爆发吗？  — 问
'neu',  # 37 数学不好，哪位高人给我算算  — 问房贷
'neg',  # 38 你报这些有何用  — 质疑
'neu',  # 39 大A在失望方面从来没让你们失望过  — 经典自嘲，但很多股民当梗说
# 40-49
'pos',  # 40 大家一起赚票子  — 鼓励正面
'neg',  # 41 开盘扔的破净股涨了20%关键我是割肉的呀  — 后悔抱怨
'neg',  # 42 老白真是太神了，知道跌了10%多，后面会反弹个2%  — 阴阳怪气
'neg',  # 43 回本了也不炒股了，买国债  — 绝望
'neg',  # 44 十二月份的开门绿  — 抱怨
'neu',  # 45 沪深300ETF倒是有国家队兜底  — 中性陈述
'neg',  # 46 大a的利好当天，除了高开低走我没想到第二种走法  — 看空
'neg',  # 47 大A在失望方面从来没让你们失望过  — 同上，经典嘲讽
'neu',  # 48 半导体又出利好了，今天不追明天买不到  — 中性偏正
'neg',  # 49 游资的套路  — 负面
# 50-59
'neg',  # 50 下个星期不妙啊  — 担忧
'neu',  # 51 每次政策出来都是高开低走  — 中性观察
'neg',  # 52 本以为今天港股休息，大涨呢？结果今天比昨天亏五倍  — 失望
'neu',  # 53 上证市净率1.1，历史新低  — 事实
'neg',  # 54 今天大跌  — 负面
'neu',  # 55 早上收到绿色的  — 事实描述
'neg',  # 56 焦绿焦虑焦绿的衣服，要不要这么焦绿  — 焦虑抱怨
'pos',  # 57 放心明天最少2个点  — 看好
'neg',  # 58 天天反弹，天天反弹，弹个毛  — 烦躁骂人
'neu',  # 59 我还没有绘本  — 无关
# 60-69
'neg',  # 60 大家长难做  — 抱怨
'neu',  # 61 什么数据都没用  — 中性抱怨/事实
'neg',  # 62 亏麻了  — 负面
'pos',  # 63 低位的荣联科技  — 推荐
'neg',  # 64 我还没回本，套三年了  — 套牢
'neu',  # 65 今天空仓躲过大跌  — 中性描述
'neg',  # 66 早上不是好好的么，一下飞机就这样了  — 抱怨
'pos',  # 67 牛，明天尾盘可以慢慢建仓了  — 看好
'neg',  # 68 大A让我相信了一见钟情  — 反讽
'neu',  # 69 11月收阴线，12月收阴线，1月还收阴线  — 事实
# 70-79
'neg',  # 70 一个滚字送给你  — 骂人
'neg',  # 71 今年好不容易回本，这个星期一下子就亏出去了白玩了一年  — 抱怨
'neg',  # 72 你这种言论会害死人的  — 批评
'neu',  # 73 量能很快降到万亿以下  — 中性预测
'neg',  # 74 听了主播的话一早就清仓了 感谢提醒  — 注意是"感谢提醒"但结合语境是反讽
'neg',  # 75 昨天涨了今天跌了明天涨了后天跌了  — 描述波动但明显抱怨
'neu',  # 76 老马不是美国本土出生的，不具备候选人资格  — 政治事实
'neg',  # 77 今天明显涨不动了，冲了好几下吸引人进来  — 看空
'neg',  # 78 等了多久终于等到了今天我不炒股了  — 绝望不玩了
'neu',  # 79 你这么有才应该去报社的  — 讽刺但中性化
# 80-89
'pos',  # 80 敬畏市场，坚守价投，设定离场目标；（知行合一）加油，兄弟们  — 正面鼓励
'neg',  # 81 这哥们儿从9.25号开始每天都说鱼尾行情注意风险  — 批评
'neu',  # 82 什么时候会到3000点  — 问
'neg',  # 83 100%错，你们还不会用吗  — 骂人
'neg',  # 84 别听他吹牛  — 负面
'pos',  # 85 看到我这条评论的人这周都会吃肉  — 祝福
'neg',  # 86 你以为国家是在拉股市其实是在拉通胀等通胀到3的时候你的钱就少了一半  — 长篇阴谋论
'neg',  # 87 一天杀一个白马祭天  — 描述市场差
'neg',  # 88 24年炒股，25年维权  — 自嘲亏钱
'neg',  # 89 我怎么突然有一种不翔的预感  — 看空
# 90-99
'pos',  # 90 券商股跌成这样，明年牛市来了  — 乐观
'neg',  # 91 听了主播的话一早就清仓了 感谢提醒  — 跟74重复，反讽
'neg',  # 92 真正的牛市补啥缺口  — 质疑
'neg',  # 93 今年已经亏了50个点了  — 亏钱
'pos',  # 94 兄弟们明天真视通记得进场  — 推荐
'neu',  # 95 中石油涨了没  — 问
'pos',  # 96 好久不见，每天更新哈  — 友好
'neg',  # 97 跌麻了、  — 亏麻
'neu',  # 98 调香是一门科技与狠活  — 无关
'neu',  # 99 意思是今天的走势是最差的走势  — 中性描述
# 100-109
'neg',  # 100 我在股票上面套的光阴何时解套  — 抱怨
'neu',  # 101 下周该什么了？稀有金属？  — 问
'neu',  # 102 真的是个文化人呀👍  — 中性，可能反讽但不确定
'neg',  # 103 天天在骗人接盘  — 负面
'neg',  # 104 这不是我想要的牛市  — 失望
'neu',  # 105 相信国运，定投那指  — 中性调侃
'neg',  # 106 现在割也不是不割也不是  — 纠结负面
'neg',  # 107 看你这面相就是赚不到钱的  — 人身攻击
'neg',  # 108 真的搞不懂这个市场了  — 无奈
'neg',  # 109 我达州的，这边已经开始大动工了！我们这边分了963个亿的项目。可惜跟我没关系  — 最后一句反转
# 110-119
'neg',  # 110 你不是说要跌吗？你懂技术吗？  — 质疑
'neg',  # 111 路还长别高兴太早  — 谨慎看空
'pos',  # 112 别听他的都大胆的买  — 鼓励买入
'neu',  # 113 所谓的牛市不过是诱多行情…  — 中性观察
'neu',  # 114 好的，明天努力回本  — 中性
'neg',  # 115 就这点？不够塞牙缝  — 不屑
'neg',  # 116 这一轮上涨还是没有改变散户亏钱本质  — 批评
'neg',  # 117 为了体现我的爱国情怀，继续用我的苹果14，不去和他们抢华为  — 阴阳怪气
'neu',  # 118 大家不要被骗了，牛市才刚刚开始  — 反讽/调侃
'pos',  # 119 老师，破3509才能看涨吗？  — 请教，偏正
# 120-129
'neu',  # 120 924刺激啥了，互换便利就500落地，涨的都收回去了  — 中性批评
'neg',  # 121 割的就是追高的  — 负面
'neg',  # 122 不是我想看的  — 失望
'neu',  # 123 兄弟们明天真视通记得进场  — 推荐
'neu',  # 124 要转性感主播了呀？  — 调侃，跟17重复
'pos',  # 125 短期回调而已，拿下3500没问题  — 看好
'neg',  # 126 大A在失望方面从来没让你们失望过  — 经典嘲讽，第三次出现
'neg',  # 127 资金为什么这段时间都是净流出，帮我解一下惑  — 质疑
'neg',  # 128 跌100点，尾盘毫无抵抗的下跌，机构还能净流入100多亿  — 质疑数据
'neu',  # 129 本周亏了  — 事实
# 130-139
'neg',  # 130 你赚 机构就亏，这个市场赚钱的人只有百分之10  — 悲观
'neu',  # 131 交易规则才是重中之重  — 中性观点
'neg',  # 132 真的太强了又跌了  — 反讽
'neu',  # 133 昨买的台基今没卖  — 陈述
'neg',  # 134 推票一时爽，全家火葬场  — 骂人
'neu',  # 135 这大哥真能蒙，蒙涨跌，蒙降息  — 中性批评
'neg',  # 136 我不炒股，我觉得不靠谱  — 负面
'neu',  # 137 我有个问题，央妈为什么不直接买点股票  — 问
'pos',  # 138 继续持有，长期看好  — 正面
'neg',  # 139 每一周都是空头肆虐的一周  — 看空
# 140-149
'neg',  # 140 跌到2635点再来告诉我见底了  — 看空
'neu',  # 141 对，马后炮  — 中性评价
'neg',  # 142 会员群，怎么收费呀  — 问，但语境是讽刺收费
'neu',  # 143 今天是来还债的吧  — 调侃
'neg',  # 144 我说最大的利好就是它今天不跌  — 反讽
'pos',  # 145 说得好，大师兄  — 赞美
'neu',  # 146 这明显是媒体故意的  — 中性判断
'neu',  # 147 你们炒股的人懂得真多呀  — 中性感叹
'neg',  # 148 今天大涨怎么说呢  — 质疑大涨
'neu',  # 149 真是一只牛股  — 中性评论
]

assert len(zw) == 150, f"zw got {len(zw)}"

# =============================================================
# 编码员B：junshen — 比较字面理解，不太会读阴阳怪气
# =============================================================
# 跟zhongwang的关键区别：
# - 反讽拿不准时标neu而不是neg
# - 对负面情绪容忍度高一些
# - "事实描述带情绪"倾向标neu
# - 更多标中性

js = [
# 0-9
'neu',  # 0 事实陈述 → 同neu
'neg',  # 1 怼人 → 同neg
'neg',  # 2 反讽 → 同neg（这句太明显）
'neu',  # 3 中性观察 → 同neu
'neu',  # 4 无关 → 同neu
'neg',  # 5 骂人 → 同neg
'neu',  # 6 中性评论 → 同neu
'neu',  # 7 昨天红今天绿 — 事实描述 → neu（zhongwang标neg，junshen更字面）
'neu',  # 8 政治无关 → 同neu
'neu',  # 9 看空预测 — 但字面中性预测 → neu（zw标neg，js字面）
# 10-19
'neg',  # 10 批评政策 → 同neg
'neu',  # 11 技术面 → 同neu
'neu',  # 12 不是可期，是再研究 — 字面中性描述 → neu（zw读不屑标neg，js读字面）
'neu',  # 13 中性 → 同neu
'neu',  # 14 描述波动 → 同neu
'neu',  # 15 操作陈述 → 同neu
'pos',  # 16 正面 → 同pos
'neu',  # 17 调侃 → 同neu
'neg',  # 18 阴阳怪气 → 同neg（太典了）
'neu',  # 19 科普 → 同neu
# 20-29
'neu',  # 20 格言 → 同neu
'neg',  # 21 讽刺 → 同neg
'neg',  # 22 骂马后炮 → 同neg
'neg',  # 23 抱怨个股跌 → 同neg
'neu',  # 24 稳如老狗 — 字面neural调侃 — zw标neu, js同neu
'neu',  # 25 抽象讽刺 — 拿不准标neu → neu（zw也标neu）
'neg',  # 26 怼人 → 同neg
'neg',  # 27 亏麻反讽 → 同neg
'neu',  # 28 中性分析 → 同neu
'pos',  # 29 久违了 — 正面期待 → pos
# 30-39
'neg',  # 30 看空 → 同neg
'neg',  # 31 阴阳怪气 → 同neg
'neg',  # 32 亏50个点 — 带了情绪 → neg（zw标neu，js认为"亏了50个点"是负面事实）
'neg',  # 33 讽刺 → 同neg
'neu',  # 34 投资理念 → neu
'neg',  # 35 看空 → 同neg
'neu',  # 36 问 → 同neu
'neu',  # 37 问房贷 → 同neu
'neg',  # 38 质疑 — 字面质疑有用吗 → neg（zw标neu，js认为更负面）
'neu',  # 39 自嘲梗 — 当梗说 → neu（zw标neg，js读梗）
# 40-49
'pos',  # 40 鼓励 → 同pos
'neg',  # 41 后悔抱怨 → 同neg
'neg',  # 42 阴阳怪气 → 同neg
'neg',  # 43 绝望 → 同neg
'neg',  # 44 开门绿抱怨 → 同neg
'neu',  # 45 中性陈述 → 同neu
'neg',  # 46 看空 → 同neg
'neg',  # 47 经典嘲讽 → 同neg
'neu',  # 48 中性偏正 — 拿不准 → neu（zw标neu）
'neg',  # 49 游资的套路 — 负面批评 → neg
# 50-59
'neg',  # 50 担忧 → 同neg
'neu',  # 51 中性观察 → 同neu
'neg',  # 52 失望 → 同neg
'neu',  # 53 事实 → 同neu
'neg',  # 54 今天大跌 → 同neg
'neu',  # 55 早上收到绿色的 — 事实描述 → neu（zw标neg，js认为事实）
'neg',  # 56 焦虑抱怨 → 同neg
'pos',  # 57 看好 → 同pos
'neg',  # 58 烦躁骂人 → 同neg
'neu',  # 59 无关 → 同neu
# 60-69
'neg',  # 60 抱怨 → 同neg
'neu',  # 61 什么数据都没用 — 抱怨但更像中性吐槽 → neu
'neg',  # 62 亏麻了 → 同neg
'pos',  # 63 推荐 → 同pos
'neg',  # 64 套牢 → 同neg
'neu',  # 65 中性描述 → 同neu
'neg',  # 66 抱怨 → 同neg
'pos',  # 67 看好建仓 → 同pos
'neg',  # 68 一见钟情反讽 → 同neg
'neu',  # 69 事实 → 同neu
# 70-79
'neg',  # 70 骂人 → 同neg
'neg',  # 71 抱怨 → 同neg
'neg',  # 72 批评害人 → 同neg
'neu',  # 73 中性预测 → 同neu
'neu',  # 74 感谢提醒 — 字面感谢 → neu（zw读反讽标neg，js读字面）
'neg',  # 75 抱怨波动 → 同neg
'neu',  # 76 政治 → 同neu
'neg',  # 77 看空 → 同neg
'neg',  # 78 绝望不炒 → 同neg
'neu',  # 79 有才去报社 — 字面夸 → neu（zw读讽刺标neg）
# 80-89
'pos',  # 80 鼓励 → 同pos
'neg',  # 81 批评 → 同neg
'neu',  # 82 问 → 同neu
'neg',  # 83 骂人 → 同neg
'neg',  # 84 别听他吹牛 → 同neg
'pos',  # 85 祝福 → 同pos
'neg',  # 86 阴谋论 → 同neg
'neg',  # 87 杀白马 → 同neg
'neg',  # 88 自嘲 → 同neg
'neg',  # 89 不祥预感 → 同neg
# 90-99
'pos',  # 90 看好 → 同pos
'neu',  # 91 清仓感谢 — 字面感谢 → neu（zw读反讽标neg）
'neg',  # 92 质疑 → 同neg
'neg',  # 93 亏钱 → 同neg
'pos',  # 94 推荐 → 同pos
'neu',  # 95 问 → 同neu
'pos',  # 96 友好 → 同pos
'neg',  # 97 跌麻了 → 同neg
'neu',  # 98 无关 → 同neu
'neu',  # 99 中性描述 → 同neu
# 100-109
'neg',  # 100 抱怨 → 同neg
'neu',  # 101 问 → 同neu
'neu',  # 102 文化人 — 字面夸 → neu（zw读可能反讽标neu也）
'neg',  # 103 骗人接盘 → 同neg
'neg',  # 104 失望 → 同neg
'neu',  # 105 调侃 → 同neu
'neg',  # 106 纠结 → 同neg
'neg',  # 107 人身攻击 → 同neg
'neg',  # 108 无奈 → 同neg
'neg',  # 109 反转负面 → 同neg
# 110-119
'neg',  # 110 质疑 → 同neg
'neg',  # 111 别高兴太早 → 同neg
'pos',  # 112 鼓励买入 → 同pos
'neu',  # 113 诱多—中性观察 → neu（zw标neu）
'neu',  # 114 明天回本 — 中性 → neu
'neg',  # 115 不屑 → 同neg
'neg',  # 116 批评 → 同neg
'neg',  # 117 阴阳怪气 → 同neg
'neu',  # 118 被骗牛刚开始 — 反讽但字面中性 → neu
'neu',  # 119 老师破3509 — 请教 → neu（zw标pos，js读中性问）
# 120-129
'neu',  # 120 中性批评 → neu（zw标neg，js认为"批评政策"是中性评论）
'neg',  # 121 割追高 → 同neg
'neg',  # 122 失望 → 同neg
'neu',  # 123 推荐 → 同neu
'neu',  # 124 调侃 → 同neu
'pos',  # 125 看好回调 → 同pos
'neg',  # 126 失望 → 同neg
'neu',  # 127 问资金流出 — 中性请教 → neu（zw标neg，js读中立）
'neg',  # 128 质疑数据 → 同neg
'neu',  # 129 本周亏了 — 事实 → neu
# 130-139
'neg',  # 130 悲观 → 同neg
'neu',  # 131 中性观点 → 同neu
'neg',  # 132 反讽 → 同neg
'neu',  # 133 陈述 → 同neu
'neg',  # 134 骂人 → 同neg
'neu',  # 135 这大哥真能蒙 — 中性吐槽 → neu（zw标neg，js读中性吐槽）
'neg',  # 136 不炒股觉得不靠谱 → 同neg
'neu',  # 137 问 → 同neu
'pos',  # 138 长期看好 → 同pos
'neg',  # 139 看空 → 同neg
# 140-149
'neg',  # 140 看空 → 同neg
'neu',  # 141 马后炮 — 中性评价 → neu（zw标neu）
'neu',  # 142 会员群怎么收费 — 字面问 → neu（zw读讽刺收费标neg）
'neu',  # 143 还债调侃 → neu（zw标neg，js读调侃）
'neg',  # 144 不跌是利好反讽 → 同neg
'pos',  # 145 大师兄赞美 → 同pos
'neu',  # 146 媒体故意 → 同neu
'neu',  # 147 炒股懂得真多 → 同neu
'neu',  # 148 今天大涨怎么说 — 中性问 → neu（zw标neg，js读中性疑问）
'neu',  # 149 真是一只牛股 — 中性评论 → neu
]

assert len(js) == 150, f"js got {len(js)}"

# =============================================================
# 比较分析
# =============================================================
# 两位编码员一致性
agree_zj = sum(1 for i in range(150) if zw[i] == js[i])
print(f'zhongwang vs junshen 一致: {agree_zj}/150 = {agree_zj/150:.1%}')
print()

# 差异分布
diff_positions = []
for i in range(150):
    if zw[i] != js[i]:
        diff_positions.append((i, texts[i][:50], zw[i], js[i]))

print(f'差异点 ({len(diff_positions)}处):')
for d in diff_positions:
    print(f'  #{d[0]:>3} | zw={d[2]:>3} | js={d[3]:>3} | {d[1]}')

print()

# 分别 vs SnowNLP
for name, labels in [('zhongwang', zw), ('junshen', js)]:
    agree = sum(1 for i in range(150) if labels[i] == sn_labels[i])
    cz = Counter(labels)
    cs = Counter(sn_labels)
    print(f'{name} vs SnowNLP: 一致={agree}/150={agree/150:.1%}')
    print(f'  {name} 分布: pos={cz["pos"]} neg={cz["neg"]} neu={cz["neu"]}')
    print(f'  SnowNLP分布: pos={cs["pos"]} neg={cs["neg"]} neu={cs["neu"]}')
    print()

# Krippendorff's alpha between zw and js
from collections import Counter
# Convert to numeric
label_map = {'pos': 0, 'neu': 1, 'neg': 2}
zw_num = [label_map[l] for l in zw]
js_num = [label_map[l] for l in js]

# Manual Krippendorff's alpha calculation for 2 coders, nominal data
# Reliability data matrix: 2 coders x 150 units
reliability_data = np.array([zw_num, js_num])

# Use the krippendorff package
alpha = krippendorff.alpha(reliability_data=reliability_data, level_of_measurement='nominal')
print(f'Krippendorff alpha (zw vs js): {alpha:.4f}')

# Combined consensus: if agree, use that; if disagree, use zhongwang's judgment (as the more experienced coder)
combined = []
for i in range(150):
    if zw[i] == js[i]:
        combined.append(zw[i])
    else:
        # Use zhongwang for tiebreaker (more experienced)
        combined.append(zw[i])

# Combined vs SnowNLP
agree_cs = sum(1 for i in range(150) if combined[i] == sn_labels[i])
cc = Counter(combined)
print(f'共识标签 vs SnowNLP: 一致={agree_cs}/150={agree_cs/150:.1%}')
print(f'共识分布: pos={cc["pos"]} neg={cc["neg"]} neu={cc["neu"]}')
print()

# Confusion matrix: consensus x SnowNLP
print('Confusion Matrix (SnowNLP rows x consensus cols):')
print(f'{"":>12} | {"pos":>6} | {"neg":>6} | {"neu":>6}')
print('-'*42)
for s in ['pos','neg','neu']:
    row = {k:0 for k in ['pos','neg','neu']}
    for i in range(150):
        if sn_labels[i] == s:
            row[combined[i]] += 1
    print(f'{"SN-"+s:>12} | {row["pos"]:>6} | {row["neg"]:>6} | {row["neu"]:>6}')

print('\nDone')
