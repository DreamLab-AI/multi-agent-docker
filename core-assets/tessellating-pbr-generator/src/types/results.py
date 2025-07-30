"""Result type definitions."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any
from .common import TextureType


@dataclass
class TextureResult:
    """Result of a single texture generation."""
    texture_type: TextureType
    file_path: Path
    success: bool
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class GenerationResult:
    """Complete generation result."""
    texture_type: TextureType
    file_path: Path
    generation_time: float
    success: bool = True
    error_message: Optional[str] = None