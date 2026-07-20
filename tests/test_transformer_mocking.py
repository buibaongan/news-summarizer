from news_summarizer.nlp.summarizers.transformer import TransformerSummarizer


def test_transformer_summarizer_is_mocked():
    mnames = ['facebook/bart-large-cnn', 't5-small']
    for mn in mnames:
        s = TransformerSummarizer(model_name=mn)
        out = s.summarize('Some long text to summarize')
        assert 'MOCK SUMMARY' in out['summary_text']
        assert out['model_name'] == mn
        assert out['summary_length'] >= 1
