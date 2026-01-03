import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import exifread
from photo_process.models import RawPhoto, RawPhotoCollection
from loguru import logger
import hashlib
import exiftool

def hash_raw_chunk(path: Path, n=256*1024, length=12) -> str:
    with open(path, "rb") as f:
        chunk = f.read(n)
    return hashlib.sha1(chunk).hexdigest()[:length].upper()

class RawPhotoFactory:
    DATETIME_FORMATS = (
        "%Y:%m:%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
    )

    @staticmethod
    def _thumbnail_signature(tags, length=12):
        thumb = tags.get("EXIF:JPEGThumbnail")
        if not thumb:
            return None  # or raise
        data = thumb
        # if exifread returns the thumbnail object, get raw bytes:
        if hasattr(data, "values"):
            data = data.values
        return hashlib.sha1(data).hexdigest()[:length].upper()

    @staticmethod
    def _extract_exif(path: Path) -> dict:
        with exiftool.ExifToolHelper() as et:
            data = et.get_metadata(str(path))
        return data[0]

    @staticmethod
    def _parse_datetime(dt_raw: str) -> datetime:
        """Try multiple possible EXIF datetime formats."""
        for fmt in RawPhotoFactory.DATETIME_FORMATS:
            try:
                return datetime.strptime(dt_raw, fmt)
            except ValueError:
                pass
        raise ValueError(f"Unable to parse EXIF DateTimeOriginal: {dt_raw}")

    @staticmethod
    def _extract_thumbnail(path: Path) -> bytes | None:
        
        return None

    @classmethod
    def from_file(cls, filepath: str | Path) -> RawPhoto:
        """Build a RawPhoto from the EXIF tags of a file."""
        path = Path(filepath)
        exif = cls._extract_exif(path)

        # exifread uses keys like "Image Model", "EXIF DateTimeOriginal"
        camera_model_tag = exif.get("EXIF:Model")
        
        logger.debug(f"Camera model tag: {camera_model_tag}")
        # need to check if "Date/Time Original" is used instead
        dt_original_tag = exif.get("EXIF:DateTimeOriginal")
        
        logger.debug(f"Camera model tag: {exif.get('EXIF:Model')}")
        camera_id = exif.get("EXIF:SerialNumber")
        hash_chunk = hash_raw_chunk(path)

        if camera_model_tag is None:
            raise ValueError("EXIF field 'EXIF:Model' not found")

        if dt_original_tag is None:
            raise ValueError("EXIF field 'EXIF:DateTimeOriginal' not found")

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
            hash_chunk=hash_chunk if hash_chunk else "none",
            exif={k: str(v) for k, v in exif.items()},
            source_path=path,

        )


class RawPhotoCollectionFactory:
    @classmethod
    def from_files(cls, filepaths: list[str | Path]) -> RawPhotoCollection:
        photos = []
        for filepath in filepaths:
            try:
                photo = RawPhotoFactory.from_file(filepath)
                photos.append(photo)
            except Exception as e:
                logger.error(f"Error processing file {filepath}: {e}")
        return RawPhotoCollection(photos=photos)

    @classmethod
    def from_folder(
        cls,
        folderpath: str | Path,
        extensions: set[str] = None,
        recursive: bool = True
    ) -> RawPhotoCollection:

        folder = Path(folderpath)
        if extensions is None:
            extensions = {"cr2", "cr3", "nef", "arw", "orf", "rw2", "raf", "tiff"}

        if recursive:
            iterator = folder.rglob("*")
        else:
            iterator = folder.glob("*")  # non-recursive

        filepaths = [
            p for p in iterator
            if p.is_file() and p.suffix.lstrip(".").lower() in extensions
        ]

        logger.info(f"Found {len(filepaths)} RAW files in {folderpath}")
        return cls.from_files(filepaths)
