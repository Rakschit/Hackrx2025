import fitz
from langchain_text_splitters import RecursiveCharacterTextSplitter

def extract_text_from_pdf(file_path):
    file = fitz.open(file_path)
    text = ""
    for page in file:
        text += page.get_text("text")
    file.close()
    return text

'''def extract_text_from_docx(file_path):
    file = docx(file_path)
    text = ""
    for para in file.paragraphs:
        text += para.text + "\n"
    return text
'''



def chunk_text(cl_text):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,      
        chunk_overlap=100,    
        separators=["\n\n", "\n", ".", " "]
    )
    
    chunks = text_splitter.split_text(cl_text)
    return chunks