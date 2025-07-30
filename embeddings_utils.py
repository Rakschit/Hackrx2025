import hashlib # add to requirements




def normalize_text(text):
    text = " ".join(text.split())
    return text

def get_content_hash(normalized):
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()




