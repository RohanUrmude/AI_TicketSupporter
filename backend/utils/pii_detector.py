"""
PII Detection and Masking Utility

This module provides utilities for detecting and masking personally identifiable
information (PII) in support tickets before they are sent to external LLM APIs.
"""
import re
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class PIIPatterns:
    """Regex patterns for detecting 20+ PII types"""

    # ============= FINANCIAL INFORMATION (5 types) =============
    # 1. Email addresses: user@domain.com
    EMAIL = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'

    # 2. Credit card: 16 digits with optional spaces/dashes
    CREDIT_CARD = r'\b(?:\d{4}[-\s]?){3}\d{4}\b'

    # 3. Credit card expiry: MM/YY or MM/YYYY
    CREDIT_CARD_EXPIRY = r'\b(?:0[1-9]|1[0-2])/(?:[0-9]{2}|[0-9]{4})\b'

    # 4. Credit card CVV: 3-4 digit security code
    CREDIT_CARD_CVV = r'\b(?:CVV|CVC|CCV)[\s:]*(?:\d{3,4})\b'

    # 5. Bank account number: 8-17 digits
    BANK_ACCOUNT = r'\b(?:account|acct)[\s:]*(?:\d{8,17})\b'

    # ============= IDENTIFICATION NUMBERS (5 types) =============
    # 6. Social Security Number: 123-45-6789 or 123456789
    SSN = r'\b(?:\d{3}-\d{2}-\d{4}|\d{9})\b'

    # 7. Driver's License: Various formats
    DRIVERS_LICENSE = r'\b(?:DL|DLN)[\s:]*(?:[A-Z0-9]{5,8})\b'

    # 8. Passport Number: Usually 6-9 alphanumeric
    PASSPORT = r'\b(?:passport|ppn)[\s:]*(?:[A-Z0-9]{6,9})\b'

    # 9. Tax ID: XX-XXXXXXX format
    TAX_ID = r'\b\d{2}-\d{7}\b'

    # 10. Medical Record Number
    MEDICAL_RECORD = r'\b(?:MRN|medical\s+record)[\s:]*(?:\d{6,10})\b'

    # ============= CONTACT INFORMATION (3 types) =============
    # 11. Phone numbers: (123) 456-7890, 123-456-7890, +1-123-456-7890, +91-XXXXXXXXXX
    PHONE = r'(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b|(?:\+91[-\s]?)?[6-9]\d{9}\b'

    # 12. Mobile/Cell phone patterns (US/International + Indian)
    MOBILE_PHONE = r'\b(?:mobile|cell|phone)[\s:]*(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b|(?:mobile|cell|phone)[\s:]*(?:\+91[-\s]?)?[6-9]\d{9}\b'

    # 13. Fax numbers: Similar to phone numbers
    FAX_NUMBER = r'\b(?:fax)[\s:]*(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b|(?:fax)[\s:]*(?:\+91[-\s]?)?[6-9]\d{9}\b'

    # 13b. Indian phone numbers (standalone): +91-XXXXXXXXXX, 0XXXXXXXXXX, XXXXXXXXXX
    INDIAN_PHONE = r'(?:\+91[-\s]?)?[6-9]\d{9}\b|0[6-9]\d{9}\b'

    # ============= INTERNET & NETWORK (3 types) =============
    # 14. IP addresses: 192.168.1.1
    IP_ADDRESS = r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'

    # 15. IPv6 addresses
    IPV6_ADDRESS = r'(?:[0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}'

    # 16. MAC addresses: 00:1A:2B:3C:4D:5E
    MAC_ADDRESS = r'\b(?:[0-9A-Fa-f]{2}[:-]){5}(?:[0-9A-Fa-f]{2})\b'

    # ============= ACCOUNT & SUBSCRIPTION (3 types) =============
    # 17. Account/Customer IDs: ACC-123456, CUST-789, etc. (strict format only)
    ACCOUNT_ID = r'\b(?:ACC|ACCT|CUST)[-][\dA-Z]{6,}\b'

    # 18. Username/Login credentials: Only if explicitly labeled with colon or equals
    USERNAME = r'\b(?:username|userid)[\s:=]*(?:[A-Za-z0-9._-]{8,})\b'

    # 19. API keys and tokens: Usually long alphanumeric strings (50+ chars)
    API_KEY = r'\b(?:api[_-]?key|token|api[_-]?token)[\s:=]*(?:[A-Za-z0-9_\-]{50,})\b'

    # ============= ADDRESSES & LOCATION (2 types) =============
    # 20. Street addresses with house numbers
    STREET_ADDRESS = r'\b\d{1,5}\s+(?:North|South|East|West|N|S|E|W)?\s*(?:1st|2nd|3rd|[4-9]th|Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)\b'

    # 21. ZIP/Postal codes: 5 digits or ZIP+4
    ZIP_CODE = r'\b\d{5}(?:-\d{4})?\b'


