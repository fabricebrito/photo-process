import click
from pathlib import Path
import shutil
from loguru import logger

from photo_process.factories import RawPhotoCollectionFactory


@click.command()
@click.argument("source", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.argument("target", type=click.Path(file_okay=False, path_type=Path))
@click.option("--dry-run", is_flag=True, help="Show operations without copying files.")
def organize(source: Path, target: Path, dry_run: bool):
    """
    Organize RAW photos from SOURCE into a date-based structure under TARGET.
    """

    logger.info(f"Scanning source folder: {source}")

    collection = RawPhotoCollectionFactory.from_folder(source)
    logger.info(f"Found {len(collection)} images")

    for photo in collection:
        logger.info(
            f"Processing: RAW={photo.source_path.name} "
            f"JPEG={'YES' if photo.has_jpeg else 'NO'}"
        )

        # Compute RAW target path
        dest_dir = target / photo.target_folder
        dest_file = dest_dir / photo.filename

        logger.debug(f"RAW → {dest_file}")

        if not dry_run:
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy(photo.source_path, dest_file)

        # If JPEG exists, copy that too
        if photo.has_jpeg:
            jpeg_dest = dest_dir / photo.jpeg_filename
            logger.debug(f"JPEG → {jpeg_dest}")

            if not dry_run:
                shutil.copy(photo.jpeg_path, jpeg_dest)

        # Save embedded thumbnail
        if photo.thumbnail_data:
            logger.debug(
                f"Thumbnail → {photo.target_folder / photo.thumbnail_filename}"
            )

            if not dry_run:
                photo.save_thumbnail()

    logger.info("Done.")


def main():
    organize()
