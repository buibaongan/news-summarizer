from news_summarizer.nlp.summarizers.base import BaseSummarizer
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

class TFIDFSummarizer(BaseSummarizer):
    model_name = 'tfidf'
    summary_type = 'extractive'

    def _summarize(self, text: str, sentences=5, **kwargs) -> str:
        sents = [s.strip() for s in text.split('\n') if s.strip()]
        if not sents:
            return ''
        vec = TfidfVectorizer(stop_words='english')
        try:
            X = vec.fit_transform(sents)
            scores = np.asarray(X.sum(axis=1)).ravel()
            idx = np.argsort(-scores)[:sentences]
            selected = [sents[i] for i in sorted(idx)]
            return ' '.join(selected)
        except Exception:
            return ' '.join(sents[:sentences])
