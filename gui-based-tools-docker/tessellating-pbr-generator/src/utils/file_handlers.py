"""File handling utilities."""

from pathlib import Path
from typing import Optional
from PIL import Image
import io


def save_texture(image_data: bytes, file_path: str) -> bool:
    """Save texture to file."""
    try:
        image = Image.open(io.BytesIO(image_data))
        path = Path(file_path)
        ensure_directory(path.parent)
        image.save(path)
        return True
    except Exception as e:
        print(f"Error saving image to {file_path}: {e}")
        return False


def load_texture(file_path: Path):
    """Load texture from file."""
    # TODO: Implement
    return None


def ensure_directory(directory: Path) -> Path:
    """Ensure directory exists."""
    directory.mkdir(parents=True, exist_ok=True)
    return directory