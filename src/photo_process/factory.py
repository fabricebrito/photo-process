from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import exifread
from photo_process.models import RawPhoto
from loguru import logger
import hashlib



class RawPhotoFactory:
    DATETIME_FORMATS = (
        "%Y:%m:%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
    )

    @staticmethod
    def _thumbnail_signature(tags, length=12):
        thumb = tags.get("JPEGThumbnail")
        if not thumb:
            return None  # or raise
        data = thumb
        # if exifread returns the thumbnail object, get raw bytes:
        if hasattr(data, "values"):
            data = data.values
        return hashlib.sha1(data).hexdigest()[:length].upper()

    @staticmethod
    def _extract_exif(path: Path) -> Dict[str, Any]:
        """Extract EXIF tags using exifread."""
        with open(path, "rb") as f:
            tags = exifread.process_file(f, details=False)  # `details=False` → faster
        return tags

    @staticmethod
    def _parse_datetime(dt_raw: str) -> datetime:
        """Try multiple possible EXIF datetime formats."""
        for fmt in RawPhotoFactory.DATETIME_FORMATS:
            try:
                return datetime.strptime(dt_raw, fmt)
            except ValueError:
                pass
        raise ValueError(f"Unable to parse EXIF DateTimeOriginal: {dt_raw}")

    @classmethod
    def from_file(cls, filepath: str | Path) -> RawPhoto:
        """Build a RawPhoto from the EXIF tags of a file."""
        path = Path(filepath)
        exif = cls._extract_exif(path)

        # exifread uses keys like "Image Model", "EXIF DateTimeOriginal"
        camera_model_tag = exif.get("Image Model")
        dt_original_tag = exif.get("EXIF DateTimeOriginal")
        logger.debug(f"EXIF tags extracted: {list(exif.keys())}")
        logger.debug(f"Camera model tag: {exif.get('Image Model')}")
        camera_id = exif.get("EXIF BodySerialNumber")
        thumb_sig = cls._thumbnail_signature(exif)

        if camera_model_tag is None:
            raise ValueError("EXIF field 'Image Model' not found")

        if dt_original_tag is None:
            raise ValueError("EXIF field 'EXIF DateTimeOriginal' not found")

        # Convert EXIF tag values to strings
        camera_model = str(camera_model_tag)
        dt_original = str(dt_original_tag)

        shooting_dt = cls._parse_datetime(dt_original)

        extension = path.suffix.lstrip(".").lower()

        return RawPhoto(
            camera_model=camera_model,
            shooting_datetime=shooting_dt,
            extension=extension,
            camera_id=str(camera_id) if camera_id else "unknown",
            thumbnail_signature=thumb_sig if thumb_sig else "none",
            exif={k: str(v) for k, v in exif.items()},
            source_path=path,
        )