class PIIDetector:
    """Detects PII in text"""

    @staticmethod
    def find_pii(text: str) -> Dict[str, List[str]]:
        """
        Scan text for PII and return detected instances.

        Args:
            text: The text to scan for PII

        Returns:
            Dictionary with PII types as keys and lists of found instances as values
        """
        findings = {}

        patterns = {
            # Financial Information (5)
            'emails': PIIPatterns.EMAIL,
            'credit_cards': PIIPatterns.CREDIT_CARD,
            'credit_card_expiry': PIIPatterns.CREDIT_CARD_EXPIRY,
            'credit_card_cvv': PIIPatterns.CREDIT_CARD_CVV,
            'bank_accounts': PIIPatterns.BANK_ACCOUNT,

            # Identification Numbers (5)
            'ssn': PIIPatterns.SSN,
            'drivers_license': PIIPatterns.DRIVERS_LICENSE,
            'passport': PIIPatterns.PASSPORT,
            'tax_id': PIIPatterns.TAX_ID,
            'medical_records': PIIPatterns.MEDICAL_RECORD,

            # Contact Information (4)
            'phone_numbers': PIIPatterns.PHONE,
            'mobile_phones': PIIPatterns.MOBILE_PHONE,
            'fax_numbers': PIIPatterns.FAX_NUMBER,
            'indian_phone_numbers': PIIPatterns.INDIAN_PHONE,

            # Internet & Network (3)
            'ip_addresses': PIIPatterns.IP_ADDRESS,
            'ipv6_addresses': PIIPatterns.IPV6_ADDRESS,
            'mac_addresses': PIIPatterns.MAC_ADDRESS,

            # Account & Subscription (3)
            'account_ids': PIIPatterns.ACCOUNT_ID,
            'usernames': PIIPatterns.USERNAME,
            'api_keys': PIIPatterns.API_KEY,

            # Addresses & Location (2)
            'street_addresses': PIIPatterns.STREET_ADDRESS,
            'zip_codes': PIIPatterns.ZIP_CODE,
        }

        for pii_type, pattern in patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                findings[pii_type] = matches
                logger.warning(f"Detected {pii_type}: {len(matches)} instance(s)")

        return findings

    @staticmethod
    def has_pii(text: str) -> bool:
        """Check if text contains any PII"""
        return bool(PIIDetector.find_pii(text))

    @staticmethod
    def get_pii_summary(detected_pii: Dict[str, List[str]]) -> str:
        """Generate a user-friendly summary of detected PII"""
        if not detected_pii:
            return ""

        types = list(detected_pii.keys())
        return f"Detected: {', '.join(types)}"


