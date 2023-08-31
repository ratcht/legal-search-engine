from PyPDF2 import PdfReader

# read pdf
def read_pdf(file_path: str) -> list:
  reader = PdfReader(file_path)
  chunks = []
  for page in reader.pages:
    chunks.append(page.extract_text())
  return chunks

def read_pdf_from_file(file) -> list:
  reader = PdfReader(file)
  chunks = []
  for page in reader.pages:
    excerpt = page.extract_text()
    chunks.append(excerpt)
  return chunks