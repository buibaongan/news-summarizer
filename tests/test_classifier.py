from news_summarizer.nlp.classifier import classify_by_keywords


def test_entertainment_article_is_not_classified_as_technology():
    text = "Could a Madison Square Garden wedding be the love story of Taylor Swift's wildest dreams?"

    assert classify_by_keywords(text) == 'entertainment'


def test_ai_keyword_requires_whole_word_match():
    assert classify_by_keywords('The company said profits increased') == 'business'
    assert classify_by_keywords('New AI software improves hospital scheduling') == 'technology'
