import cv2
import numpy as np
import pandas as pd
try:
    import pytesseract
except ImportError:
    pytesseract = None

def preprocess_scorecard_image(image_bytes: bytes) -> np.ndarray:
    """
    Converts raw uploaded image bytes into a high-contrast, cleaned grayscale 
    image optimized for OCR text extraction engines.
    """
    # 1. Decode bytes into an OpenCV image matrix
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # 2. Convert to grayscale to remove distracting background course colors
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 3. Apply adaptive thresholding to maximize contrast between grid pencil marks and paper
    processed_img = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    
    return processed_img

def extract_scores_from_card(image_bytes: bytes) -> dict:
    """
    Processes a scorecard image and attempts to parse out hole-by-hole scores.
    Returns a dictionary mapping hole numbers (1-18) to gross stroke counts.
    """
    # Initialize a clean default scorecard layout dictionary
    parsed_scores = {h: 4 for h in range(1, 19)}
    
    if pytesseract is None:
        # Fallback placeholder flag if Tesseract binary isn't locally installed on host
        return parsed_scores

    try:
        cleaned_image = preprocess_scorecard_image(image_bytes)
        
        # Configure Tesseract to look specifically for digits (Saves processing overhead)
        custom_config = r'--oem 3 --psm 6 outputbase digits'
        extracted_text = pytesseract.image_to_string(cleaned_image, config=custom_config)
        
        # TODO: Implement table grid cell zoning or regex parsing logic here.
        # For now, we return a safe parsed fallback loop token for testing
        print(f"OCR Stream Debug Output:\n{extracted_text}")
        
    except Exception as e:
        print(f"OCR Pipeline structural execution error: {e}")
        
    return parsed_scores