import sys
import traceback
from typing import Any, Callable, Dict, Optional, Type, TypeVar, cast

from .logger import logger

# Type variables for function signatures
T = TypeVar('T')
R = TypeVar('R')

class PipelineError(Exception):
    """Base class for all pipeline errors."""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        """
        Initialize a pipeline error.
        
        Args:
            message: Error message.
            original_error: The original exception that caused this error.
        """
        self.original_error = original_error
        self.message = message
        super().__init__(self.message)

class ConnectionError(PipelineError):
    """Error raised when connection to a data source fails."""
    pass

class ReadError(PipelineError):
    """Error raised when reading a file fails."""
    pass

class ProcessingError(PipelineError):
    """Error raised when processing data fails."""
    pass

class ValidationError(PipelineError):
    """Error raised when data validation fails."""
    pass

class TransformationError(PipelineError):
    """Error raised when data transformation fails."""
    pass

class LoadingError(PipelineError):
    """Error raised when loading data to a target fails."""
    pass

class ChunkingError(PipelineError):
    """Error raised when chunking data fails."""
    pass

class EmbeddingError(PipelineError):
    """Error raised when generating embeddings fails."""
    pass

def handle_error(
    error_type: Type[PipelineError],
    message: str,
    original_error: Optional[Exception] = None,
    log_traceback: bool = True,
    raise_error: bool = True
) -> None:
    """
    Handle an error in a standardized way.
    
    Args:
        error_type: The type of PipelineError to create.
        message: Error message.
        original_error: The original exception that caused this error.
        log_traceback: Whether to log the traceback.
        raise_error: Whether to raise the error after logging.
    
    Raises:
        PipelineError: The wrapped error if raise_error is True.
    """
    error = error_type(message, original_error)
    
    # Log the error
    if log_traceback and original_error:
        logger.error(
            f"{message} - Original error: {str(original_error)}\n"
            f"{''.join(traceback.format_exception(type(original_error), original_error, original_error.__traceback__))}"
        )
    else:
        logger.error(message)
    
    # Raise the error if requested
    if raise_error:
        raise error

def error_handler(
    error_type: Type[PipelineError],
    message: str,
    log_traceback: bool = True,
    raise_error: bool = True
) -> Callable[[Callable[..., R]], Callable[..., R]]:
    """
    Decorator to handle errors in pipeline functions.
    
    Args:
        error_type: The type of PipelineError to create.
        message: Error message template. Can include {args} and {kwargs} that will be replaced.
        log_traceback: Whether to log the traceback.
        raise_error: Whether to raise the error after logging.
    
    Returns:
        Decorated function that handles errors.
    """
    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        def wrapper(*args: Any, **kwargs: Any) -> R:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Format the message with args and kwargs if possible
                try:
                    formatted_message = message.format(args=args, kwargs=kwargs)
                except (KeyError, ValueError):
                    formatted_message = message
                
                # Include the function name in the message
                full_message = f"Error in {func.__name__}: {formatted_message}"
                
                handle_error(
                    error_type,
                    full_message,
                    original_error=e,
                    log_traceback=log_traceback,
                    raise_error=raise_error
                )
                
                # This will only be reached if raise_error is False
                return cast(R, None)
        
        return wrapper
    
    return decorator

def safe_execute(
    func: Callable[..., R],
    *args: Any,
    error_type: Type[PipelineError] = PipelineError,
    message: str = "Error executing function",
    log_traceback: bool = True,
    raise_error: bool = False,
    default_return: Optional[R] = None,
    **kwargs: Any
) -> Optional[R]:
    """
    Safely execute a function and handle any errors.
    
    Args:
        func: The function to execute.
        *args: Positional arguments to pass to the function.
        error_type: The type of PipelineError to create.
        message: Error message.
        log_traceback: Whether to log the traceback.
        raise_error: Whether to raise the error after logging.
        default_return: Default value to return if an error occurs and raise_error is False.
        **kwargs: Keyword arguments to pass to the function.
    
    Returns:
        The result of the function or default_return if an error occurs.
        
    Raises:
        PipelineError: If an error occurs and raise_error is True.
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        full_message = f"Error executing {func.__name__}: {message}"
        
        handle_error(
            error_type,
            full_message,
            original_error=e,
            log_traceback=log_traceback,
            raise_error=raise_error
        )
        
        return default_return