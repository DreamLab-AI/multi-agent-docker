"""Configuration type definitions."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from .common import TextureType, TextureFormat, Resolution


@dataclass
class RoughnessConfig:
    """Advanced roughness generation configuration."""
    base_value: float = 0.5
    variation: float = 0.15
    invert: bool = False
    directional: bool = False
    direction_angle: float = 0.0
    # Legacy support
    roughness_range: Optional[tuple[float, float]] = None

    def __post_init__(self):
        # Convert legacy roughness_range to base_value if provided
        if self.roughness_range is not None:
            min_val, max_val = self.roughness_range
            self.base_value = (min_val + max_val) / 2
            self.variation = (max_val - min_val) / 2


@dataclass
class NormalConfig:
    """Advanced normal map generation configuration."""
    strength: float = 1.0
    blur_radius: float = 0
    invert_height: bool = False


@dataclass
class MetallicConfig:
    """Advanced metallic map generation configuration."""
    base_value: float = 0.0
    variation: float = 0.0
    patterns: Optional[Dict[str, Any]] = None


@dataclass
class HeightConfig:
    """Advanced height map generation configuration."""
    depth_scale: float = 0.1
    blur_radius: float = 0


@dataclass
class AOConfig:
    """Advanced ambient occlusion generation configuration."""
    radius: float = 5.0
    intensity: float = 1.0


@dataclass
class GenerationConfig:
    """Texture generation settings."""
    diffuse: Dict[str, Any] = field(default_factory=dict)
    normal: NormalConfig = field(default_factory=NormalConfig)
    roughness: RoughnessConfig = field(default_factory=RoughnessConfig)
    metallic: MetallicConfig = field(default_factory=MetallicConfig)
    height: HeightConfig = field(default_factory=HeightConfig)
    ao: AOConfig = field(default_factory=AOConfig)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GenerationConfig":
        """Create GenerationConfig from dictionary."""
        # Extract diffuse settings
        diffuse = data.get("diffuse", {})
        
        # Parse normal config
        normal_data = data.get("normal", {})
        normal = NormalConfig(
            strength=normal_data.get("strength", 1.0),
            blur_radius=normal_data.get("blur_radius", 0),
            invert_height=normal_data.get("invert_height", False)
        )
        
        # Parse roughness config
        roughness_data = data.get("roughness", {})
        roughness = RoughnessConfig(
            base_value=roughness_data.get("base_value", 0.5),
            variation=roughness_data.get("variation", 0.15),
            invert=roughness_data.get("invert", False),
            directional=roughness_data.get("directional", False),
            direction_angle=roughness_data.get("direction_angle", 0.0)
        )
        
        # Parse metallic config
        metallic_data = data.get("metallic", {})
        metallic = MetallicConfig(
            base_value=metallic_data.get("base_value", 0.0),
            variation=metallic_data.get("variation", 0.0),
            patterns=metallic_data.get("patterns")
        )
        
        # Parse height config
        height_data = data.get("height", {})
        height = HeightConfig(
            depth_scale=height_data.get("depth_scale", 0.1),
            blur_radius=height_data.get("blur_radius", 0)
        )
        
        # Parse AO config
        ao_data = data.get("ao", {})
        ao = AOConfig(
            radius=ao_data.get("radius", 5.0),
            intensity=ao_data.get("intensity", 1.0)
        )
        
        return cls(
            diffuse=diffuse,
            normal=normal,
            roughness=roughness,
            metallic=metallic,
            height=height,
            ao=ao
        )


@dataclass
class MaterialProperties:
    """Material-specific properties for texture generation."""
    # Legacy properties for backward compatibility
    roughness_range: Optional[tuple[float, float]] = None
    metallic_value: Optional[float] = None
    normal_strength: Optional[float] = None
    ao_intensity: Optional[float] = None
    additional_properties: Dict[str, Any] = field(default_factory=dict)
    
    # Advanced generation settings
    generation: Optional[GenerationConfig] = None


@dataclass
class TextureConfig:
    """Configuration for texture generation."""
    resolution: Resolution
    format: TextureFormat
    types: List[TextureType]
    seamless: bool = True
    bit_depth: int = 8

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TextureConfig":
        """Create TextureConfig from dictionary."""
        resolution = Resolution(
            width=data["resolution"]["width"],
            height=data["resolution"]["height"]
        )
        format_enum = TextureFormat(data["format"])
        types = [TextureType(t) for t in data["types"]]

        return cls(
            resolution=resolution,
            format=format_enum,
            types=types,
            seamless=data.get("seamless", True),
            bit_depth=data.get("bit_depth", 8)
        )


@dataclass
class Config:
    """Main configuration class."""
    project_name: str
    project_version: str
    texture_config: TextureConfig
    material: str
    style: str
    material_properties: MaterialProperties
    model: str
    output_directory: str
    naming_convention: str
    create_preview: bool = True
    api_key: Optional[str] = None
    org_id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """Create Config from dictionary."""
        texture_config = TextureConfig.from_dict(data["textures"])

        # Check if we have advanced generation config
        generation_config = None
        has_advanced_config = False
        
        if "generation" in data:
            gen_data = data["generation"]
            # Check if it has advanced texture configs (not just model)
            if any(key in gen_data for key in ["diffuse", "normal", "roughness", "metallic", "height", "ao"]):
                generation_config = GenerationConfig.from_dict(gen_data)
                has_advanced_config = True
        
        # Parse material properties with backward compatibility
        material_data = data.get("material", {})
        properties_data = material_data.get("properties", {})
        
        # Create MaterialProperties with both legacy and new config
        material_props = MaterialProperties(
            # Only set legacy properties if no advanced config
            roughness_range=tuple(properties_data.get("roughness_range", [0.0, 1.0])) if not has_advanced_config else None,
            metallic_value=properties_data.get("metallic_value", 0.0) if not has_advanced_config else None,
            normal_strength=properties_data.get("normal_strength", 1.0) if not has_advanced_config else None,
            ao_intensity=properties_data.get("ao_intensity", 1.0) if not has_advanced_config else None,
            additional_properties=properties_data,
            generation=generation_config
        )

        # Handle different config formats
        if "project" in data:
            # Standard format
            project_name = data["project"]["name"]
            project_version = data["project"]["version"]
            model = data["generation"]["model"]
            output_dir = data["output"]["directory"]
            naming_convention = data["output"]["naming_convention"]
            create_preview = data["output"].get("create_preview", True)
            api_key = data.get("api", {}).get("openai_key")
            org_id = data.get("api", {}).get("openai_org_id")
        else:
            # Example format (stone_wall.json, etc.)
            project_name = material_data.get("base_material", "unknown")
            project_version = "1.0.0"
            model = data.get("api", {}).get("model", "dall-e-3")
            output_dir = data.get("output", {}).get("directory", "output")
            naming_convention = data.get("output", {}).get("prefix", project_name)
            create_preview = data.get("output", {}).get("create_preview", True)
            # Support both api_key formats
            api_key = data.get("api", {}).get("api_key") or data.get("api", {}).get("openai_key")
            org_id = data.get("api", {}).get("org_id") or data.get("api", {}).get("openai_org_id")

        return cls(
            project_name=project_name,
            project_version=project_version,
            texture_config=texture_config,
            material=material_data.get("base_material", "generic"),
            style=material_data.get("style", "realistic"),
            material_properties=material_props,
            model=model,
            output_directory=output_dir,
            naming_convention=naming_convention,
            create_preview=create_preview,
            api_key=api_key,
            org_id=org_id
        )