from PIL import Image
import pytesseract
import cv2
import re
import os

# For Windows - install tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text_from_image(image_path):
    '''Extract text from uploaded ID card using OCR'''
    try:
        # Read image
        image = cv2.imread(image_path)
        if image is None:
            return 'Error: Could not read image'
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding for better OCR
        gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        
        # Extract text using Tesseract
        text = pytesseract.image_to_string(gray)
        return text
    except Exception as e:
        return f'OCR Error: {str(e)}'

def extract_id_details(text):
    '''Parse extracted text to find name, ID number, DOB'''
    details = {
        'name': None,
        'id_number': None,
        'dob': None,
    }
    
    # Pattern matching
    name_pattern = r'(?:Name|NAME)[:\s]+([A-Z][a-z]+(?:\s[A-Z][a-z]+)+)'
    id_pattern = r'(?:ID|License|Registration)[:\s]+([A-Z0-9]{6,15})'
    dob_pattern = r'(?:DOB|Date of Birth)[:\s]+(\d{2}[/-]\d{2}[/-]\d{4})'
    
    name_match = re.search(name_pattern, text, re.IGNORECASE)
    if name_match:
        details['name'] = name_match.group(1).strip()
    
    id_match = re.search(id_pattern, text, re.IGNORECASE)
    if id_match:
        details['id_number'] = id_match.group(1).strip()
    
    dob_match = re.search(dob_pattern, text, re.IGNORECASE)
    if dob_match:
        details['dob'] = dob_match.group(1).strip()
    
    return details

def verify_id_document(uploaded_file, save_path):
    '''Process uploaded ID card and extract information'''
    try:
        # Save file temporarily
        with open(save_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
        
        # Extract text
        extracted_text = extract_text_from_image(save_path)
        details = extract_id_details(extracted_text)
        
        return {
            'success': True,
            'extracted_text': extracted_text,
            'details': details
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
