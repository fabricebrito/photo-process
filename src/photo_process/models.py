from datetime import datetime
from pydantic import BaseModel, Field
from typing import Dict, Any
from pathlib import Path

from enum import Enum

class CanonCamera(str, Enum):
    EOS_5D_MARK_IV = "Canon EOS 5D Mark IV"
    EOS_6D_MARK_II = "Canon EOS 6D Mark II"
    EOS_7D_MARK_II = "Canon EOS 7D Mark II"

    @property
    def prefix(self) -> str:
        mapping = {
            CanonCamera.EOS_5D_MARK_IV: "5D4",
            CanonCamera.EOS_6D_MARK_II: "6D2",
            CanonCamera.EOS_7D_MARK_II: "7D2",
        }
        return mapping[self]

class RawPhoto(BaseModel):
    camera_model: CanonCamera = Field(..., description="Exact EXIF camera model")
    camera_id: str = Field(..., description="Camera serial number")
    shooting_datetime: datetime = Field(..., description="EXIF DateTimeOriginal")
    extension: str = Field(..., description="File extension (e.g. cr2, cr3, jpg)")
    exif: Dict[str, Any] = Field(default_factory=dict, description="Raw EXIF tags")
    thumbnail_signature: str = Field(..., description="Short JPEG thumbnail hash")
    source_path: Path = Field(..., description="Original file path")

    @property
    def camera_prefix(self) -> str:
        return self.camera_model.prefix
        
    @property
    def photo_id(self) -> str:
        ts = self.shooting_datetime.strftime("%Y%m%dT%H%M%S")
        return f"{self.camera_prefix}_{ts}_{self.camera_id}_{self.thumbnail_signature}"
    
    @property
    def filename(self) -> str:
        return f"{self.photo_id}.{self.extension}"
    
    @property
    def target_folder(self) -> Path:
        """Return a folder path like YEAR/MONTH/DAY based on shooting date."""
        dt = self.shooting_datetime
        return Path(f"{dt.year}/{dt.month:02d}/{dt.day:02d}")