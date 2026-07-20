import time
from typing import Optional, Dict

try:
    from rouge_score import rouge_scorer
except Exception:
    rouge_scorer = None

try:
    from bert_score import score as bert_score
except Exception:
    bert_score = None

def evaluate_summary(summary: str, reference: Optional[str] = None) -> Dict:
    start = time.time()
    results = {'processing_time': None, 'summary_length': len(summary.split())}
    if reference and rouge_scorer:
        scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
        scores = scorer.score(reference, summary)
        results.update({
            'rouge_1': scores['rouge1'].fmeasure,
            'rouge_2': scores['rouge2'].fmeasure,
            'rouge_l': scores['rougeL'].fmeasure
        })
    else:
        results.update({'rouge_1': None, 'rouge_2': None, 'rouge_l': None})

    if reference and bert_score:
        P, R, F = bert_score([summary], [reference], lang='en')
        results.update({'bertscore_precision': _mean_float(P), 'bertscore_recall': _mean_float(R), 'bertscore_f1': _mean_float(F)})
    else:
        results.update({'bertscore_precision': None, 'bertscore_recall': None, 'bertscore_f1': None})

    results['processing_time'] = time.time() - start
    return results


def _mean_float(value):
    if hasattr(value, 'mean'):
        return float(value.mean())
    if isinstance(value, (list, tuple)):
        return float(sum(value) / len(value)) if value else None
    return float(value)
