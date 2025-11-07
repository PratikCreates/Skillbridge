import io
import base64
import fitz  # PyMuPDF
from openai import OpenAI
from skillbridge.utils.config import AIML_API_KEY, AIML_API_BASE
import logging

# Instantiate the AIML client, which we will use for OCR.
ai_client = OpenAI(api_key=AIML_API_KEY, base_url=AIML_API_BASE)
logger = logging.getLogger(__name__)

def ocr_image_with_ai(image_bytes: bytes) -> str:
    """Sends image bytes to a multimodal AI (GPT-4o) for OCR."""
    try:
        b64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        # --- THIS IS THE SOTA CHOICE ---
        # We are explicitly calling the powerful and cost-effective gpt-4o model.
        response = ai_client.chat.completions.create(
            model="openai/gpt-4o", 
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "You are an expert OCR system. Extract all text from this image of a resume. Preserve the layout, spacing, and structure as accurately as possible."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{b64_image}"
                            },
                        },
                    ],
                }
            ],
            max_tokens=4000,
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        logger.error(f"AI-powered OCR failed: {e}")
        return ""

def parse_resume(file_content: bytes, filename: str) -> str:
    """
    An advanced resume parser that intelligently handles digital PDFs,
    scanned PDFs (via OCR), DOCX, TXT, and common image formats.
    """
    text = ""
    file_lower = filename.lower()
    logger.info(f"Parsing file: {filename}")

    if file_lower.endswith(".pdf"):
        try:
            # Use PyMuPDF (fitz) for robust PDF handling
            pdf_document = fitz.open(stream=file_content, filetype="pdf")
            for page_num in range(len(pdf_document)):
                page = pdf_document.load_page(page_num)
                # First, try to extract text directly
                page_text = page.get_text("text")
                # If the page has meaningful text, use it.
                if len(page_text.strip()) > 20: # A small threshold to avoid empty text blocks
                    text += page_text + "\n"
                else:
                    # If no text is found, it's a scanned image. Use our new OCR function.
                    logger.warning(f"Page {page_num+1} appears to be a scan. Attempting AI OCR...")
                    pix = page.get_pixmap()
                    img_bytes = pix.tobytes("jpeg")
                    text += ocr_image_with_ai(img_bytes) + "\n"
            return text
        except Exception as e:
            logger.error(f"Error processing PDF {filename}: {e}")
            return ""

    elif file_lower.endswith(".docx"):
        # This requires the python-docx library
        import docx
        doc = docx.Document(io.BytesIO(file_content))
        return "\n".join(para.text for para in doc.paragraphs)
        
    elif file_lower.endswith((".txt", ".md")):
        return file_content.decode("utf-8", errors="ignore")
        
    elif file_lower.endswith((".png", ".jpg", ".jpeg")):
        # Directly OCR image file types
        return ocr_image_with_ai(file_content)

    logger.warning(f"Unsupported file type for parsing: {filename}")
    return ""