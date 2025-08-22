#!/usr/bin/env python3
"""
Address Parser Module using ShipEngine API

This module provides functionality to detect and tag addresses in text using
the ShipEngine address parsing API. It identifies addresses and wraps them
with XML tags for further processing.
"""

import re
import requests
import logging
from typing import Dict, List, Tuple, Optional
import json
from .logging_config import get_logger


class AddressParser:
    """
    A class to handle address detection and tagging using ShipEngine API.
    """
    
    def __init__(self, api_key: str, base_url: str = "https://api.shipengine.com", mock_mode: bool = False):
        """
        Initialize the Address Parser with ShipEngine API credentials.
        
        Args:
            api_key (str): ShipEngine API key
            base_url (str): ShipEngine API base URL (default: "https://api.shipengine.com")
            mock_mode (bool): If True, skip API calls and use regex-only detection
        """
        if not api_key and not mock_mode:
            raise ValueError("ShipEngine API key is required")
        
        self.api_key = api_key
        self.base_url = base_url
        self.mock_mode = mock_mode
        self.headers = {
            "API-Key": api_key,
            "Content-Type": "application/json"
        } if api_key else {}
        
        # Setup logging using centralized configuration
        self.logger = get_logger(__name__)
    
    def parse_address_with_shipengine(self, text: str) -> Optional[Dict]:
        """
        Call ShipEngine API to recognize potential addresses from text.
        
        Args:
            text (str): Text that might contain an address
            
        Returns:
            Dict: Parsed address data from ShipEngine API, or None if parsing fails
        """
        if self.mock_mode:
            self.logger.info("Mock mode: Skipping ShipEngine API call")
            return self._mock_address_validation(text)
        
        try:
            url = f"{self.base_url}/v1/addresses/recognize"
            payload = {"text": text}
            
            response = requests.put(url, json=payload, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                # Check if ShipEngine found a valid address
                if result and result.get('address'):
                    return result
            elif response.status_code == 402:
                self.logger.warning("ShipEngine API: Address recognition requires Advanced plan or higher")
                self.logger.info("Falling back to regex-only mode")
                return self._mock_address_validation(text)
            elif response.status_code == 401:
                self.logger.error("ShipEngine API: Invalid API key - falling back to regex-only mode")
                return self._mock_address_validation(text)
            else:
                self.logger.warning(f"ShipEngine API returned status {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error calling ShipEngine API: {e}")
            self.logger.info("Falling back to regex-only validation")
            return self._mock_address_validation(text)
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing ShipEngine response: {e}")
        
        return None
    
    def _mock_address_validation(self, text: str) -> Optional[Dict]:
        """
        Mock address validation using regex patterns (fallback when API unavailable).
        
        Args:
            text (str): Text to validate as an address
            
        Returns:
            Dict: Mock response similar to ShipEngine format if text looks like an address
        """
        # Basic regex patterns to identify address components
        has_number = bool(re.search(r'\b\d{1,5}\b', text))
        has_street = bool(re.search(r'\b(?:Street|St\.?|Avenue|Ave\.?|Road|Rd\.?|Lane|Ln\.?|Drive|Dr\.?|Boulevard|Blvd\.?)\b', text, re.IGNORECASE))
        has_city_state_zip = bool(re.search(r'\b[A-Za-z\s]+,\s*[A-Z]{2}\s+\d{5}(?:-\d{4})?\b', text))
        has_po_box = bool(re.search(r'\bP\.?O\.?\s+Box\s+\d+\b', text, re.IGNORECASE))
        
        # Calculate a simple confidence score
        score = 0.0
        if has_number: score += 0.3
        if has_street: score += 0.4
        if has_city_state_zip: score += 0.3
        if has_po_box: score += 0.5
        
        # Must have either (number + street) or PO box to be considered an address
        if (has_number and has_street) or has_po_box:
            # Extract basic components using regex
            address_line1 = ""
            city = ""
            state = ""
            postal_code = ""
            
            # Try to extract address line
            addr_match = re.search(r'\b\d{1,5}\s+[A-Za-z0-9\s,.-]+?(?:Street|St\.?|Avenue|Ave\.?|Road|Rd\.?|Lane|Ln\.?|Drive|Dr\.?|Boulevard|Blvd\.?|Circle|Cir\.?|Court|Ct\.?|Place|Pl\.?|Way|Parkway|Pkwy\.?)', text, re.IGNORECASE)
            if addr_match:
                address_line1 = addr_match.group().strip()
            
            # Try to extract city, state, zip
            csz_match = re.search(r'\b([A-Za-z\s]+),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)\b', text)
            if csz_match:
                city = csz_match.group(1).strip()
                state = csz_match.group(2)
                postal_code = csz_match.group(3)
            
            return {
                "score": score,
                "address": {
                    "address_line1": address_line1,
                    "city_locality": city,
                    "state_province": state,
                    "postal_code": postal_code,
                    "country_code": "US"
                }
            }
        
        return None
    
    def is_valid_address(self, parsed_response: Dict) -> bool:
        """
        Determine if a parsed address response contains enough components to be considered valid.
        
        Args:
            parsed_response (Dict): Response data from ShipEngine recognize API
            
        Returns:
            bool: True if address appears to be valid and complete
        """
        if not parsed_response or not parsed_response.get('address'):
            return False
        
        address = parsed_response['address']
        
        # Must have address line
        if not address.get('address_line1'):
            return False
        
        # Should have at least one additional component
        optional_but_helpful = ['city_locality', 'state_province', 'postal_code']
        has_additional_component = any(
            address.get(field) for field in optional_but_helpful
        )
        
        # Also check if we have a good confidence score
        score = parsed_response.get('score', 0)
        confidence_threshold = 0.5  # 50% confidence minimum
        
        return has_additional_component and score >= confidence_threshold
    
    def find_address_candidates(self, text: str) -> List[str]:
        """
        Find potential address candidates in text using regex patterns.
        
        Args:
            text (str): Input text to search for addresses
            
        Returns:
            List[str]: List of potential address strings
        """
        candidates = []
        
        # Pattern for US addresses - more flexible patterns
        address_patterns = [
            # Standard address with full components: number + street + city + state + zip
            r'\b\d{1,5}\s+[A-Za-z0-9\s,.-]+?(?:Street|St\.?|Avenue|Ave\.?|Road|Rd\.?|Lane|Ln\.?|Drive|Dr\.?|Boulevard|Blvd\.?|Circle|Cir\.?|Court|Ct\.?|Place|Pl\.?|Way|Parkway|Pkwy\.?|Highway|Hwy\.?)\b[^.!?]*?[A-Za-z\s]+[,\s]+(?:[A-Z]{2}|Alabama|Alaska|Arizona|Arkansas|California|Colorado|Connecticut|Delaware|Florida|Georgia|Hawaii|Idaho|Illinois|Indiana|Iowa|Kansas|Kentucky|Louisiana|Maine|Maryland|Massachusetts|Michigan|Minnesota|Mississippi|Missouri|Montana|Nebraska|Nevada|New Hampshire|New Jersey|New Mexico|New York|North Carolina|North Dakota|Ohio|Oklahoma|Oregon|Pennsylvania|Rhode Island|South Carolina|South Dakota|Tennessee|Texas|Utah|Vermont|Virginia|Washington|West Virginia|Wisconsin|Wyoming)\s+\d{5}(?:-\d{4})?',
            
            # More flexible pattern - address line with potential suite/apt
            r'\b\d{1,5}\s+[A-Za-z0-9\s,.-]+?(?:Street|St\.?|Avenue|Ave\.?|Road|Rd\.?|Lane|Ln\.?|Drive|Dr\.?|Boulevard|Blvd\.?|Circle|Cir\.?|Court|Ct\.?|Place|Pl\.?|Way|Parkway|Pkwy\.?)(?:\s*,?\s*(?:Suite|Ste\.?|Apt\.?|Apartment|Unit|#)\s*[A-Za-z0-9-]+)?[^.!?]*?[A-Za-z\s]+[,\s]+[A-Z]{2}\s+\d{5}(?:-\d{4})?',
            
            # PO Box patterns
            r'\b(?:P\.?O\.?\s+Box|Post\s+Office\s+Box)\s+\d+[^.!?]*?[A-Za-z\s]+[,\s]+[A-Z]{2}\s+\d{5}(?:-\d{4})?',
            
            # Simpler pattern for just number + street name (less restrictive)
            r'\b\d{1,5}\s+[A-Za-z][A-Za-z0-9\s,.-]{5,50}(?:Street|St\.?|Avenue|Ave\.?|Road|Rd\.?|Lane|Ln\.?|Drive|Dr\.?|Boulevard|Blvd\.?)'
        ]
        
        for pattern in address_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            for match in matches:
                candidate = match.group().strip()
                # Clean up candidate - remove trailing punctuation except periods in abbreviations
                candidate = re.sub(r'[,;]\s*$', '', candidate)
                
                if len(candidate) > 15:  # Filter out very short matches
                    candidates.append(candidate)
        
        # Also try to find sentences or text that might contain addresses
        # Split text into sentences and check each one
        sentences = re.split(r'[.!?]+', text)
        for sentence in sentences:
            sentence = sentence.strip()
            # Look for sentences with numbers and common address words
            if (len(sentence) > 20 and 
                re.search(r'\b\d{1,5}\s', sentence) and 
                re.search(r'\b(?:Street|St|Avenue|Ave|Road|Rd|Lane|Ln|Drive|Dr|Boulevard|Blvd)\b', sentence, re.IGNORECASE)):
                candidates.append(sentence)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_candidates = []
        for candidate in candidates:
            candidate_clean = re.sub(r'\s+', ' ', candidate.lower().strip())
            if candidate_clean not in seen and len(candidate) > 15:
                seen.add(candidate_clean)
                unique_candidates.append(candidate)
        
        return unique_candidates
    
    def tag_addresses_in_text(self, text: str) -> str:
        """
        Main method to detect addresses in text and wrap them with XML tags.
        
        Args:
            text (str): Input text that may contain addresses
            
        Returns:
            str: Text with addresses wrapped in <address>...</address> tags
        """
        if not text or not text.strip():
            return text
        
        # Find potential address candidates using regex
        candidates = self.find_address_candidates(text)
        
        if not candidates:
            self.logger.info("No address candidates found in text, trying full text with ShipEngine")
            # If no candidates found with regex, try the entire text with ShipEngine
            parsed_response = self.parse_address_with_shipengine(text)
            
            if parsed_response and self.is_valid_address(parsed_response):
                # Try to extract the original address text from the entities
                address_text = self._extract_address_text_from_entities(parsed_response, text)
                if address_text:
                    self.logger.info(f"Found address in full text: {address_text[:30]}...")
                    tagged_text = text.replace(address_text, f"<address>{address_text}</address>")
                    return tagged_text
            
            return text
        
        tagged_text = text
        addresses_found = []
        
        # Process each candidate with ShipEngine
        for candidate in candidates:
            self.logger.info(f"Checking candidate: {candidate[:50]}...")
            
            # Try to parse with ShipEngine
            parsed_response = self.parse_address_with_shipengine(candidate)
            
            if parsed_response and self.is_valid_address(parsed_response):
                self.logger.info(f"Valid address found: {candidate[:30]}...")
                
                # Tag the address in the text (only if not already tagged)
                if f"<address>{candidate}</address>" not in tagged_text:
                    tagged_text = tagged_text.replace(candidate, f"<address>{candidate}</address>")
                    addresses_found.append(candidate)
        
        if addresses_found:
            self.logger.info(f"Tagged {len(addresses_found)} addresses in text")
        else:
            self.logger.info("No valid addresses found to tag")
        
        return tagged_text
    
    def _extract_address_text_from_entities(self, parsed_response: Dict, original_text: str) -> Optional[str]:
        """
        Extract the original address text from ShipEngine entities response.
        
        Args:
            parsed_response (Dict): Response from ShipEngine recognize API
            original_text (str): Original text that was parsed
            
        Returns:
            str: Original address text if found, None otherwise
        """
        if not parsed_response.get('entities'):
            return None
        
        # Find address-related entities and their positions
        address_entities = []
        for entity in parsed_response['entities']:
            if entity.get('type') in ['address', 'address_line', 'city_locality', 'state_province', 'postal_code']:
                start_idx = entity.get('start_index')
                end_idx = entity.get('end_index')
                if start_idx is not None and end_idx is not None:
                    address_entities.append((start_idx, end_idx))
        
        if not address_entities:
            return None
        
        # Find the span that covers all address entities
        min_start = min(start for start, end in address_entities)
        max_end = max(end for start, end in address_entities)
        
        # Extract the text span, but expand to word boundaries
        address_text = original_text[min_start:max_end].strip()
        
        # Basic validation - should contain numbers and letters
        if len(address_text) > 10 and any(c.isdigit() for c in address_text):
            return address_text
        
        return None
    
    def extract_tagged_addresses(self, tagged_text: str) -> List[str]:
        """
        Extract addresses that have been tagged with XML tags.
        
        Args:
            tagged_text (str): Text containing <address>...</address> tags
            
        Returns:
            List[str]: List of addresses found within tags
        """
        pattern = r'<address>(.*?)</address>'
        matches = re.findall(pattern, tagged_text, re.DOTALL)
        return matches


def process_text_for_addresses(text: str, api_key: str = None, mock_mode: bool = False) -> str:
    """
    Convenience function to process text and tag addresses using ShipEngine API.
    
    Args:
        text (str): Input text that may contain addresses
        api_key (str, optional): ShipEngine API key (not needed in mock_mode)
        mock_mode (bool): If True, use regex-only detection without API calls
        
    Returns:
        str: Text with addresses wrapped in <address>...</address> tags
    """
    parser = AddressParser(api_key, mock_mode=mock_mode)
    return parser.tag_addresses_in_text(text)


if __name__ == "__main__":
    # Example usage
    import os
    
    # Get API key from environment variable
    api_key = os.getenv('SHIPENGINE_API_KEY')
    if not api_key:
        print("Please set SHIPENGINE_API_KEY environment variable")
        print("Example: $env:SHIPENGINE_API_KEY = 'your_api_key_here'")
        exit(1)
    
    # Example text with addresses
    sample_text = """
    John Smith lives at 123 Main Street, Anytown, CA 90210. 
    Our office is located at 456 Oak Avenue, Suite 100, Los Angeles, CA 90001.
    Please send mail to P.O. Box 789, San Francisco, CA 94102.
    The meeting will be held in New York City next week.
    """
    
    parser = AddressParser(api_key)
    result = parser.tag_addresses_in_text(sample_text)
    
    print("Original text:")
    print(sample_text)
    print("\nTagged text:")
    print(result)
    
    # Extract tagged addresses
    addresses = parser.extract_tagged_addresses(result)
    print(f"\nFound {len(addresses)} addresses:")
    for i, addr in enumerate(addresses, 1):
        print(f"{i}. {addr}")
