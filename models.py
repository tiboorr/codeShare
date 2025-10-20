from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


# Many-to-many relationship table between files and folders
file_folder_association = Table(
    'file_folder_association',
    Base.metadata,
    Column('file_id', Integer, ForeignKey('file_uploads.id'), primary_key=True),
    Column('folder_id', Integer, ForeignKey('folders.id'), primary_key=True)
)


class FileUpload(Base):
    """File upload model"""
    __tablename__ = "file_uploads"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String, unique=True, index=True, nullable=False)
    original_filename = Column(String, nullable=False)
    stored_filename = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    is_public = Column(Boolean, default=True, nullable=False)
    upload_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationship to folders
    folders = relationship("Folder", secondary=file_folder_association, back_populates="files")
    
    def __repr__(self):
        return f"<FileUpload {self.original_filename}>"


class Folder(Base):
    """Folder model for organizing files"""
    __tablename__ = "folders"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    is_public = Column(Boolean, default=True, nullable=False)
    created_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationship to files
    files = relationship("FileUpload", secondary=file_folder_association, back_populates="folders")
    
    def __repr__(self):
        return f"<Folder {self.name}>"