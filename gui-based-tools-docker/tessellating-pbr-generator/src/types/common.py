"""Common type definitions for the PBR texture generator."""

from enum import Enum
from typing import NamedTuple


class TextureType(Enum):
    """Available texture types for PBR materials."""
    DIFFUSE = "diffuse"
    NORMAL = "normal"
    ROUGHNESS = "roughness"
    METALLIC = "metallic"
    AMBIENT_OCCLUSION = "ao"
    HEIGHT = "height"
    EMISSIVE = "emissive"


class TextureFormat(Enum):
    """Supported texture file formats."""
    PNG = "png"
    JPG = "jpg"
    TIFF = "tiff"
    EXR = "exr"


class Resolution(NamedTuple):
    """Texture resolution definition."""
    width: int
    height: int
    
    def __str__(self) -> str:
        return f"{self.width}x{self.height}"
    
    @classmethod
    def from_string(cls, resolution_str: str) -> "Resolution":
        """Create Resolution from string like '2048x2048'."""
        width, height = map(int, resolution_str.split('x'))
        return cls(width=width, height=height)