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


def get_file_by_db_id(db: Session, db_id: int):
    """Get file by database ID"""
    return db.query(models.FileUpload).filter(models.FileUpload.id == db_id).first()


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


# ============================================================================
# FOLDER CRUD OPERATIONS
# ============================================================================

def create_folder(db: Session, name: str, is_public: bool):
    """Create a new folder"""
    db_folder = models.Folder(
        name=name,
        is_public=is_public,
    )
    db.add(db_folder)
    db.commit()
    db.refresh(db_folder)
    return db_folder


def get_folder(db: Session, folder_id: int):
    """Get folder by ID"""
    return db.query(models.Folder).filter(models.Folder.id == folder_id).first()


def get_folders(db: Session, is_public: bool):
    """Get all folders for public or private section"""
    return (
        db.query(models.Folder)
        .filter(models.Folder.is_public == is_public)
        .order_by(models.Folder.name)
        .all()
    )


def update_folder(db: Session, folder_id: int, name: str):
    """Update folder name"""
    db_folder = db.query(models.Folder).filter(models.Folder.id == folder_id).first()
    if db_folder:
        db_folder.name = name
        db.commit()
        db.refresh(db_folder)
        return db_folder
    return None


def delete_folder(db: Session, folder_id: int):
    """Delete folder (files remain but lose association)"""
    db_folder = db.query(models.Folder).filter(models.Folder.id == folder_id).first()
    if db_folder:
        db.delete(db_folder)
        db.commit()
        return True
    return False


def add_file_to_folder(db: Session, folder_id: int, file_db_id: int):
    """Add file to folder"""
    db_folder = get_folder(db, folder_id)
    db_file = get_file_by_db_id(db, file_db_id)
    
    if db_folder and db_file:
        # Check if already associated
        if db_file not in db_folder.files:
            db_folder.files.append(db_file)
            db.commit()
            return True
    return False


def remove_file_from_folder(db: Session, folder_id: int, file_db_id: int):
    """Remove file from folder"""
    db_folder = get_folder(db, folder_id)
    db_file = get_file_by_db_id(db, file_db_id)
    
    if db_folder and db_file:
        if db_file in db_folder.files:
            db_folder.files.remove(db_file)
            db.commit()
            return True
    return False