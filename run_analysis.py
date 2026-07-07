#!/usr/bin/env python3
"""唐太宗v3.0 · A股论文 SnowNLP验证 + LDA改进"""
import pandas as pd
import numpy as np
import json, os, warnings
warnings.filterwarnings('ignore')

DATA = '/Users/lyu/Desktop/博士发表论文/1.A股趋势文章/预处理.xlsx'
OUT = '/Users/lyu/.openclaw/workspace/validation_output'
os.makedirs(OUT, exist_ok=True)

def main():
    print('='*60)
    print('PART 1: SnowNLP sentiment scoring (sequential)')
    print('='*60)

    df = pd.read_excel(DATA)
    df.columns = ['user', 'comment', 'date']
    print(f'Loaded {len(df)} comments')

    from snownlp import SnowNLP
    batch_size = 2000
    all_scores = []
    for i in range(0, len(df), batch_size):
        batch = df['comment'].iloc[i:i+batch_size].tolist()
        scores = []
        for j, text in enumerate(batch):
            try:
                scores.append(SnowNLP(str(text)).sentiments)
            except:
                scores.append(0.5)
            if (i + j) % 3000 == 0 and (i + j) > 0:
                pct = (i + j) / len(df) * 100
                print(f'  Progress: {i+j}/{len(df)} ({pct:.0f}%)')
        all_scores.extend(scores)

    df['snownlp_score'] = all_scores
    df['sentiment_label'] = pd.cut(df['snownlp_score'],
        bins=[0, 0.35, 0.65, 1.0],
        labels=['negative', 'neutral', 'positive'])

    print('\nSnowNLP distribution:')
    print(df['sentiment_label'].value_counts())
    print(f'Mean={np.mean(all_scores):.3f}  Std={np.std(all_scores):.3f}')

    # Part 2: Stratified sample for LLM
    print('\n' + '='*60)
    print('PART 2: Stratified sample 300 for LLM validation')
    print('='*60)
    np.random.seed(42)
    sampled = []
    for label in ['negative', 'neutral', 'positive']:
        pool = df[df['sentiment_label'] == label]
        n = min(100, len(pool))
        sampled.append(pool.sample(n=n, random_state=42))
    sample = pd.concat(sampled).sample(frac=1, random_state=42)
    sample[['comment', 'snownlp_score', 'sentiment_label']].to_json(
        f'{OUT}/llm_sample.json', orient='records', force_ascii=False)
    print(f'Saved {len(sample)} samples')

    # Part 3: LDA with gensim
    print('\n' + '='*60)
    print('PART 3: LDA topic optimization (jieba+gensim)')
    print('='*60)
    import jieba
    from gensim.corpora import Dictionary
    from gensim.models import CoherenceModel, LdaModel

    lda_df = df.sample(n=15000, random_state=42)
    texts = lda_df['comment'].tolist()
    print(f'Sampled {len(texts)} for LDA')

    stopwords = set('这个 那个 什么 怎么 为什么 可以 没有 不是 就是 '
                    '一个 我们 他们 你们 自己 知道 觉得 看到 所以 '
                    '但是 因为 如果 虽然 不过 还是 已经 可能 应该 '
                    '不会 不要 真的 只是 所有 这些 那些 这么 还是 '
                    '我 你 它 他 她 的 了 在 是 有 和 与 都 就 也 '
                    '不 很 会 要 没 被 把 让 对 那 这 还 上 下 看 '
                    '说 到 去 能 做 为 过 来 大 小 多 少 好 长 等 之 年 月'.split())

    tokenized = []
    for t in texts:
        words = jieba.lcut(str(t))
        words = [w for w in words if len(w) > 1 and w not in stopwords]
        if len(words) >= 3:
            tokenized.append(words)
    print(f'Valid texts: {len(tokenized)} (>=3 tokens, cleaned)')

    dictionary = Dictionary(tokenized)
    dictionary.filter_extremes(no_below=5, no_above=0.8)
    print(f'Dictionary: {len(dictionary)} terms')
    corpus = [dictionary.doc2bow(t) for t in tokenized]

    k_values = [5, 8, 10, 12, 15, 20]
    results = {}
    best_cv, best_k, best_model = -1, None, None

    for k in k_values:
        print(f'\nLDA k={k}...')
        lda = LdaModel(corpus=corpus, id2word=dictionary,
                       num_topics=k, random_state=42,
                       passes=10, iterations=200,
                       alpha='auto', eta='auto')

        cv = CoherenceModel(model=lda, texts=tokenized,
                           dictionary=dictionary,
                           coherence='c_v', topn=20).get_coherence()
        um = CoherenceModel(model=lda, corpus=corpus,
                           dictionary=dictionary,
                           coherence='u_mass').get_coherence()
        results[k] = {'c_v': round(cv, 4), 'u_mass': round(um, 4)}
        print(f'  C_v={cv:.4f}  UMass={um:.4f}')

        if cv > best_cv:
            best_cv, best_k, best_model = cv, k, lda

        if k in (8, 10, 12):
            print(f'  Topics (k={k}):')
            for tid, topic in lda.show_topics(num_words=8):
                words = ', '.join([w for w, _ in topic])
                print(f'    [{tid}] {words}')

    print('\n=== LDA Summary ===')
    print('k     | C_v     | UMass')
    print('-'*30)
    for k in sorted(results):
        r = results[k]
        print(f'{k:<5} | {r["c_v"]:<7} | {r["u_mass"]:<7}')

    print(f'\nBest: k={best_k}, C_v={best_cv:.4f}')
    print(f'Topics (k={best_k}):')
    for tid, topic in best_model.show_topics(num_words=10):
        words = ', '.join([w for w, _ in topic])
        print(f'  [{tid}] {words}')

    with open(f'{OUT}/lda_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    df[['comment', 'date', 'snownlp_score', 'sentiment_label']].to_parquet(
        f'{OUT}/snownlp_full.parquet', index=False)
    print(f'\nDone -> {OUT}/')

if __name__ == '__main__':
    main()
