from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pytesseract
from PIL import Image
import io
import uvicorn
import os
import platform


# Configure Tesseract path based on platform
def configure_tesseract():
    system = platform.system().lower()

    # Check for environment variable first (for Heroku/Docker)
    if os.getenv("TESSERACT_CMD"):
        pytesseract.pytesseract.tesseract_cmd = os.getenv("TESSERACT_CMD")
    elif system == "windows":
        # Common Windows paths
        windows_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        ]
        for path in windows_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                break
    # Linux/Unix systems typically have tesseract in PATH


configure_tesseract()

app = FastAPI(title="OCR API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_TYPES = {"image/jpeg", "image/jpg", "image/png"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Validate file type
        if file.content_type not in ALLOWED_TYPES:
            return {"success": False, "error": "Only JPG and PNG files are allowed"}

        # Read file content
        content = await file.read()

        # Validate file size
        if len(content) > MAX_FILE_SIZE:
            return {"success": False, "error": "File size exceeds 10MB limit"}

        # Validate file extension
        filename_lower = file.filename.lower() if file.filename else ""
        if not any(filename_lower.endswith(ext) for ext in ALLOWED_EXTENSIONS):
            return {"success": False, "error": "Invalid file extension"}

        # Process image with OCR
        try:
            image = Image.open(io.BytesIO(content))
            extracted_text = pytesseract.image_to_string(image)

            return {"success": True, "text": extracted_text.strip()}

        except Exception as ocr_error:
            return {
                "success": False,
                "error": f"OCR processing failed: {str(ocr_error)}",
            }

    except Exception as e:
        return {"success": False, "error": f"File processing failed: {str(e)}"}
