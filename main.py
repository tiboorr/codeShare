import os
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional
import secrets
import mimetypes
from urllib.parse import quote

from fastapi import (
    FastAPI,
    Request,
    UploadFile,
    File,
    Form,
    HTTPException,
    Depends,
    status,
)
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse, PlainTextResponse, Response, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv

from database import get_db, engine
import models
import crud

# Load environment variables
load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

# File upload settings
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 524288000))  # 500MB
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))

# Authentication passwords
UPLOAD_PASSWORD = os.getenv("UPLOAD_PASSWORD", "upload123")
PRIVATE_VIEW_PASSWORD = os.getenv("PRIVATE_VIEW_PASSWORD", "private123")
DELETE_PASSWORD = os.getenv("DELETE_PASSWORD", os.getenv("UPLOAD_PASSWORD", "upload123"))

# Rate limiting configuration
# Format: "requests_per_minute/minute;requests_per_hour/hour"
RATE_LIMIT_UPLOAD = "20/minute;100/hour"           # Upload endpoint
RATE_LIMIT_DELETE = "30/minute;100/hour"         # Delete endpoint
RATE_LIMIT_DOWNLOAD = "50/minute;150/hour"       # Download endpoint
RATE_LIMIT_PREVIEW = "100/minute;200/hour"        # Preview endpoint
RATE_LIMIT_PAGES = "200/minute;500/hour"         # Page access (/, /public, /private, etc.)

# Text file extensions for preview
TEXT_EXTENSIONS = {
    '.txt', '.py', '.java', '.c', '.cpp', '.h', '.hpp', '.js', '.ts',
    '.html', '.css', '.json', '.xml', '.yaml', '.yml', '.md', '.rst',
    '.sh', '.bat', '.ps1', '.sql', '.go', '.rs', '.php', '.rb', '.pl',
    '.swift', '.kt', '.scala', '.r', '.m', '.cs', '.vb', '.lua', '.vim'
}

# ============================================================================
# SETUP
# ============================================================================

# Create uploads directory
UPLOAD_DIR.mkdir(exist_ok=True)

# Create static directory
STATIC_DIR = Path("static")
STATIC_DIR.mkdir(exist_ok=True)

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Initialize FastAPI
app = FastAPI(
    title="codeShare",
    description="FastAPI file sharing application",
    version="1.0.0"
)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Add timezone filter for Jinja2
def format_datetime_local(dt):
    """Convert UTC datetime to local time (UTC+2)"""
    if dt:
        # Add 2 hours to UTC time
        local_dt = dt + timedelta(hours=2)
        return local_dt.strftime('%Y-%m-%d %H:%M')
    return ''

def format_file_size(bytes_size):
    """Format file size in human readable format"""
    if bytes_size < 1024:
        return f"{bytes_size} B"
    elif bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.2f} KB"
    elif bytes_size < 1024 * 1024 * 1024:
        return f"{bytes_size / (1024 * 1024):.2f} MB"
    else:
        return f"{bytes_size / (1024 * 1024 * 1024):.2f} GB"

templates.env.filters['format_datetime_local'] = format_datetime_local
templates.env.filters['format_file_size'] = format_file_size

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def verify_upload_password(password: str) -> bool:
    """Verify upload password"""
    return password == UPLOAD_PASSWORD


def verify_private_password(password: str) -> bool:
    """Verify private view password"""
    return password == PRIVATE_VIEW_PASSWORD


def verify_delete_password(password: str) -> bool:
    """Verify delete password"""
    return password == DELETE_PASSWORD


def safe_filename_header(filename: str) -> str:
    """Create safe Content-Disposition header with filename"""
    # URL encode the filename for UTF-8 support
    encoded_filename = quote(filename)
    # Try ASCII filename first, fallback to UTF-8
    try:
        ascii_filename = filename.encode('ascii').decode('ascii')
        return f'inline; filename="{ascii_filename}"'
    except (UnicodeEncodeError, UnicodeDecodeError):
        # Use RFC 5987 for UTF-8 filenames
        return f"inline; filename*=UTF-8''{encoded_filename}"


# ============================================================================
# ROUTES
# ============================================================================

