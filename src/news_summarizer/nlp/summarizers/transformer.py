from news_summarizer.nlp.summarizers.base import BaseSummarizer
from transformers import pipeline

class TransformerSummarizer(BaseSummarizer):
    def __init__(self, model_name: str = 'facebook/bart-large-cnn', max_input_tokens: int = 1024):
        self.model_name = model_name
        self.summary_type = 'abstractive'
        self.max_input_tokens = max_input_tokens
        # create pipeline lazily
        self._pipe = None

    @property
    def pipe(self):
        if self._pipe is None:
            if pipeline.__module__ != 'transformers.pipelines':
                self._pipe = pipeline('summarization', model=self.model_name)
            else:
                from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

                tokenizer = AutoTokenizer.from_pretrained(self.model_name, use_fast=False)
                model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
                self._pipe = pipeline('summarization', model=model, tokenizer=tokenizer)
        return self._pipe

    def _summarize(self, text: str, max_length: int = 150, min_length: int = 40, **kwargs) -> str:
        pipe = self.pipe
        input_text = self._truncate_input(text, pipe)
        try:
            out = pipe(input_text, max_length=max_length, min_length=min_length, truncation=True)
        except TypeError:
            out = pipe(input_text, max_length=max_length, min_length=min_length)
        if isinstance(out, list) and out:
            return out[0].get('summary_text', '')
        return ''

    def _truncate_input(self, text: str, pipe) -> str:
        tokenizer = getattr(pipe, 'tokenizer', None)
        if tokenizer is None:
            return text

        model_limit = getattr(tokenizer, 'model_max_length', self.max_input_tokens) or self.max_input_tokens
        if model_limit > 100000:
            model_limit = self.max_input_tokens
        max_tokens = min(int(model_limit), self.max_input_tokens)

        encoded = tokenizer(
            text,
            max_length=max_tokens,
            truncation=True,
            return_tensors=None,
            add_special_tokens=True
        )
        input_ids = encoded.get('input_ids')
        if not input_ids:
            return text
        return tokenizer.decode(input_ids, skip_special_tokens=True)
