#!/usr/bin/env python3
"""唐太宗v3.0 · A股 SnowNLP验证 + LDA"""
import pandas as pd, numpy as np, json, os, warnings
warnings.filterwarnings('ignore')

DATA = '/Users/lyu/Desktop/博士发表论文/1.A股趋势文章/预处理.xlsx'
OUT = '/Users/lyu/.openclaw/workspace/validation_output'
os.makedirs(OUT, exist_ok=True)

def main():
    # Load & sample 15k (SnowNLP on 85k is too slow)
    df = pd.read_excel(DATA)
    df.columns = ['user', 'comment', 'date']
    print(f'Loaded {len(df)} comments')

    smpl = df.sample(n=15000, random_state=42).reset_index(drop=True)
    print(f'Working on {len(smpl)} sample')

    # ── SnowNLP ──
    print('Running SnowNLP...')
    from snownlp import SnowNLP
    scores = []
    for i, t in enumerate(smpl['comment']):
        try:
            scores.append(SnowNLP(str(t)).sentiments)
        except:
            scores.append(0.5)
        if (i+1) % 2000 == 0:
            print(f'  SnowNLP: {i+1}/{len(smpl)}')
    smpl['snownlp_score'] = scores
    # Use 0.4/0.6 thresholds (better than 0.35/0.65 for SnowNLP)
    smpl['snownlp_label'] = pd.cut(scores, bins=[0, 0.4, 0.6, 1.0],
                                    labels=['negative', 'neutral', 'positive'])

    print('\nSnowNLP distribution:')
    print(smpl['snownlp_label'].value_counts())
    print(f'Mean={np.mean(scores):.3f}  Std={np.std(scores):.3f}')

    # ── Stratified sample 300 for LLM ──
    np.random.seed(42)
    chunks = []
    for lab in ['negative', 'neutral', 'positive']:
        pool = smpl[smpl['snownlp_label'] == lab]
        n = min(100, len(pool))
        chunks.append(pool.sample(n=n, random_state=42))
    llm_sample = pd.concat(chunks).sample(frac=1, random_state=42)
    llm_sample[['comment', 'snownlp_score', 'snownlp_label']].to_json(
        f'{OUT}/llm_sample.json', orient='records', force_ascii=False)
    print(f'Saved {len(llm_sample)} LLM validation samples')

    # ── LDA with jieba + gensim ──
    print('\nRunning LDA...')
    import jieba
    from gensim.corpora import Dictionary
    from gensim.models import CoherenceModel, LdaModel

    stop = set('这个 那个 什么 怎么 为什么 可以 没有 不是 就是 '
               '一个 我们 他们 你们 自己 知道 觉得 看到 所以 '
               '但是 因为 如果 虽然 不过 还是 已经 可能 应该 '
               '不会 不要 真的 只是 所有 这些 那些 这么 还是 '
               '我 你 它 他 她 的 了 在 是 有 和 与 都 就 也 '
               '不 很 会 要 没 被 把 让 对 那 这 还 上 下 看 '
               '说 到 去 能 做 为 过 来 大 小 多 少 好 长 等 之 年 月 时 点'.split())

    print('Tokenizing with jieba...')
    tokenized = []
    for t in smpl['comment']:
        words = [w for w in jieba.lcut(str(t)) if len(w) > 1 and w not in stop]
        if len(words) >= 3:
            tokenized.append(words)
    print(f'Valid texts: {len(tokenized)}')

    dictionary = Dictionary(tokenized)
    dictionary.filter_extremes(no_below=5, no_above=0.8)
    print(f'Dictionary: {len(dictionary)} terms')
    corpus = [dictionary.doc2bow(t) for t in tokenized]

    k_values = [5, 8, 10, 12, 15, 20]
    res = {}
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
        res[k] = {'c_v': round(cv, 4), 'u_mass': round(um, 4)}
        print(f'  C_v={cv:.4f}  UMass={um:.4f}')

        if cv > best_cv:
            best_cv, best_k, best_model = cv, k, lda

        if k in (8, 10, 12):
            for tid_str, topic_str in lda.show_topics(num_words=8):
                # topic_str looks like '0.023*"word" + 0.015*"word2"'
                parts = topic_str.split('+')
                words = []
                for p in parts:
                    try:
                        w = p.split('*')[1].strip().strip('"')
                        words.append(w)
                    except:
                        pass
                print(f'  [{tid_str}] {", ".join(words[:8])}')

    print('\n=== LDA Summary ===')
    print('k     | C_v     | UMass')
    print('-'*30)
    for k in sorted(res):
        r = res[k]
        print(f'{k:<5} | {r["c_v"]:<7} | {r["u_mass"]:<7}')

    print(f'\nBest: k={best_k}, C_v={best_cv:.4f}')
    for tid, topic in best_model.show_topics(num_words=10):
        words = ', '.join([w for w, _ in topic])
        print(f'  [{tid}] {words}')

    # Save
    with open(f'{OUT}/lda_results.json', 'w') as f:
        json.dump(res, f, indent=2)
    smpl[['comment', 'date', 'snownlp_score', 'snownlp_label']].to_parquet(
        f'{OUT}/snownlp_15k.parquet', index=False)
    print(f'\nDone -> {OUT}/')

if __name__ == '__main__':
    main()
