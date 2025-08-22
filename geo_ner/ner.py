#!/usr/bin/env python3
"""
Named Entity Recognition (NER) Module

This module provides functionality to perform Named Entity Recognition on text
using a hybrid approach:
1. First, ShipEngine API to detect and tag addresses
2. Then, SpaCy NER to detect GPE and LOC entities

This implements the two-step NER process described in better_NER.md.
"""

import spacy
from typing import List, Tuple
from .address_parser import AddressParser
import uuid
import re
from .logging_config import get_logger

# Get logger for this module
logger = get_logger(__name__)


class NERProcessor:
    """
    A class to handle hybrid Named Entity Recognition processing using 
    ShipEngine API for addresses and SpaCy for GPE/LOC entities.
    """
    
    def __init__(self, model_name: str = None, shipengine_api_key: str = None):
        """
        Initialize the NER processor with SpaCy model and ShipEngine API key.
        
        Args:
            model_name (str): Name of the SpaCy model to use (default: "en_core_web_trf")
            shipengine_api_key (str): ShipEngine API key for address parsing
        """
        # Load model name from configuration if not explicitly provided
        from .config import get_spacy_model_name
        resolved_model = get_spacy_model_name(model_name)
        logger.debug(f"Initializing NER processor with model: {resolved_model}")
        self.model_name = resolved_model
        self.nlp = spacy.load(resolved_model)
        # Define the entity types we want to detect with SpaCy
        self.target_entities = {'GPE', 'LOC'}
        logger.debug(f"SpaCy model loaded successfully. Target entities: {self.target_entities}")

        # Initialize address parser
        if shipengine_api_key:
            self.address_parser = AddressParser(shipengine_api_key)
            logger.debug("Address parser initialized with API key")
        else:
            self.address_parser = AddressParser("dummy_key", mock_mode=True)
            if shipengine_api_key:
                logger.debug("Address parser initialized in mock mode (no API key)")
    
    def process_text(self, text: str) -> Tuple[str, bool]:
        """
        Process a text using hybrid NER approach:
        1. First, detect and tag addresses using ShipEngine API
        2. Replace address tags with placeholders to prevent double-tagging
        3. Run SpaCy NER on the placeholder text for GPE and LOC entities
        4. Restore the original address tags
        
        Args:
            text (str): Input text to process
            
        Returns:
            Tuple[str, bool]: (tagged_text, has_entities) - text with XML tags and boolean indicating if entities were found
        """
        logger.debug(f"Processing text of length {len(text)} characters")
        
        # Step 1: Tag addresses first (if address parser is available)
        address_tagged_text = text
        if self.address_parser:
            logger.debug("Step 1: Running address detection")
            address_tagged_text = self.address_parser.tag_addresses_in_text(text)
            if '<address>' in address_tagged_text:
                address_count = address_tagged_text.count('<address>')
                logger.debug(f"Found {address_count} addresses in text")
        
        # Step 2: Replace address tags with unique placeholders to prevent double-tagging
        logger.debug("Step 2: Creating placeholders for address tags")
        address_placeholders = {}
        placeholder_text = address_tagged_text
        
        # Find all address tags and replace with placeholders
        address_pattern = r'<address>(.*?)</address>'
        for match in re.finditer(address_pattern, address_tagged_text):
            full_match = match.group(0)  # The full <address>...</address> tag
            placeholder = f"ADDR_PLACEHOLDER_{uuid.uuid4().hex[:8]}"
            address_placeholders[placeholder] = full_match
            placeholder_text = placeholder_text.replace(full_match, placeholder, 1)
        
        logger.debug(f"Created {len(address_placeholders)} address placeholders")
        
        # Step 3: Process with SpaCy NER to find GPE and LOC entities
        logger.debug("Step 3: Running SpaCy NER for GPE and LOC entities")
        doc = self.nlp(placeholder_text)
        
        # Count and log detected entities
        spacy_entities = [ent for ent in doc.ents if ent.label_ in self.target_entities]
        logger.debug(f"SpaCy found {len(spacy_entities)} target entities: {[(ent.text, ent.label_) for ent in spacy_entities]}")
        
        # Step 4: Build tagged text by adding SpaCy entity tags
        logger.debug("Step 4: Adding SpaCy entity tags")
        spacy_tagged_text = placeholder_text
        entity_spans = []
        
        # Collect entity spans (in reverse order to maintain text positions)
        for ent in reversed(doc.ents):
            if ent.label_ in self.target_entities:
                entity_spans.append((ent.start_char, ent.end_char, ent.label_))
        
        # Apply SpaCy entity tags
        for start, end, label in entity_spans:
            entity_text = placeholder_text[start:end]
            tagged_entity = f"<{label}>{entity_text}</{label}>"
            spacy_tagged_text = spacy_tagged_text[:start] + tagged_entity + spacy_tagged_text[end:]
        
        # Step 5: Restore the original address tags by replacing placeholders
        logger.debug("Step 5: Restoring address placeholders")
        final_text = spacy_tagged_text
        for placeholder, original_address_tag in address_placeholders.items():
            # Check if the placeholder is inside an existing tag
            placeholder_pos = final_text.find(placeholder)
            if placeholder_pos != -1:
                # Look for surrounding tags
                before_text = final_text[:placeholder_pos]
                after_text = final_text[placeholder_pos + len(placeholder):]
                
                # Check if we're inside a tag by looking for unclosed tags before this position
                open_tags = []
                for match in re.finditer(r'<(\w+)(?:\s[^>]*)?>|</(\w+)>', before_text):
                    if match.group(1):  # Opening tag
                        open_tags.append(match.group(1))
                    elif match.group(2):  # Closing tag
                        if open_tags and open_tags[-1] == match.group(2):
                            open_tags.pop()
                
                # If we're inside a tag, just replace with the address text without tags
                if open_tags:
                    # Extract just the address text from the tag
                    address_text = re.search(r'<address>(.*?)</address>', original_address_tag)
                    if address_text:
                        final_text = final_text.replace(placeholder, address_text.group(1))
                    else:
                        final_text = final_text.replace(placeholder, original_address_tag)
                else:
                    final_text = final_text.replace(placeholder, original_address_tag)
        
        # Check if we have any entities (addresses or GPE/LOC)
        has_addresses = '<address>' in final_text
        has_spacy_entities = len(entity_spans) > 0
        has_entities = has_addresses or has_spacy_entities
        
        logger.debug(f"NER processing complete. Has addresses: {has_addresses}, Has SpaCy entities: {has_spacy_entities}, Total entities: {has_entities}")
        logger.debug(f"Final tagged text length: {len(final_text)} characters")
        
        return final_text, has_entities
    
    def process_inputs(self, text_inputs: List[str]) -> List[Tuple[str, bool, str]]:
        """
        Process multiple text inputs using hybrid NER.
        
        Args:
            text_inputs (List[str]): List of text inputs to process
            
        Returns:
            List[Tuple[str, bool, str]]: List of (tagged_text, has_entities, text_info) tuples
        """
        results = []
        
        for i, text_input in enumerate(text_inputs, 1):
            # Process the input
            tagged_text, has_entities = self.process_text(text_input)
            
            # Add input information
            results.append((tagged_text, has_entities, f"Text {i}"))
        
        return results


