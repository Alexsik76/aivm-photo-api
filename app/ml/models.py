from pathlib import Path
from ultralytics import YOLO

def load_models():
    """Load YOLO models from the models directory."""
    display_model_path = Path("models/display.pt")
    digit_model_path = Path("models/digits.pt")
    
    # In a real environment, these files must exist.
    # For initial setup/testing, we might want to handle their absence gracefully 
    # or just let it fail if they are mandatory.
    if not display_model_path.exists() or not digit_model_path.exists():
        # During development/CI we might not have models. 
        # But the prompt says they are committed to git.
        # If they are not there yet, we might want to log a warning or use mocks.
        # For now, let's assume they should be there or we provide a way to mock.
        pass

    display_model = YOLO(str(display_model_path)) if display_model_path.exists() else None
    digit_model = YOLO(str(digit_model_path)) if digit_model_path.exists() else None
    
    return display_model, digit_model
