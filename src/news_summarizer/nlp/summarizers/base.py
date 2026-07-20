import time
from typing import Dict

class BaseSummarizer:
    model_name = 'base'
    summary_type = 'extractive'

    def summarize(self, text: str, **kwargs) -> Dict:
        start = time.time()
        summary = self._summarize(text, **kwargs)
        end = time.time()
        return {
            'summary_text': summary,
            'model_name': self.model_name,
            'summary_type': self.summary_type,
            'processing_time': end - start,
            'summary_length': len(summary.split())
        }

    def _summarize(self, text: str, **kwargs) -> str:
        raise NotImplementedError()
