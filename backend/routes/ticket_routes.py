"""
Ticket Processing API Routes

This blueprint handles all routes related to ticket submission and processing.
It is responsible for input validation and invoking the appropriate service.
"""
from flask import Blueprint, request, jsonify
from services.ticket_processing_service import process_support_ticket
from utils.pii_detector import PIIDetector, PIIMasker
from utils.translation_service import translate_text

# Create a Blueprint
ticket_bp = Blueprint('ticket_bp', __name__, url_prefix='/api')

# Invalid ticket keywords - non-support issues
INVALID_KEYWORDS = [
    'lost my pen', 'stuck in traffic', 'weather', 'restaurant',
    'buy cheap', 'click here', 'amazing deals', 'test', 'spam'
]

def is_valid_support_ticket(text):
    """Check if ticket is a valid support ticket"""
    text_lower = text.lower().strip()

    # Too short
    if len(text_lower) < 10:
        return False, "Ticket is too short. Please provide details about your issue."

    # Check invalid keywords
    for keyword in INVALID_KEYWORDS:
        if keyword in text_lower:
            return False, "This doesn't appear to be a valid support ticket."

    return True, None

@ticket_bp.route('/ticket', methods=['POST'])
def handle_process_ticket():
    """
    API endpoint to process a new support ticket.
    It validates input, detects PII, and passes it to the ticket processing service.
    """
    data = request.get_json()
    # --- Input Validation ---
    if not data or not data.get('ticket_text') or not data['ticket_text'].strip():
        return jsonify({"error": "ticket_text is a required non-empty field"}), 400

    ticket_text = data['ticket_text']
    if len(ticket_text) > 2000:
        return jsonify({"error": "ticket_text exceeds maximum length of 2000 characters"}), 400

    # --- Check if valid support ticket ---
    is_valid, invalid_reason = is_valid_support_ticket(ticket_text)
    if not is_valid:
        return jsonify({"error": invalid_reason}), 400

    # --- PII Detection and Masking ---
    detected_pii = PIIDetector.find_pii(ticket_text)

    if detected_pii:
        # Mask PII before processing
        masked_ticket_text, _ = PIIMasker.mask_pii(ticket_text)

        # Return warning to user with detected PII types
        return jsonify({
            "warning": "Your ticket contains sensitive personal information",
            "detected_pii_types": list(detected_pii.keys()),
            "message": "For your security, personal information like emails, phone numbers, SSN, and credit cards should not be included in support tickets. Please review your submission and remove any sensitive data, then resubmit.",
            "examples": {
                "emails": detected_pii.get('emails', [])[:2],
                "phone_numbers": detected_pii.get('phone_numbers', [])[:2],
                "ssn": detected_pii.get('ssn', [])[:2],
                "credit_cards": detected_pii.get('credit_cards', [])[:2],
                "account_ids": detected_pii.get('account_ids', [])[:2],
            }
        }), 400

    result, error = process_support_ticket(ticket_text)

    if error:
        return jsonify(error), 502 # 502 Bad Gateway indicates an upstream API error

    return jsonify(result)


@ticket_bp.route('/translate', methods=['POST'])
def handle_translate():
    """
    API endpoint to translate guidance text to Indian languages.
    Supports: Hindi, Tamil, Telugu, Kannada, Malayalam, Gujarati, Marathi, Bengali, Punjabi

    Request body:
    {
        "text": "Text to translate",
        "target_language": "Hindi"  # Target Indian language
    }

    Returns:
        JSON with translated text
    """
    try:
        data = request.get_json()

        if not data or 'text' not in data:
            return jsonify({
                "error": "Missing text field",
                "error_code": "INVALID_REQUEST"
            }), 400

        text = data.get('text', '')
        target_language = data.get('target_language', 'English')

        if not text.strip():
            return jsonify({
                "error": "Text cannot be empty",
                "error_code": "EMPTY_TEXT"
            }), 400

        translated_text = translate_text(text, target_language)

        return jsonify({
            "original_text": text,
            "translated_text": translated_text,
            "target_language": target_language
        }), 200

    except Exception as e:
        return jsonify({
            "error": "Translation service error",
            "error_code": "TRANSLATION_ERROR",
            "message": str(e)
        }), 500