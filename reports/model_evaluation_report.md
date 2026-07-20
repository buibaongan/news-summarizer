# Model Evaluation Report

Generated: 2026-06-25  
Dataset: `data/evaluation/sample.jsonl`  
Current dataset: 50 longer, diverse article-style samples  
Database inspected: `news.db`

## How It Was Evaluated

Command used:

```bash
PYTHONPATH=src .venv/bin/python -m scripts.run_evaluation \
  --dataset data/evaluation/sample.jsonl \
  --models tfidf,textrank,t5,bart
```

The script saves summaries and metrics into `news.db`. I also inspected the actual saved summaries, not only the final scores.

Important: `scripts.run_evaluation` appends results every time. So the printed table is cumulative and includes repeated/older runs.


## Current 50-Sample Scores

This table uses only the latest saved result for each current sample and model:

| Model | Samples | Avg Time | Avg Words | ROUGE-1 | ROUGE-2 | ROUGE-L | BERT F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| `facebook/bart-large-cnn` | 50 | 5.1219 | 37.64 | 0.3316 | 0.0948 | 0.2459 | 0.8910 |
| `t5-small` | 50 | 1.6049 | 40.64 | 0.3000 | 0.0847 | 0.2305 | 0.8772 |
| `tfidf` | 50 | 0.0019 | 91.04 | 0.2656 | 0.0759 | 0.1954 | 0.8890 |
| `textrank` | 50 | 0.0028 | 89.32 | 0.2628 | 0.0790 | 0.1872 | 0.8871 |

## Short Conclusion

`facebook/bart-large-cnn` is the best overall summarizer.

Why: it has the best current ROUGE scores, the best current BERT F1, and the most readable summaries. It usually captures the main point without copying most of the article.

`t5-small` is the best compromise if BART is too slow.

Why: it is much faster than BART and still produces concise summaries, but the writing is rougher. It often starts lowercase, has awkward punctuation, and sometimes misses the article's main framing.

`tfidf` and `textrank` are best for speed, not quality.

Why: they are almost instant and factual because they copy source sentences. But their summaries are around 90 words on average, more than twice as long as BART/T5. They often feel like excerpts instead of summaries.

## Model Comments

### BART

Best quality. For example, on the USGS water sample, BART clearly summarized the tool, the water-stress causes, and the planning purpose in about 44 words. This is close to what a human summary should look like.

Weakness: slow on CPU, about 5 seconds per summary.

### T5

Good speed/quality middle ground. It compresses better than extractive models, but its style is weaker. Example issue: it produced text like `lifestyle intervention can reduce...` with lowercase starts and extra spaces before periods.

Weakness: needs generation tuning or post-processing.

### TF-IDF

Very fast and safe. It usually keeps correct facts because it copies sentences directly from the input.

Weakness: too long. For the BLS employment sample, it returned a long multi-sentence excerpt instead of a tight summary.

### TextRank

Also very fast and factual. It sometimes chooses useful sentences, but the order can be awkward.

Weakness: like TF-IDF, it is too extractive and often too long.

## Why BERTScore Is Close

BERTScore measures semantic similarity. Long extractive summaries keep many meanings from the article, so `tfidf` and `textrank` can score close to BART even when they are less readable.

That is why summary length matters:

- BART: ~38 words
- T5: ~41 words
- TF-IDF: ~91 words
- TextRank: ~89 words

So BERTScore alone does not mean best summary. BART wins because it balances semantic similarity, concision, and readability.

## Recommendation

For demos:

- Use `tfidf` for instant results.
- Use `bart` when showing best summary quality.
- Use `t5` when BART is too slow but you still want abstractive summaries.

For future improvement:

- Clear or separate the evaluation database before each official run.
- Batch BERTScore so evaluation is faster.
- Add compression ratio as a metric.
- Tune BART/T5 generation lengths for short and medium articles.
