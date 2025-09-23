import fitz  # PyMuPDF (for PDFs)
from openai import OpenAI
import json
import os
import base64
import time
from docx import Document
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models import DynamicPrompt, ProcessedDocument
from app.logger import get_logger

logger = get_logger(__name__)

class DocumentProcessor:
    def __init__(self, openai_api_key: str):
        self.client = OpenAI(api_key=openai_api_key)
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from both text-based and scanned PDFs using OpenAI Vision when needed."""
        doc = fitz.open(pdf_path)
        full_text = ""

        for page_num, page in enumerate(doc, start=1):
            text = page.get_text("text")

            if text.strip():  
                logger.info(f"[Page {page_num}] ✅ Text detected directly")
                full_text += text + "\n"
            else:
                logger.info(f"[Page {page_num}] 🔍 No text found, using OpenAI Vision OCR...")
                pix = page.get_pixmap(dpi=200)  # render page as image
                img_bytes = pix.tobytes("png")
                img_b64 = base64.b64encode(img_bytes).decode("utf-8")

                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "Extract all text clearly from this image."},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/png;base64,{img_b64}"},
                                },
                            ],
                        }
                    ],
                )

                page_text = response.choices[0].message.content.strip()
                full_text += page_text + "\n"

        return full_text.strip()

    def extract_text_from_docx(self, docx_path: str) -> str:
        """Extract text from DOCX files."""
        doc = Document(docx_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text.strip()

    def extract_text_from_txt(self, txt_path: str) -> str:
        """Extract text from TXT files."""
        with open(txt_path, "r", encoding="utf-8") as f:
            return f.read().strip()

    def extract_text_from_image_with_openai(self, image_path: str) -> str:
        """Extract text from images using OpenAI Vision."""
        with open(image_path, "rb") as f:
            img_bytes = f.read()
        img_b64 = base64.b64encode(img_bytes).decode("utf-8")

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract all text clearly from this image."},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"},
                        },
                    ],
                }
            ],
        )

        return response.choices[0].message.content.strip()

    def extract_text(self, file_path: str) -> str:
        """Auto-detect file type and extract text."""
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".pdf":
            return self.extract_text_from_pdf(file_path)
        elif ext == ".docx":
            return self.extract_text_from_docx(file_path)
        elif ext == ".txt":
            return self.extract_text_from_txt(file_path)
        elif ext in [".jpg", ".jpeg", ".png", ".jfif", ".bmp", ".tiff", ".tif", ".webp", ".heic"]:
            return self.extract_text_from_image_with_openai(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

    def process_text_with_prompt(self, text: str, prompt_template: str) -> Dict[str, Any]:
        """Process extracted text using a custom prompt template."""
        # Replace {text} placeholder in the prompt template with actual text
        prompt = prompt_template.format(text=text)
        
        # Measure processing time
        start_time = time.time()
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        
        end_time = time.time()
        elapsed = end_time - start_time
        content = response.choices[0].message.content.strip()

        # Strip markdown code blocks if present
        if content.startswith("```"):
            content = "\n".join(content.split("\n")[1:])
            if content.endswith("```"):
                content = "\n".join(content.split("\n")[:-1])

        try:
            parsed = json.loads(content)
        except Exception as e:
            logger.error(f"Error converting text to JSON: {e}")
            parsed = {"raw_output": content, "error": str(e)}

        # Log usage statistics
        usage = response.usage
        logger.info(f"Processing completed - Total tokens: {usage.total_tokens}, Time: {elapsed:.2f}s")

        return {
            "result": parsed,
            "usage": {
                "total_tokens": usage.total_tokens,
                "processing_time": elapsed
            }
        }

    def process_document(self, db: Session, user_id: str, prompt_id: str, file_path: str, original_filename: str) -> ProcessedDocument:
        """Process a document with a specific prompt and save results to database."""
        try:
            # Get the prompt from database
            prompt = db.query(DynamicPrompt).filter(
                DynamicPrompt.id == prompt_id,
                DynamicPrompt.user_id == user_id,
                DynamicPrompt.is_active == True
            ).first()
            
            if not prompt:
                raise ValueError("Prompt not found or not active")

            # Create processing record
            file_type = os.path.splitext(file_path)[1].lower()
            processed_doc = ProcessedDocument(
                user_id=user_id,
                prompt_id=prompt_id,
                original_filename=original_filename,
                file_path=file_path,
                file_type=file_type,
                processing_status="processing"
            )
            db.add(processed_doc)
            db.commit()
            db.refresh(processed_doc)

            # Extract text from document
            logger.info(f"Extracting text from {original_filename}")
            extracted_text = self.extract_text(file_path)
            
            # Update with extracted text
            processed_doc.extracted_text = extracted_text
            db.commit()

            # Process text with custom prompt
            logger.info(f"Processing text with prompt: {prompt.name}")
            result = self.process_text_with_prompt(extracted_text, prompt.prompt_template)
            
            # Update with final result
            processed_doc.processed_result = json.dumps(result["result"])
            processed_doc.processing_status = "completed"
            db.commit()

            logger.info(f"Document processing completed successfully for {original_filename}")
            return processed_doc

        except Exception as e:
            logger.error(f"Error processing document {original_filename}: {str(e)}")
            
            # Update processing record with error
            if 'processed_doc' in locals():
                processed_doc.processing_status = "failed"
                processed_doc.error_message = str(e)
                db.commit()
            
            raise e

    def get_file_type(self, file_path: str) -> str:
        """Get file type from file path."""
        return os.path.splitext(file_path)[1].lower()
