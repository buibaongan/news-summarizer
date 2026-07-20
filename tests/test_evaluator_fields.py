from news_summarizer.nlp import evaluator


def test_evaluator_with_reference(monkeypatch):
    # mock rouge scorer
    class FakeScores:
        def __init__(self):
            pass

    class FakeScore:
        def __init__(self, f):
            self.fmeasure = f

    class FakeRouge:
        def __init__(self, *args, **kwargs):
            pass

        def score(self, ref, summary):
            return {'rouge1': FakeScore(0.5), 'rouge2': FakeScore(0.25), 'rougeL': FakeScore(0.45)}

    monkeypatch.setattr('news_summarizer.nlp.evaluator.rouge_scorer', type('M', (), {'RougeScorer': lambda *a, **k: FakeRouge()}))
    monkeypatch.setattr('news_summarizer.nlp.evaluator.bert_score', lambda a, b, lang='en': ([0.6], [0.5], [0.55]))

    res = evaluator.evaluate_summary('summary text', reference='reference text')
    assert res['rouge_1'] == 0.5
    assert res['rouge_2'] == 0.25
    assert res['rouge_l'] == 0.45
    assert abs(res['bertscore_f1'] - 0.55) < 1e-6
    assert 'processing_time' in res and res['processing_time'] is not None
    assert res['summary_length'] == len('summary text'.split())


def test_evaluator_no_reference(monkeypatch):
    # ensure rouge_scorer and bert_score are None
    monkeypatch.setattr('news_summarizer.nlp.evaluator.rouge_scorer', None)
    monkeypatch.setattr('news_summarizer.nlp.evaluator.bert_score', None)

    res = evaluator.evaluate_summary('summary only', reference=None)
    assert res['rouge_1'] is None
    assert res['rouge_2'] is None
    assert res['rouge_l'] is None
    assert res['bertscore_f1'] is None
    assert res['processing_time'] is not None
    assert res['summary_length'] == len('summary only'.split())
