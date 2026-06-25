import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.stem import WordNetLemmatizer
import re

_nlp_ready = False

def ensure_nltk():
    global _nlp_ready
    if _nlp_ready:
        return
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')
    _nlp_ready = True

def preprocess_text(text: str):
    ensure_nltk()
    sents = sent_tokenize(text)
    lemmatizer = WordNetLemmatizer()
    sw = set(stopwords.words('english'))
    cleaned = []
    for s in sents:
        words = [w.lower() for w in word_tokenize(s) if re.search(r"[a-zA-Z0-9]", w)]
        words = [w for w in words if w not in sw]
        lem = [lemmatizer.lemmatize(w) for w in words]
        if len(lem) >= 3:
            cleaned.append({'sentence': s, 'tokens': lem})
    return cleaned
