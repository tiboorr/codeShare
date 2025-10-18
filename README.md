# codeShare

FastAPI fullstack file sharing application with public and private uploads.

## Features

- 🔐 Password-protected uploads
- 📁 Public and private file sharing
- 🖱️ Drag & drop file upload (up to 500MB)
- 👁️ File preview (images, videos, PDFs, text files)
- 📥 Direct file downloads
- 🛡️ Rate limiting and security features
- 📊 SQLite database for metadata
- 🎨 Clean, minimal UI

## Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create .env file:
```bash
cp .env.example .env
```

4. Edit .env file with your passwords:
```
UPLOAD_PASSWORD=your_upload_password
PRIVATE_VIEW_PASSWORD=your_private_view_password
SECRET_KEY=your_secret_key_here
MAX_FILE_SIZE=524288000
UPLOAD_DIR=uploads
DATABASE_URL=sqlite:///./codeshare.db
```

5. Run the application:
```bash
uvicorn main:app --reload
```

6. Open browser at `http://localhost:8000`

## Usage

### Uploading Files
- Enter upload password
- Select public or private upload
- Drag & drop or click to select file (max 500MB)
- Click upload

### Viewing Files
- **Public files**: Click "View Public Files" on homepage
- **Private files**: Enter private view password when prompted

### Preview & Download
- Click "Preview" to view file in new window
- Click "Download" to save file

## Security Features

- Password authentication for uploads and private files
- Rate limiting (10 uploads per hour per IP)
- File size validation
- SQL injection protection
- CSRF protection
- Secure file storage

## Technology Stack

- **Backend**: FastAPI
- **Database**: SQLite with SQLAlchemy
- **Templates**: Jinja2
- **Security**: passlib, slowapi
- **Frontend**: Minimal HTML/CSS/JavaScript

## License

MIT