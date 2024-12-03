from PyPDF2 import PdfReader
from pdf2image import convert_from_path
import pdfplumber
import pytesseract
from PIL import Image
import camelot

def extract_Text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

def extract_images_from_pdf(pdf_path):
    images = convert_from_path(pdf_path)
    image_paths = []

    for i, image in enumerate(images):
        image_path = f"page_{i}.png"
        image.save(image_path, "PNG")
        image_paths.append(image_path)
    return image_paths

def extract_tables_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        tabels = []
        for page in pdf.pages:
            table = page.extract_table()
            if table :
                tabels.append(table)
        return tabels
    
def extract_tables_from_camelot(pdf_path):
    tables = camelot.read_pdf(pdf_path, pages= 'all', flavor='stream')
    return tables

def ocr_on_image(image_path):
    img = Image.open(image_path)
    text = pytesseract.image_to_string(image=img)
    return text

def check_document_type(pdf_path):
    text = extract_Text_from_pdf(pdf_path)
    #images = extract_images_from_pdf(pdf_path)
    #tables = extract_tables_from_pdf(pdf_path)
    # print("Text: ", text)
    # print("Images: ", images)
    # print("Tables: ", tables)
    return text  # , images, tables
    
    # if text and not images and not tables:
    #     return "text_only"
    # elif not text and images and not tables:
    #     return "image_only"
    # elif not text and not images and tables:
    #     return "table_only"
    # elif text and images and not tables:
    #     return "text_and_images"
    # elif text and not images and tables:
    #     return "text_and_tables"
    # elif not text and images and tables:
    #     return "images_and_tables"
    # elif text and images and tables:
    #     return "text_images_and_tables"
    # else:
    #     return "empty"

def text_chunking(text, max_chunk_size= 250, overlap=50):
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chunk_size 
        chunk = text[start:end+1]
        chunks.append(chunk)
        start += max_chunk_size - overlap
    return chunks
    
def displaying_chunks(chunks):
    print("Length of Chunks before embeddings: ", len(chunks))
    for i, chunk  in enumerate(chunks):
        print(f"Chunk {i+1}:\n{chunk}\n\n")
