"""
Barcode detection and extraction from images.
Uses OpenCV and pyzbar to detect and extract barcode data from images.
"""

import cv2
import numpy as np
from pyzbar import pyzbar
from typing import List, Optional
import logging
import base64

logger = logging.getLogger(__name__)


def detect_barcodes_with_preprocessing(image_data: str, image_format: str = 'jpeg') -> List[str]:
    """
    Detect barcodes in an image using preprocessing and pyzbar.
    
    Args:
        image_data: Base64 encoded image string
        image_format: Format of the image (jpeg, png, etc.)
        
    Returns:
        List of detected barcode numbers
    """
    try:
        # Decode base64 image
        image_bytes = base64.b64decode(image_data)
        
        # Convert to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        
        # Decode image using OpenCV
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            logger.error("Failed to decode image")
            return []
        
        # Try to detect barcodes from the original image
        barcodes = pyzbar.decode(img)
        
        if barcodes:
            detected = [barcode.data.decode('utf-8') for barcode in barcodes]
            logger.info(f"Detected barcodes: {detected}")
            return detected
        
        # If no barcodes found, apply preprocessing
        processed_images = preprocess_image(img)
        
        for processed_img in processed_images:
            barcodes = pyzbar.decode(processed_img)
            if barcodes:
                detected = [barcode.data.decode('utf-8') for barcode in barcodes]
                logger.info(f"Detected barcodes after preprocessing: {detected}")
                return detected
        
        logger.warning("No barcodes detected in image")
        return []
        
    except Exception as e:
        logger.error(f"Error detecting barcodes: {e}")
        return []


def preprocess_image(img: np.ndarray) -> List[np.ndarray]:
    """
    Apply various preprocessing techniques to improve barcode detection.
    """
    processed_images = []
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 1. Original grayscale
    processed_images.append(gray)
    
    # 2. Threshold binary
    _, thresh = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
    processed_images.append(thresh)
    
    # 3. Adaptive threshold
    adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                     cv2.THRESH_BINARY, 11, 2)
    processed_images.append(adaptive)
    
    return processed_images


def validate_barcode_format(barcode: str) -> bool:
    """
    Validate if the barcode is in a valid format.
    """
    # Barcodes should be numeric and between 8-14 digits
    if not barcode.isdigit():
        return False
    
    length = len(barcode)
    # Valid lengths for common barcodes: EAN-8, EAN-13, UPC-A, UPC-E
    valid_lengths = [8, 12, 13, 14]
    return length in valid_lengths
