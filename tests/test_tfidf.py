from news_summarizer.nlp.summarizers.tfidf import TFIDFSummarizer

def test_tfidf_basic():
    text = "Sentence one.\nSentence two about python.\nSentence three about testing."
    s = TFIDFSummarizer()
    out = s.summarize(text)
    assert 'summary_text' in out