@app.get("/", response_class=HTMLResponse)
@limiter.limit(RATE_LIMIT_PAGES)
async def home(request: Request):
    """Home page with upload form"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/upload")
@limiter.limit(RATE_LIMIT_UPLOAD)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    password: str = Form(...),
    is_public: bool = Form(...),
    db: Session = Depends(get_db),
):
    """Upload file endpoint"""
    try:
        # Verify password
        if not verify_upload_password(password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid upload password"
            )

        # Check file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE / (1024*1024):.0f}MB"
            )

        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot upload empty file"
            )

        # Generate unique filename
        file_id = secrets.token_urlsafe(16)
        file_extension = Path(file.filename).suffix
        stored_filename = f"{file_id}{file_extension}"
        file_path = UPLOAD_DIR / stored_filename

        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Save to database
        db_file = crud.create_file(
            db=db,
            file_id=file_id,
            original_filename=file.filename,
            stored_filename=stored_filename,
            file_size=file_size,
            is_public=is_public,
        )

        return {
            "message": "File uploaded successfully",
            "file_id": file_id,
            "filename": file.filename,
            "is_public": is_public,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@app.delete("/delete/{file_id}")
@limiter.limit(RATE_LIMIT_DELETE)
async def delete_file(
    request: Request,
    file_id: str,
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Delete file endpoint"""
    try:
        # Verify password
        if not verify_delete_password(password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid delete password"
            )

        # Get file from database
        db_file = crud.get_file(db, file_id)
        if not db_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )

        # Delete physical file
        file_path = UPLOAD_DIR / db_file.stored_filename
        if file_path.exists():
            file_path.unlink()

        # Delete from database
        crud.delete_file(db, file_id)

        return {"message": "File deleted successfully", "filename": db_file.original_filename}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Delete failed: {str(e)}"
        )


@app.get("/public", response_class=HTMLResponse)
@limiter.limit(RATE_LIMIT_PAGES)
async def public_files(request: Request, db: Session = Depends(get_db)):
    """View public files"""
    files = crud.get_public_files(db)
    return templates.TemplateResponse(
        "files.html",
        {"request": request, "files": files, "is_public": True}
    )


@app.get("/private", response_class=HTMLResponse)
@limiter.limit(RATE_LIMIT_PAGES)
async def private_files_auth(request: Request):
    """Private files password page"""
    return templates.TemplateResponse("private_auth.html", {"request": request})


@app.post("/private", response_class=HTMLResponse)
@limiter.limit(RATE_LIMIT_PAGES)
async def private_files(
    request: Request,
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """View private files with password"""
    if not verify_private_password(password):
        return templates.TemplateResponse(
            "private_auth.html",
            {"request": request, "error": "Napačno geslo"}
        )
    
    files = crud.get_private_files(db)
    return templates.TemplateResponse(
        "files.html",
        {"request": request, "files": files, "is_public": False, "private_password": password}
    )


@app.get("/download/{file_id}")
@limiter.limit(RATE_LIMIT_DOWNLOAD)
async def download_file(request: Request, file_id: str, db: Session = Depends(get_db)):
    """Download file"""
    db_file = crud.get_file(db, file_id)
    if not db_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    file_path = UPLOAD_DIR / db_file.stored_filename
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk"
        )

    # Create safe Content-Disposition header
    encoded_filename = quote(db_file.original_filename)
    
    return FileResponse(
        path=file_path,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
    )


@app.get("/preview/{file_id}")
@limiter.limit(RATE_LIMIT_PREVIEW)
async def preview_file(request: Request, file_id: str, db: Session = Depends(get_db)):
    """Preview file in browser"""
    db_file = crud.get_file(db, file_id)
    if not db_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    file_path = UPLOAD_DIR / db_file.stored_filename
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk"
        )

    # Get file extension
    file_extension = Path(db_file.original_filename).suffix.lower()

    # Determine mime type
    mime_type, _ = mimetypes.guess_type(db_file.original_filename)
    
    # Handle text files - display as plain text
    if file_extension in TEXT_EXTENSIONS:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return PlainTextResponse(content=content)
        except UnicodeDecodeError:
            # If can't decode as UTF-8, try as binary
            with open(file_path, 'rb') as f:
                content = f.read()
            return PlainTextResponse(content=content.decode('latin-1'))
    
    # For images, videos, PDFs - return with inline disposition
    if mime_type:
        content_disposition = safe_filename_header(db_file.original_filename)
        return FileResponse(
            path=file_path,
            media_type=mime_type,
            headers={"Content-Disposition": content_disposition}
        )
    
    # Default: show as text if possible, otherwise download
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return PlainTextResponse(content=content)
    except:
        encoded_filename = quote(db_file.original_filename)
        return FileResponse(
            path=file_path,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
        )