class PIIMasker:
    """Masks PII in text before sending to external APIs"""

    @staticmethod
    def mask_pii(text: str) -> Tuple[str, Dict[str, List[str]]]:
        """
        Mask all PII in text and return both masked text and detected PII.

        Args:
            text: The text to mask

        Returns:
            Tuple of (masked_text, detected_pii_dict)
        """
        detected_pii = PIIDetector.find_pii(text)
        masked_text = text

        # Mask Financial Information (5 types)
        if 'emails' in detected_pii:
            masked_text = re.sub(PIIPatterns.EMAIL, '[EMAIL_MASKED]', masked_text, flags=re.IGNORECASE)
        if 'credit_cards' in detected_pii:
            masked_text = re.sub(PIIPatterns.CREDIT_CARD, '[CREDITCARD_MASKED]', masked_text, flags=re.IGNORECASE)
        if 'credit_card_expiry' in detected_pii:
            masked_text = re.sub(PIIPatterns.CREDIT_CARD_EXPIRY, '[EXPIRY_MASKED]', masked_text, flags=re.IGNORECASE)
        if 'credit_card_cvv' in detected_pii:
            masked_text = re.sub(PIIPatterns.CREDIT_CARD_CVV, '[CVV_MASKED]', masked_text, flags=re.IGNORECASE)
        if 'bank_accounts' in detected_pii:
            masked_text = re.sub(PIIPatterns.BANK_ACCOUNT, '[BANK_ACCOUNT_MASKED]', masked_text, flags=re.IGNORECASE)

        # Mask Identification Numbers (5 types)
        if 'ssn' in detected_pii:
            masked_text = re.sub(PIIPatterns.SSN, '[SSN_MASKED]', masked_text, flags=re.IGNORECASE)
        if 'drivers_license' in detected_pii:
            masked_text = re.sub(PIIPatterns.DRIVERS_LICENSE, '[DL_MASKED]', masked_text, flags=re.IGNORECASE)
        if 'passport' in detected_pii:
            masked_text = re.sub(PIIPatterns.PASSPORT, '[PASSPORT_MASKED]', masked_text, flags=re.IGNORECASE)
        if 'tax_id' in detected_pii:
            masked_text = re.sub(PIIPatterns.TAX_ID, '[TAX_ID_MASKED]', masked_text, flags=re.IGNORECASE)
        if 'medical_records' in detected_pii:
            masked_text = re.sub(PIIPatterns.MEDICAL_RECORD, '[MRN_MASKED]', masked_text, flags=re.IGNORECASE)

        # Mask Contact Information (3 types)
        if 'phone_numbers' in detected_pii:
            masked_text = re.sub(PIIPatterns.PHONE, '[PHONE_MASKED]', masked_text, flags=re.IGNORECASE)
        if 'mobile_phones' in detected_pii:
            masked_text = re.sub(PIIPatterns.MOBILE_PHONE, '[MOBILE_MASKED]', masked_text, flags=re.IGNORECASE)
        if 'fax_numbers' in detected_pii:
            masked_text = re.sub(PIIPatterns.FAX_NUMBER, '[FAX_MASKED]', masked_text, flags=re.IGNORECASE)
        if 'indian_phone_numbers' in detected_pii:
            masked_text = re.sub(PIIPatterns.INDIAN_PHONE, '[INDIAN_PHONE_MASKED]', masked_text, flags=re.IGNORECASE)

        # Mask Internet & Network (3 types)
        if 'ip_addresses' in detected_pii:
            masked_text = re.sub(PIIPatterns.IP_ADDRESS, '[IP_MASKED]', masked_text, flags=re.IGNORECASE)
        if 'ipv6_addresses' in detected_pii:
            masked_text = re.sub(PIIPatterns.IPV6_ADDRESS, '[IPV6_MASKED]', masked_text, flags=re.IGNORECASE)
        if 'mac_addresses' in detected_pii:
            masked_text = re.sub(PIIPatterns.MAC_ADDRESS, '[MAC_MASKED]', masked_text, flags=re.IGNORECASE)

        # Mask Account & Subscription (3 types)
        if 'account_ids' in detected_pii:
            masked_text = re.sub(PIIPatterns.ACCOUNT_ID, '[ACCOUNT_ID_MASKED]', masked_text, flags=re.IGNORECASE)
        if 'usernames' in detected_pii:
            masked_text = re.sub(PIIPatterns.USERNAME, '[USERNAME_MASKED]', masked_text, flags=re.IGNORECASE)
        if 'api_keys' in detected_pii:
            masked_text = re.sub(PIIPatterns.API_KEY, '[APIKEY_MASKED]', masked_text, flags=re.IGNORECASE)

        # Mask Addresses & Location (2 types)
        if 'street_addresses' in detected_pii:
            masked_text = re.sub(PIIPatterns.STREET_ADDRESS, '[ADDRESS_MASKED]', masked_text, flags=re.IGNORECASE)
        if 'zip_codes' in detected_pii:
            masked_text = re.sub(PIIPatterns.ZIP_CODE, '[ZIP_MASKED]', masked_text, flags=re.IGNORECASE)

        if detected_pii:
            logger.info(f"Masked PII in text. Detected types: {list(detected_pii.keys())}")

        return masked_text, detected_pii
