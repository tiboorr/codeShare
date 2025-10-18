from sqlalchemy.orm import Session
from sqlalchemy import desc
import models


def create_file(
    db: Session,
    file_id: str,
    original_filename: str,
    stored_filename: str,
    file_size: int,
    is_public: bool,
):
    """Create file record in database"""
    db_file = models.FileUpload(
        file_id=file_id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_size=file_size,
        is_public=is_public,
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file


def get_file(db: Session, file_id: str):
    """Get file by ID"""
    return db.query(models.FileUpload).filter(models.FileUpload.file_id == file_id).first()


def get_public_files(db: Session):
    """Get all public files"""
    return (
        db.query(models.FileUpload)
        .filter(models.FileUpload.is_public == True)
        .order_by(desc(models.FileUpload.upload_date))
        .all()
    )


def get_private_files(db: Session):
    """Get all private files"""
    return (
        db.query(models.FileUpload)
        .filter(models.FileUpload.is_public == False)
        .order_by(desc(models.FileUpload.upload_date))
        .all()
    )


def delete_file(db: Session, file_id: str):
    """Delete file from database"""
    db_file = db.query(models.FileUpload).filter(models.FileUpload.file_id == file_id).first()
    if db_file:
        db.delete(db_file)
        db.commit()
        return True
    return False