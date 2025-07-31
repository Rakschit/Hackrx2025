import fitz

def extract_text_from_pdf(file_path):
    file = fitz.open(file_path)
    text = ""
    for page in file:
        text += page.get_text("text")
    file.close()
    return text