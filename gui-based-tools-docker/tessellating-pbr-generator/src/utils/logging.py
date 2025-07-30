"""Enhanced logging configuration with color coding and progress indicators."""

import logging
import sys
import time
from typing import Optional, Dict, Any
from datetime import datetime


# ANSI color codes for terminal output
class Colors:
    """ANSI color codes for terminal output."""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    # Colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color coding for different log levels."""
    
    COLORS = {
        'DEBUG': Colors.BRIGHT_BLACK,
        'INFO': Colors.BRIGHT_BLUE,
        'WARNING': Colors.BRIGHT_YELLOW,
        'ERROR': Colors.BRIGHT_RED,
        'CRITICAL': Colors.BRIGHT_RED + Colors.BOLD,
    }
    
    LEVEL_ICONS = {
        'DEBUG': '🔍',
        'INFO': 'ℹ️ ',
        'WARNING': '⚠️ ',
        'ERROR': '❌',
        'CRITICAL': '🚨',
    }
    
    def __init__(self, *args, use_colors: bool = True, verbose: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self.use_colors = use_colors and sys.stdout.isatty()
        self.verbose = verbose
        
    def format(self, record):
        # Add custom fields
        record.icon = self.LEVEL_ICONS.get(record.levelname, '')
        
        if self.use_colors:
            color = self.COLORS.get(record.levelname, '')
            record.levelname_color = f"{color}{record.levelname}{Colors.RESET}"
            record.msg_color = f"{color}{record.msg}{Colors.RESET}"
        else:
            record.levelname_color = record.levelname
            record.msg_color = record.msg
            
        # Format time in a more readable way
        if self.verbose:
            record.time_str = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        else:
            record.time_str = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
            
        return super().format(record)


class ProgressLogger:
    """Logger wrapper with progress tracking capabilities."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.start_times: Dict[str, float] = {}
        self.step_counts: Dict[str, int] = {}
        
    def start_progress(self, task_name: str, total_steps: Optional[int] = None):
        """Mark the start of a progress-tracked task."""
        self.start_times[task_name] = time.time()
        if total_steps:
            self.step_counts[task_name] = total_steps
        self.logger.info(f"{Colors.BRIGHT_GREEN}▶ Starting: {task_name}{Colors.RESET}")
        
    def update_progress(self, task_name: str, message: str, current_step: Optional[int] = None):
        """Update progress for a task."""
        elapsed = time.time() - self.start_times.get(task_name, time.time())
        elapsed_str = f"[{elapsed:.1f}s]"
        
        if current_step and task_name in self.step_counts:
            progress = f"({current_step}/{self.step_counts[task_name]})"
            self.logger.info(f"  {Colors.BRIGHT_CYAN}→ {message} {progress} {elapsed_str}{Colors.RESET}")
        else:
            self.logger.info(f"  {Colors.BRIGHT_CYAN}→ {message} {elapsed_str}{Colors.RESET}")
            
    def complete_progress(self, task_name: str, message: Optional[str] = None):
        """Mark a task as complete."""
        if task_name in self.start_times:
            elapsed = time.time() - self.start_times[task_name]
            complete_msg = message or f"Completed: {task_name}"
            self.logger.info(f"{Colors.BRIGHT_GREEN}✓ {complete_msg} [{elapsed:.1f}s]{Colors.RESET}")
            del self.start_times[task_name]
            if task_name in self.step_counts:
                del self.step_counts[task_name]
                
    def error_progress(self, task_name: str, error_message: str):
        """Mark a task as failed."""
        if task_name in self.start_times:
            elapsed = time.time() - self.start_times[task_name]
            self.logger.error(f"{Colors.BRIGHT_RED}✗ Failed: {task_name} - {error_message} [{elapsed:.1f}s]{Colors.RESET}")
            del self.start_times[task_name]
            if task_name in self.step_counts:
                del self.step_counts[task_name]


_loggers = {}
_progress_loggers = {}


def setup_logger(name: str = "pbr_generator", debug: bool = False, verbose: bool = False, no_color: bool = False) -> logging.Logger:
    """Setup and configure enhanced logger.
    
    Args:
        name: Logger name.
        debug: Enable debug logging.
        verbose: Enable verbose output with more details.
        no_color: Disable color output.
        
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Set level
    level = logging.DEBUG if debug else logging.INFO
    logger.setLevel(level)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Create formatter
    if verbose:
        format_str = '%(time_str)s | %(levelname_color)-8s | %(name)s | %(msg_color)s'
    else:
        format_str = '%(icon)s %(levelname_color)-8s | %(msg_color)s'
        
    formatter = ColoredFormatter(
        format_str,
        use_colors=not no_color,
        verbose=verbose
    )
    console_handler.setFormatter(formatter)
    
    # Add handler
    logger.addHandler(console_handler)
    
    # Store logger
    _loggers[name] = logger
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get logger instance.
    
    Args:
        name: Logger name. If None, returns root logger.
        
    Returns:
        Logger instance.
    """
    if name is None:
        name = "pbr_generator"
    
    if name not in _loggers:
        return setup_logger(name)
    
    return _loggers[name]


def get_progress_logger(name: Optional[str] = None) -> ProgressLogger:
    """Get progress logger instance.
    
    Args:
        name: Logger name. If None, returns root progress logger.
        
    Returns:
        ProgressLogger instance.
    """
    if name is None:
        name = "pbr_generator"
        
    if name not in _progress_loggers:
        base_logger = get_logger(name)
        _progress_loggers[name] = ProgressLogger(base_logger)
        
    return _progress_loggers[name]


def print_summary(results: list, total_time: float, warnings: list = None):
    """Print a formatted summary report.
    
    Args:
        results: List of generation results.
        total_time: Total generation time in seconds.
        warnings: List of warning messages.
    """
    logger = get_logger()
    
    # Print separator
    logger.info(f"\n{Colors.BRIGHT_WHITE}{'='*60}{Colors.RESET}")
    logger.info(f"{Colors.BRIGHT_WHITE}📊 GENERATION SUMMARY{Colors.RESET}")
    logger.info(f"{Colors.BRIGHT_WHITE}{'='*60}{Colors.RESET}")
    
    # Generation stats
    successful = sum(1 for r in results if r.success)
    failed = len(results) - successful
    
    logger.info(f"\n{Colors.BRIGHT_CYAN}⏱️  Total Time: {total_time:.2f} seconds{Colors.RESET}")
    logger.info(f"{Colors.BRIGHT_GREEN}✅ Successful: {successful} textures{Colors.RESET}")
    
    if failed > 0:
        logger.info(f"{Colors.BRIGHT_RED}❌ Failed: {failed} textures{Colors.RESET}")
    
    # Output locations
    logger.info(f"\n{Colors.BRIGHT_WHITE}📁 Generated Textures:{Colors.RESET}")
    for result in results:
        if result.success:
            icon = "✓"
            color = Colors.GREEN
            logger.info(f"  {color}{icon} {result.texture_type.value}: {result.file_path}{Colors.RESET}")
        else:
            icon = "✗"
            color = Colors.RED
            logger.info(f"  {color}{icon} {result.texture_type.value}: {result.error_message}{Colors.RESET}")
    
    # Warnings
    if warnings:
        logger.info(f"\n{Colors.BRIGHT_YELLOW}⚠️  Warnings:{Colors.RESET}")
        for warning in warnings:
            logger.info(f"  {Colors.YELLOW}• {warning}{Colors.RESET}")
    
    # Footer
    logger.info(f"\n{Colors.BRIGHT_WHITE}{'='*60}{Colors.RESET}\n")