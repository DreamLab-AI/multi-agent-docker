"""Configuration loader with JSON validation for the PBR texture generator."""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from jsonschema import validate, ValidationError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration schema for validation
CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "project": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "version": {"type": "string"},
                "description": {"type": "string"}
            },
            "required": ["name", "version"]
        },
        "textures": {
            "type": "object",
            "properties": {
                "resolution": {
                    "type": "object",
                    "properties": {
                        "width": {"type": "integer", "minimum": 128},
                        "height": {"type": "integer", "minimum": 128}
                    },
                    "required": ["width", "height"]
                },
                "format": {
                    "type": "string",
                    "enum": ["png", "jpg", "tiff", "exr"]
                },
                "types": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["diffuse", "normal", "roughness", "metallic", "ao", "height", "emissive"]
                    }
                }
            },
            "required": ["resolution", "format", "types"]
        },
        "material": {
            "type": "object",
            "properties": {
                "base_material": {"type": "string"},
                "style": {"type": "string"},
                "seamless": {"type": "boolean"},
                "properties": {
                    "type": "object",
                    "additionalProperties": True
                }
            },
            "required": ["base_material"]
        },
        "generation": {
            "type": "object",
            "properties": {
                "model": {"type": "string"},
                "temperature": {"type": "number", "minimum": 0, "maximum": 2},
                "max_tokens": {"type": "integer", "minimum": 1},
                "batch_size": {"type": "integer", "minimum": 1}
            }
        },
        "output": {
            "type": "object",
            "properties": {
                "directory": {"type": "string"},
                "naming_convention": {"type": "string"},
                "create_preview": {"type": "boolean"}
            },
            "required": ["directory"]
        }
    },
    "required": ["project", "textures", "material", "output"]
}


class ConfigLoader:
    """Loads and validates configuration from JSON files."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the configuration loader.

        Args:
            config_path: Path to the configuration file. If None, uses default.
        """
        self.config_path = config_path or self._get_default_config_path()
        self.config: Dict[str, Any] = {}
        self.api_key: Optional[str] = None
        self.org_id: Optional[str] = None

    def _get_default_config_path(self) -> str:
        """Get the default configuration file path."""
        # Get the project root directory
        project_root = Path(__file__).parent.parent
        config_path = project_root / "config" / "default.json"
        return str(config_path)

    def load(self) -> Dict[str, Any]:
        """Load and validate the configuration.

        Returns:
            The validated configuration dictionary.

        Raises:
            FileNotFoundError: If the configuration file doesn't exist.
            ValidationError: If the configuration is invalid.
        """
        # Load configuration file
        with open(self.config_path, 'r') as f:
            self.config = json.load(f)

        # Validate against schema
        try:
            validate(instance=self.config, schema=CONFIG_SCHEMA)
        except ValidationError as e:
            raise ValidationError(f"Invalid configuration: {e.message}")

        # Load API key from environment
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")

        self.org_id = os.getenv("OPENAI_ORG_ID")

        # Add API key and org ID to config
        if "api" not in self.config:
            self.config["api"] = {}
        self.config["api"]["openai_key"] = self.api_key
        if self.org_id:
            self.config["api"]["openai_org_id"] = self.org_id

        return self.config

    def save(self, config: Dict[str, Any], path: Optional[str] = None) -> None:
        """Save configuration to a JSON file.

        Args:
            config: Configuration dictionary to save.
            path: Path to save the configuration. If None, uses current path.
        """
        save_path = path or self.config_path

        # Validate before saving
        try:
            validate(instance=config, schema=CONFIG_SCHEMA)
        except ValidationError as e:
            raise ValidationError(f"Invalid configuration: {e.message}")

        # Don't save API key to file
        config_to_save = config.copy()
        if "api" in config_to_save and "openai_key" in config_to_save["api"]:
            del config_to_save["api"]["openai_key"]

        # Save to file
        with open(save_path, 'w') as f:
            json.dump(config_to_save, f, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key.

        Args:
            key: Dot-separated key path (e.g., "textures.resolution.width").
            default: Default value if key not found.

        Returns:
            The configuration value or default.
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value by key.

        Args:
            key: Dot-separated key path (e.g., "textures.resolution.width").
            value: Value to set.
        """
        keys = key.split('.')
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from JSON file.

    Args:
        config_path: Path to configuration file. If None, uses default.

    Returns:
        Validated configuration dictionary.
    """
    loader = ConfigLoader(config_path)
    return loader.load()