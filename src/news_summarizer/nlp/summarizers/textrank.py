from news_summarizer.nlp.summarizers.base import BaseSummarizer
import numpy as np
import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class TextRankSummarizer(BaseSummarizer):
    model_name = 'textrank'
    summary_type = 'extractive'

    def _summarize(self, text: str, sentences=5, **kwargs) -> str:
        sents = [s.strip() for s in text.split('\n') if s.strip()]
        if len(sents) <= sentences:
            return ' '.join(sents)
        try:
            vec = TfidfVectorizer(stop_words='english').fit_transform(sents)
            sim = cosine_similarity(vec)
            nx_graph = nx.from_numpy_array(sim)
            scores = nx.pagerank(nx_graph)
            ranked = sorted(((scores[i], s) for i, s in enumerate(sents)), reverse=True)
            selected = [r[1] for r in ranked[:sentences]]
            return ' '.join(selected)
        except Exception:
            return ' '.join(sents[:sentences])
