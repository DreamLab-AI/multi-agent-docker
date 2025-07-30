"""Validation utilities."""

from typing import Dict, Any


def validate_config(config: Dict[str, Any]) -> bool:
    """Validate configuration dictionary."""
    return True


def validate_texture_type(texture_type: str) -> bool:
    """Validate texture type string."""
    valid_types = {"diffuse", "normal", "roughness", "metallic", "ao", "height", "emissive"}
    return texture_type in valid_types