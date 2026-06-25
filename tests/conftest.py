import pytest
from unittest.mock import MagicMock


@pytest.fixture(autouse=True)
def mock_transformer_pipelines(monkeypatch):
    """Mock transformers.pipeline used by TransformerSummarizer to avoid model downloads during tests."""
    def fake_pipeline(task, model=None, **kwargs):
        def summarizer(text, max_length=None, min_length=None):
            return [{'summary_text': f'MOCK SUMMARY from {model or "model"}'}]
        return summarizer

    # patch the pipeline symbol inside the nlp.transformer_summarizer module
    monkeypatch.setattr('nlp.transformer_summarizer.pipeline', fake_pipeline)
    # also patch transformers.pipeline in case other modules reference it
    monkeypatch.setattr('transformers.pipeline', fake_pipeline)
    yield