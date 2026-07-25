"""SnowNLP Validation & LDA Improvement for A股论文"""
import pandas as pd
import numpy as np
from snownlp import SnowNLP
import json, random, time, os

DATA = '/Users/lyu/Desktop/博士发表论文/1.A股趋势文章/预处理.xlsx'
OUTPUT = '/Users/lyu/.openclaw/workspace/validation_output'

os.makedirs(OUTPUT, exist_ok=True)

# ── Step 1: Load data ──
print('Loading data...')
df = pd.read_excel(DATA)
df.columns = ['user', 'comment', 'date']
print(f'Total comments: {len(df)}')

# ── Step 2: Run SnowNLP on a sample (first run on all to get distribution) ──
print('Running SnowNLP on all 85k comments... (this takes a few minutes)')

def snownlp_sentiment(text):
    try:
        s = SnowNLP(str(text))
        return s.sentiments  # 0-1, >0.5 = positive
    except:
        return 0.5  # neutral for errors

# Run on all texts - use batches with progress
batch_size = 1000
all_scores = []
for i in range(0, len(df), batch_size):
    batch = df['comment'].iloc[i:i+batch_size].tolist()
    scores = [snownlp_sentiment(t) for t in batch]
    all_scores.extend(scores)
    if (i // batch_size) % 5 == 0:
        print(f'  Processed {i+len(batch)}/{len(df)}...')

df['snownlp_score'] = all_scores
df['snownlp_class'] = df['snownlp_score'].apply(
    lambda x: 'negative' if x < 0.4 else ('neutral' if x < 0.6 else 'positive'))

print(f'\nSnowNLP distribution:')
print(df['snownlp_class'].value_counts())
print(f'Mean: {df["snownlp_score"].mean():.3f}, Std: {df["snownlp_score"].std():.3f}')

# ── Step 3: Stratified sample for LLM validation ──
n_sample = 300
stratified = []
samples_per_class = n_sample // 3
for cls in ['negative', 'neutral', 'positive']:
    pool = df[df['snownlp_class'] == cls]
    n = min(samples_per_class, len(pool))
    stratified.append(pool.sample(n=n, random_state=42))
sample_df = pd.concat(stratified).sample(frac=1, random_state=42).reset_index(drop=True)

# Save sample for LLM labeling
sample_out = sample_df[['comment', 'snownlp_score', 'snownlp_class']].copy()
sample_out.to_json(f'{OUTPUT}/sentiment_sample.json', orient='records', force_ascii=False)
sample_df.to_excel(f'{OUTPUT}/sentiment_sample.xlsx', index=False)
print(f'\nSaved {len(sample_df)} stratified samples to {OUTPUT}/')

# ── Step 4: Run LDA with sklearn ──
print('\n--- LDA Topic Modeling ---')
# SnowNLP-based segmentation function
def tokenize(text):
    try:
        s = SnowNLP(str(text))
        return ' '.join(s.words)
    except:
        return ''

# Sample 10k for LDA (85k full LDA is heavy)
lda_sample = df.sample(n=10000, random_state=42)
print(f'Tokenizing {len(lda_sample)} comments for LDA...')
lda_sample['tokens'] = lda_sample['comment'].apply(tokenize)

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation

# Filter short texts
valid = lda_sample[lda_sample['tokens'].str.split().str.len() >= 3]
print(f'Valid texts (≥3 tokens): {len(valid)}')

vectorizer = CountVectorizer(max_features=3000, min_df=5, max_df=0.85)
dtm = vectorizer.fit_transform(valid['tokens'])
vocab = vectorizer.get_feature_names_out()
print(f'DTM shape: {dtm.shape}')
print(f'Vocabulary size: {len(vocab)}')

# Try multiple topic numbers
k_values = [5, 8, 10, 12, 15, 20]
results = {}

for k in k_values:
    print(f'\nTraining LDA with k={k}...')
    lda = LatentDirichletAllocation(
        n_components=k,
        random_state=42,
        max_iter=100,
        learning_method='batch',
        n_jobs=-1
    )
    lda.fit(dtm)
    
    # Log-likelihood (per-word)
    ll = lda.score(dtm)
    perplexity = lda.perplexity(dtm)
    
    # Calculate pseudo-coherence: average topic-word probability for top words
    top_words_per_topic = []
    for topic_idx, topic in enumerate(lda.components_):
        top_n = 10
        top_word_indices = topic.argsort()[:-top_n-1:-1]
        top_words = [(vocab[i], topic[i]) for i in top_word_indices]
        top_words_per_topic.append(top_words)
        print(f'  Topic {topic_idx}: {", ".join([w for w,p in top_words[:8]])}')
    
    # Simple coherence proxy: average pairwise PMI of top words
    # Use word co-occurrence in the DTM
    from sklearn.metrics.pairwise import cosine_similarity
    word_doc_matrix = dtm.T  # words × docs
    coherence_scores = []
    for topic_words in top_words_per_topic:
        word_idxs = [list(vocab).index(w) for w, _ in topic_words if w in vocab]
        if len(word_idxs) < 2:
            continue
        # Get word vectors from DTM
        word_vecs = word_doc_matrix[word_idxs].toarray()
        sim = cosine_similarity(word_vecs)
        # Upper triangle mean
        triu = np.triu(sim, k=1)
        if triu.sum() > 0:
            coherence_scores.append(triu[triu > 0].mean())
    
    avg_coherence = np.mean(coherence_scores) if coherence_scores else 0
    results[k] = {
        'log_likelihood': ll,
        'perplexity': perplexity,
        'pseudo_coherence': avg_coherence
    }
    print(f'  Perplexity: {perplexity:.1f}, Pseudo-coherence: {avg_coherence:.4f}')

# Results summary
print('\n=== LDA Results Summary ===')
for k, v in sorted(results.items()):
    print(f'k={k}: LL={v["log_likelihood"]:.1f}, Perp={v["perplexity"]:.1f}, Coh={v["pseudo_coherence"]:.4f}')

# Save results
with open(f'{OUTPUT}/lda_results.json', 'w') as f:
    json.dump({str(k): v for k, v in results.items()}, f, indent=2, default=str)

# ── Step 5: Save full data with SnowNLP scores ──
df.to_parquet(f'{OUTPUT}/all_scores.parquet', index=False)
print(f'\n✅ All done. Files saved to {OUTPUT}/')
print('Summary:')
print(f'  - SnowNLP done on all {len(df)} comments')
print(f'  - Stratified sample ({n_sample}) ready for LLM validation')
print(f'  - LDA run on {k_values}')
