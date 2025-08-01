import fitz

def extract_text_from_pdf(file_path: str):

    with fitz.open(file_path) as doc:
        page_count = doc.page_count
        text = ""
        for page in doc:
            text += page.get_text("text")
    return text, page_count 