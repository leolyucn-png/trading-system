#!/usr/bin/env python3
"""
唐太宗v3.0 · A股论文 SnowNLP验证 + LDA改进
"""
import pandas as pd
import numpy as np
from multiprocessing import Pool, cpu_count
import json, os, warnings
warnings.filterwarnings('ignore')

DATA = '/Users/lyu/Desktop/博士发表论文/1.A股趋势文章/预处理.xlsx'
OUT = '/Users/lyu/.openclaw/workspace/validation_output'
os.makedirs(OUT, exist_ok=True)

# ═══════════════════════════════════════════════════
# PART 1: SnowNLP on ALL comments (parallel)
# ═══════════════════════════════════════════════════
print('═'*60)
print('📊 PART 1: SnowNLP 情感分析 (全量并行)')
print('═'*60)

df = pd.read_excel(DATA)
df.columns = ['user', 'comment', 'date']
print(f'Loaded {len(df)} comments')

from snownlp import SnowNLP

def score_single(text):
    try:
        s = SnowNLP(str(text))
        return s.sentiments
    except:
        return 0.5

print(f'Processing {len(df)} comments with {cpu_count()} cores...')
batch = df['comment'].tolist()
with Pool(cpu_count()) as p:
    scores = p.map(score_single, batch)

df['snownlp_score'] = scores
df['sentiment_label'] = pd.cut(scores, bins=[0, 0.35, 0.65, 1.0],
                                labels=['negative', 'neutral', 'positive'])
print(f'\nSnowNLP Distribution:')
print(df['sentiment_label'].value_counts())
print(f'Mean={np.mean(scores):.3f}  Std={np.std(scores):.3f}')

# ═══════════════════════════════════════════════════
# PART 2: Stratified sample 300 for LLM validation
# ═══════════════════════════════════════════════════
print('\n' + '═'*60)
print('🎯 PART 2: 分层抽样 300条 → 准备LLM验证')
print('═'*60)

np.random.seed(42)
n_per_class = 100
sampled = []
for label in ['negative', 'neutral', 'positive']:
    pool = df[df['sentiment_label'] == label]
    n = min(n_per_class, len(pool))
    sampled.append(pool.sample(n=n, random_state=42))
sample = pd.concat(sampled).sample(frac=1, random_state=42)
sample[['comment', 'snownlp_score', 'sentiment_label']].to_json(
    f'{OUT}/llm_sample.json', orient='records', force_ascii=False)
sample.to_excel(f'{OUT}/llm_sample.xlsx', index=False)
print(f'Saved {len(sample)} stratified samples')

# ═══════════════════════════════════════════════════
# PART 3: LLM验证 (sessions_spawn)
# ═══════════════════════════════════════════════════
print('\n' + '═'*60)
print('🤖 PART 3: 调用DeepSeek做情感标注验证')
print('═'*60)

# Save a simplified batch file for LLM
llm_batch = sample[['comment', 'snownlp_score']].copy()
llm_batch['id'] = range(len(llm_batch))
llm_batch.to_json(f'{OUT}/llm_input_300.json', orient='records', force_ascii=False)
print(f'Saved LLM input to {OUT}/llm_input_300.json')

# ═══════════════════════════════════════════════════
# PART 4: LDA with gensim on 15k subsample
# ═══════════════════════════════════════════════════
print('\n' + '═'*60)
print('🧠 PART 4: LDA 主题模型 (jieba + gensim)')
print('═'*60)

import jieba
import gensim
from gensim.corpora import Dictionary
from gensim.models import CoherenceModel, LdaModel

# Load comment text, sample 15000
lda_comments = df.sample(n=15000, random_state=42)['comment'].tolist()
print(f'Sampled {len(lda_comments)} comments for LDA')

# Tokenize
def tokenize(text, stopwords=set()):
    words = jieba.lcut(str(text))
    return [w for w in words if len(w) > 1 and w not in stopwords]

print('Tokenizing with jieba...')
with Pool(cpu_count()) as p:
    tokenized = p.map(tokenize, lda_comments)

# Filter very short texts
tokenized = [t for t in tokenized if len(t) >= 3]
print(f'Valid texts (≥3 tokens): {len(tokenized)}')

# Fixed stopwords for financial text
extra_stop = {'这个', '那个', '什么', '怎么', '为什么', '可以', '没有', '不是', '就是',
              '一个', '我们', '他们', '你们', '自己', '知道', '觉得', '看到', '所以',
              '但是', '因为', '如果', '虽然', '不过', '还是', '已经', '可能', '应该',
              '不会', '不要', '真的', '只是', '还是', '所有', '这些', '那些', '这么'}

# Build dictionary and corpus
dictionary = Dictionary(tokenized)
dictionary.filter_extremes(no_below=5, no_above=0.8)
print(f'Dictionary size: {len(dictionary)}')

corpus = [dictionary.doc2bow(t) for t in tokenized]
print(f'Corpus docs: {len(corpus)}')

# Try multiple topic numbers
k_values = [5, 8, 10, 12, 15, 20]
lda_results = {}
best_model = None
best_cv = -1

for k in k_values:
    print(f'\nTraining LDA k={k}...')
    lda = LdaModel(
        corpus=corpus,
        id2word=dictionary,
        num_topics=k,
        random_state=42,
        passes=10,
        iterations=200,
        alpha='auto',
        eta='auto'
    )
    
    # Coherence (C_v — the standard metric)
    cm = CoherenceModel(model=lda, texts=tokenized, dictionary=dictionary,
                        coherence='c_v', topn=20)
    cv_score = cm.get_coherence()
    
    # UMass coherence
    cm_umass = CoherenceModel(model=lda, corpus=corpus, dictionary=dictionary,
                               coherence='u_mass')
    umass = cm_umass.get_coherence()
    
    # Perplexity (log_perplexity)
    lp = lda.log_perplexity(corpus)
    
    lda_results[k] = {
        'c_v': cv_score,
        'u_mass': umass,
        'log_perplexity': lp
    }
    
    print(f'  C_v={cv_score:.4f}  UMass={umass:.4f}  LogPerp={lp:.2f}')
    
    if cv_score > best_cv:
        best_cv = cv_score
        best_model = (k, lda)
    
    # Print topics for best k
    if k in (10, 12):
        print(f'\n  Topics for k={k}:')
        for tid, topic in lda.show_topics(num_words=8):
            words = ', '.join([w for w, _ in topic])
            print(f'    #{tid}: {words}')

print('\n=== LDA Summary ===')
print(f"{'k':>4} | {'C_v':>8} | {'UMass':>8} | {'LogPerp':>10}")
print('-'*40)
for k, v in sorted(lda_results.items()):
    print(f"{k:>4} | {v['c_v']:>8.4f} | {v['u_mass']:>8.4f} | {v['log_perplexity']:>10.2f}")

best_k, best_lda = best_model
print(f'\n✅ Best k={best_k} (C_v={best_cv:.4f})')

# Print best topics
print(f'\nBest model (k={best_k}) topics:')
for tid, topic in best_lda.show_topics(num_words=10):
    words = ', '.join([w for w, _ in topic])
    print(f'  #{tid}: {words}')

# Save results
with open(f'{OUT}/lda_results.json', 'w') as f:
    json.dump(lda_results, f, indent=2)

# Save SnowNLP scores
df.to_parquet(f'{OUT}/snownlp_full.parquet', index=False)
print(f'\n✅ All results saved to {OUT}/')
