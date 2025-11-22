import click
from pathlib import Path
from photo_process.factory import RawPhotoFactory


@click.group()
def cli():
    """CLI for reading and managing Canon RAW photos."""
    pass


@cli.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
def info(path):
    """
    Show EXIF-based info for a RAW photo.
    """
    try:
        photo = RawPhotoFactory.from_file(path)
    except Exception as e:
        click.echo(f"Error: {e}")
        raise click.Abort()

    click.echo(f"Camera:         {photo.camera_model.value}")
    click.echo(f"Prefix:         {photo.camera_prefix}")
    #click.echo(f"Camera ID:      {photo.camera_id}")
    click.echo(f"Shooting date:  {photo.shooting_datetime.isoformat()}")


def main():
    cli()