@app.get("/health")
@limiter.limit(RATE_LIMIT_PAGES)
async def health_check(request: Request):
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


# ============================================================================
# FOLDER MANAGEMENT ENDPOINTS
# ============================================================================

@app.get("/api/folders")
@limiter.limit(RATE_LIMIT_PAGES)
async def get_folders_api(
    request: Request,
    is_public: bool,
    password: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all folders for public or private section"""
    # Verify access for private folders
    if not is_public:
        if not password or not verify_private_password(password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid password"
            )
    
    folders = crud.get_folders(db, is_public)
    return {
        "folders": [
            {
                "id": folder.id,
                "name": folder.name,
                "file_count": len(folder.files),
                "is_public": folder.is_public
            }
            for folder in folders
        ]
    }


@app.post("/api/folders")
@limiter.limit(RATE_LIMIT_UPLOAD)
async def create_folder_api(
    request: Request,
    name: str = Form(...),
    is_public: bool = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Create a new folder"""
    # Verify password
    if not verify_upload_password(password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )
    
    # Create folder
    folder = crud.create_folder(db, name, is_public)
    return {
        "message": "Folder created successfully",
        "folder": {
            "id": folder.id,
            "name": folder.name,
            "is_public": folder.is_public
        }
    }


@app.put("/api/folders/{folder_id}")
@limiter.limit(RATE_LIMIT_UPLOAD)
async def update_folder_api(
    request: Request,
    folder_id: int,
    name: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Update folder name"""
    # Verify password
    if not verify_upload_password(password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )
    
    folder = crud.update_folder(db, folder_id, name)
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found"
        )
    
    return {
        "message": "Folder updated successfully",
        "folder": {
            "id": folder.id,
            "name": folder.name
        }
    }


@app.delete("/api/folders/{folder_id}")
@limiter.limit(RATE_LIMIT_DELETE)
async def delete_folder_api(
    request: Request,
    folder_id: int,
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Delete folder"""
    # Verify password
    if not verify_delete_password(password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )
    
    success = crud.delete_folder(db, folder_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found"
        )
    
    return {"message": "Folder deleted successfully"}


@app.post("/api/folders/{folder_id}/files")
@limiter.limit(RATE_LIMIT_UPLOAD)
async def add_file_to_folder_api(
    request: Request,
    folder_id: int,
    file_id: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Add file to folder"""
    # Verify password
    if not verify_upload_password(password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )
    
    # Get file
    db_file = crud.get_file(db, file_id)
    if not db_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    success = crud.add_file_to_folder(db, folder_id, db_file.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to add file to folder"
        )
    
    return {"message": "File added to folder successfully"}


@app.delete("/api/folders/{folder_id}/files/{file_id}")
@limiter.limit(RATE_LIMIT_DELETE)
async def remove_file_from_folder_api(
    request: Request,
    folder_id: int,
    file_id: str,
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Remove file from folder"""
    # Verify password
    if not verify_delete_password(password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )
    
    # Get file
    db_file = crud.get_file(db, file_id)
    if not db_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    success = crud.remove_file_from_folder(db, folder_id, db_file.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to remove file from folder"
        )
    
    return {"message": "File removed from folder successfully"}


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Custom 404 handler"""
    return templates.TemplateResponse(
        "error.html",
        {"request": request, "error": "Page not found", "status_code": 404},
        status_code=404
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    """Custom 500 handler"""
    return templates.TemplateResponse(
        "error.html",
        {"request": request, "error": "Internal server error", "status_code": 500},
        status_code=500
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)