"""Progress tracking utilities using tqdm for better user feedback."""

import time
from typing import Optional, Dict, Any, List
from tqdm import tqdm
from contextlib import contextmanager
from ..utils.logging import get_logger, Colors


class ProgressTracker:
    """Manages progress bars for texture generation tasks."""
    
    def __init__(self, total_textures: int, material_name: str):
        """Initialize progress tracker.
        
        Args:
            total_textures: Total number of textures to generate.
            material_name: Name of the material being generated.
        """
        self.logger = get_logger()
        self.total_textures = total_textures
        self.material_name = material_name
        self.warnings: List[str] = []
        self.start_time = time.time()
        
        # Main progress bar for overall generation
        self.main_pbar = tqdm(
            total=total_textures,
            desc=f"Generating {material_name} textures",
            unit="texture",
            bar_format="{l_bar}{bar:30}{r_bar}",
            colour="green"
        )
        
        # Sub progress bar for individual texture steps
        self.sub_pbar: Optional[tqdm] = None
        
    def start_texture(self, texture_type: str, steps: int = 3):
        """Start tracking a new texture generation.
        
        Args:
            texture_type: Type of texture being generated.
            steps: Number of steps for this texture.
        """
        # Close any existing sub progress bar
        if self.sub_pbar:
            self.sub_pbar.close()
            
        # Create new sub progress bar
        self.sub_pbar = tqdm(
            total=steps,
            desc=f"  → {texture_type}",
            unit="step",
            bar_format="{l_bar}{bar:20}{r_bar}",
            colour="cyan",
            leave=False
        )
        
    def update_step(self, step_name: str, status: str = "processing"):
        """Update the current step.
        
        Args:
            step_name: Name of the current step.
            status: Status of the step (processing, complete, failed).
        """
        if self.sub_pbar:
            # Update description with status indicator
            if status == "complete":
                icon = "✓"
                color = "green"
            elif status == "failed":
                icon = "✗"
                color = "red"
            else:
                icon = "⟳"
                color = "yellow"
                
            self.sub_pbar.set_description(f"  → {step_name} {icon}")
            
            if status in ["complete", "failed"]:
                self.sub_pbar.update(1)
                
    def complete_texture(self, texture_type: str, success: bool = True, error: Optional[str] = None):
        """Mark a texture as complete.
        
        Args:
            texture_type: Type of texture completed.
            success: Whether generation was successful.
            error: Error message if failed.
        """
        # Close sub progress bar
        if self.sub_pbar:
            self.sub_pbar.close()
            self.sub_pbar = None
            
        # Update main progress
        self.main_pbar.update(1)
        
        # Log result
        if success:
            self.logger.info(f"{Colors.GREEN}✓ {texture_type} generated successfully{Colors.RESET}")
        else:
            self.logger.error(f"{Colors.RED}✗ {texture_type} generation failed: {error}{Colors.RESET}")
            self.warnings.append(f"{texture_type} generation failed: {error}")
            
    def add_warning(self, warning: str):
        """Add a warning message.
        
        Args:
            warning: Warning message to add.
        """
        self.warnings.append(warning)
        self.logger.warning(warning)
        
    def close(self):
        """Close all progress bars and return summary data."""
        # Close any open progress bars
        if self.sub_pbar:
            self.sub_pbar.close()
        self.main_pbar.close()
        
        # Calculate total time
        total_time = time.time() - self.start_time
        
        return {
            'total_time': total_time,
            'warnings': self.warnings
        }


class StepProgressBar:
    """Context manager for step-based progress tracking."""
    
    def __init__(self, total_steps: int, description: str):
        """Initialize step progress bar.
        
        Args:
            total_steps: Total number of steps.
            description: Description for the progress bar.
        """
        self.pbar = tqdm(
            total=total_steps,
            desc=description,
            unit="step",
            bar_format="{l_bar}{bar:25}{r_bar}",
            colour="blue"
        )
        self.current_step = 0
        
    def update(self, step_description: str):
        """Update to next step.
        
        Args:
            step_description: Description of the current step.
        """
        self.current_step += 1
        self.pbar.set_description(f"{step_description} ({self.current_step}/{self.pbar.total})")
        self.pbar.update(1)
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.pbar.close()


@contextmanager
def api_progress(operation: str):
    """Context manager for API call progress indication.
    
    Args:
        operation: Description of the API operation.
        
    Yields:
        Progress bar instance.
    """
    pbar = tqdm(
        total=1,
        desc=f"API: {operation}",
        bar_format="{desc}: {elapsed}s",
        colour="magenta"
    )
    
    try:
        yield pbar
    finally:
        pbar.update(1)
        pbar.close()


def create_time_estimate(completed: int, total: int, elapsed_time: float) -> str:
    """Create time estimate string for remaining work.
    
    Args:
        completed: Number of completed items.
        total: Total number of items.
        elapsed_time: Time elapsed so far in seconds.
        
    Returns:
        Formatted time estimate string.
    """
    if completed == 0:
        return "Calculating..."
        
    avg_time_per_item = elapsed_time / completed
    remaining_items = total - completed
    estimated_remaining = avg_time_per_item * remaining_items
    
    # Format time
    if estimated_remaining < 60:
        return f"{estimated_remaining:.0f}s remaining"
    elif estimated_remaining < 3600:
        minutes = estimated_remaining / 60
        return f"{minutes:.1f}m remaining"
    else:
        hours = estimated_remaining / 3600
        return f"{hours:.1f}h remaining"