def create_ner_processor(model_name: str = None, shipengine_api_key: str = None) -> NERProcessor:
    """
    Factory function to create an NER processor instance.
    
    Args:
        model_name (str): Name of the SpaCy model to use
        shipengine_api_key (str): ShipEngine API key for address parsing
        
    Returns:
        NERProcessor: Initialized NER processor
    """
    return NERProcessor(model_name, shipengine_api_key)


def process_text_input(text: str, model_name: str = None, shipengine_api_key: str = None) -> Tuple[str, bool]:
    """
    Convenience function to process a single text input using hybrid NER.
    
    Args:
        text (str): Input text to process
        model_name (str): Name of the SpaCy model to use
        shipengine_api_key (str): ShipEngine API key for address parsing
        
    Returns:
        Tuple[str, bool]: (tagged_text, has_entities) - text with XML tags and boolean indicating if entities were found
    """
    processor = create_ner_processor(model_name, shipengine_api_key)
    return processor.process_text(text)


def process_text_inputs(text_inputs: List[str], model_name: str = None, shipengine_api_key: str = None) -> List[Tuple[str, bool, str]]:
    """
    Convenience function to process multiple text inputs using hybrid NER.
    
    Args:
        text_inputs (List[str]): List of text inputs to process
        model_name (str): Name of the SpaCy model to use
        shipengine_api_key (str): ShipEngine API key for address parsing
        
    Returns:
        List[Tuple[str, bool, str]]: List of (tagged_text, has_entities, text_info) tuples
    """
    processor = create_ner_processor(model_name, shipengine_api_key)
    return processor.process_inputs(text_inputs)
