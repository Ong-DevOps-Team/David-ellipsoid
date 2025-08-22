#!/usr/bin/env python3
"""
Text to Geocode Processing Module

This module handles the complete pipeline of processing text:
1. Named Entity Recognition (NER) using SpaCy
2. Geocoding of detected entities using Esri's service
3. Transformation of XML tags to HTML hyperlinks

This module consolidates the processing logic that was previously scattered
across multiple modules and the main app.py file.

Implementation Note:
- NER model selection is encapsulated within this package and not exposed to callers
- This allows for future refactoring (e.g., replacing SpaCy) without breaking the public API
- Geocoding is the primary purpose - this module always performs geocoding when entities are found
"""

from typing import List, Tuple, Optional, Dict, Union
from .ner import process_text_inputs
from .geocode import process_text_with_geocoding, is_api_key_configured
from .config import get_spacy_model_name
from .tagged_text_to_geotext import process_geocoded_text
from .logging_config import get_logger
import re

# Get logger for this module
logger = get_logger(__name__)


def filter_entities_by_area_of_interest(tagged_text: str, area_of_interest: Optional[Dict[str, float]] = None) -> str:
    """
    Filter XML geo-tagged entities based on area-of-interest bounds.
    
    Removes XML geo tags that fall outside the specified latitude/longitude bounds.
    
    Args:
        tagged_text (str): Text with XML geo tags containing lat/lon attributes
        area_of_interest (Dict[str, float], optional): Area-of-interest bounds with keys:
            - 'min_lat': Minimum latitude (float)
            - 'max_lat': Maximum latitude (float) 
            - 'min_lon': Minimum longitude (float)
            - 'max_lon': Maximum longitude (float)
            
    Returns:
        str: Text with out-of-bounds geo tags removed (entities return to plain text)
        
    Example:
        area_of_interest = {'min_lat': 40.0, 'max_lat': 45.0, 'min_lon': -75.0, 'max_lon': -70.0}
        # Keeps entities within New York/New England area, removes others
    """
    if not area_of_interest:
        return tagged_text
        
    # Validate area_of_interest parameters
    required_keys = ['min_lat', 'max_lat', 'min_lon', 'max_lon']
    if not all(key in area_of_interest for key in required_keys):
        logger.warning(f"Invalid area_of_interest format. Required keys: {required_keys}")
        return tagged_text
    
    # Extract bounds
    min_lat, max_lat = area_of_interest['min_lat'], area_of_interest['max_lat']
    min_lon, max_lon = area_of_interest['min_lon'], area_of_interest['max_lon']
    
    # Validate bounds
    if min_lat >= max_lat or min_lon >= max_lon:
        logger.warning("Invalid area_of_interest bounds: min values must be less than max values")
        return tagged_text
    
    # Pattern to match XML geo tags with lat/lon attributes (both new and legacy formats)
    # New format: <GPE lat="40.7128" lon="-74.006" zoom_level="10">New York</GPE>
    # Legacy format: <LOC lat="37.7749" lon="-122.4194">San Francisco</LOC>
    pattern_new = r'<(GPE|LOC|address)\s+lat="([^"]+)"\s+lon="([^"]+)"\s+zoom_level="([^"]+)"[^>]*>(.*?)</\1>'
    pattern_legacy = r'<(GPE|LOC|address)\s+lat="([^"]+)"\s+lon="([^"]+)"[^>]*>(.*?)</\1>'
    
    def check_entity_bounds_new(match):
        entity_type, lat_str, lon_str, zoom_level_str, entity_text = match.groups()
        
        # Handle "none" coordinates (entities that failed to geocode)
        if lat_str == "none" or lon_str == "none" or zoom_level_str == "none":
            # Remove the tag for entities that couldn't be geocoded
            logger.debug(f"Removing entity '{entity_text}' - no valid coordinates (geocoding failed)")
            return entity_text
        
        try:
            lat, lon = float(lat_str), float(lon_str)
            
            # Check if coordinates are within bounds
            if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
                # Keep the entity tag - it's within bounds
                logger.debug(f"Keeping entity '{entity_text}' at ({lat}, {lon}) with zoom level {zoom_level_str} - within area-of-interest bounds")
                return match.group(0)
            else:
                # Remove the tag - return just the entity text
                logger.debug(f"Removing entity '{entity_text}' at ({lat}, {lon}) - outside area-of-interest bounds")
                return entity_text
        except ValueError:
            # Invalid coordinates (unexpected format) - remove the tag
            logger.warning(f"Invalid coordinates in entity tag: lat='{lat_str}', lon='{lon_str}'")
            return entity_text
    
    def check_entity_bounds_legacy(match):
        entity_type, lat_str, lon_str, entity_text = match.groups()
        
        # Handle "none" coordinates (entities that failed to geocode)
        if lat_str == "none" or lon_str == "none":
            # Remove the tag for entities that couldn't be geocoded
            logger.debug(f"Removing legacy entity '{entity_text}' - no valid coordinates (geocoding failed)")
            return entity_text
        
        try:
            lat, lon = float(lat_str), float(lon_str)
            
            # Check if coordinates are within bounds
            if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
                # Keep the entity tag - it's within bounds
                logger.debug(f"Keeping legacy entity '{entity_text}' at ({lat}, {lon}) - within area-of-interest bounds")
                return match.group(0)
            else:
                # Remove the tag - return just the entity text
                logger.debug(f"Removing legacy entity '{entity_text}' at ({lat}, {lon}) - outside area-of-interest bounds")
                return entity_text
        except ValueError:
            # Invalid coordinates (unexpected format) - remove the tag
            logger.warning(f"Invalid coordinates in legacy entity tag: lat='{lat_str}', lon='{lon_str}'")
            return entity_text
    
    # Apply the filter - first try new format, then legacy format
    filtered_text = re.sub(pattern_new, check_entity_bounds_new, tagged_text)
    filtered_text = re.sub(pattern_legacy, check_entity_bounds_legacy, filtered_text)
    
    return filtered_text


def process_inputs_with_ner(text_inputs: List[str], shipengine_api_key: str = None) -> List[Tuple[str, bool, str]]:
    """
    Perform Named Entity Recognition on text inputs using hybrid approach.
    
    Args:
        text_inputs (List[str]): List of text inputs to process
        shipengine_api_key (str, optional): ShipEngine API key for address parsing
        
    Returns:
        List[Tuple[str, bool, str]]: List of (tagged_text, has_entities, text_info) tuples
    """
    # Model selection via configuration file (models.cfg)
    model = get_spacy_model_name()
    
    logger.debug(f"Starting NER processing for {len(text_inputs)} text inputs using model: {model}")
    results = process_text_inputs(text_inputs, model, shipengine_api_key)
    entities_found = sum(1 for _, has_entities, _ in results if has_entities)
    logger.debug(f"NER processing complete. Found entities in {entities_found} out of {len(text_inputs)} inputs")
    return results


def process_inputs_with_geocoding(inputs_with_entities: List[Tuple[str, bool, str]], 
                                 esri_api_key: str = None,
                                 area_of_interest: Optional[Dict[str, float]] = None) -> List[Tuple[str, bool, str]]:
    """
    Step 2: Geocode the named entities in the text inputs and apply area-of-interest filtering.
    
    Takes XML-tagged entities and enriches them with geocoding information.
    Optionally filters entities based on area-of-interest bounds.
    
    Args:
        inputs_with_entities (List[Tuple[str, bool, str]]): List of (tagged_text, has_entities, text_info) tuples
        esri_api_key (str): The Esri API key for geocoding
        area_of_interest (Dict[str, float], optional): Area-of-interest bounds for filtering entities
        
    Returns:
        List[Tuple[str, bool, str]]: List of inputs with geocoded XML tags (filtered by area-of-interest if specified)
        
    Raises:
        ValueError: If API key is not configured
        Exception: If geocoding fails
    """
    logger.debug(f"Starting geocoding processing for {len(inputs_with_entities)} inputs")
    
    if not is_api_key_configured(esri_api_key or ""):
        logger.debug("Geocoding requested but API key not configured")
        raise ValueError("Esri API key is not configured")
    
    if area_of_interest:
        logger.debug(f"Applying area-of-interest filtering: {area_of_interest}")
    
    geocoded_inputs = []
    
    for i, (tagged_text, has_entities, text_info) in enumerate(inputs_with_entities):
        logger.debug(f"Processing input {i+1}/{len(inputs_with_entities)}: {text_info}")
        
        if has_entities:
            try:
                logger.debug(f"Geocoding entities in: {text_info}")
                # Geocode the entities (adds coordinate information to XML tags)
                geocoded_text = process_text_with_geocoding(tagged_text, esri_api_key, area_of_interest=area_of_interest)
                
                # Apply area-of-interest filtering if specified
                if area_of_interest:
                    filtered_text = filter_entities_by_area_of_interest(geocoded_text, area_of_interest)
                    # Check if any entities remain after filtering (check for actual tag types)
                    has_entities_after_filter = any(tag in filtered_text for tag in ['<GPE', '<LOC', '<address'])
                    geocoded_inputs.append((filtered_text, has_entities_after_filter, text_info))
                    if not has_entities_after_filter:
                        logger.debug(f"All entities filtered out by area-of-interest for: {text_info}")
                else:
                    geocoded_inputs.append((geocoded_text, has_entities, text_info))
                
                logger.debug(f"Successfully geocoded {text_info}")
            except ValueError as e:
                logger.debug(f"Geocoding error for {text_info}: {e}")
                raise ValueError(f"Geocoding error: {e}")
            except Exception as e:
                raise Exception(f"Error during geocoding: {e}")
        else:
            # No entities found, pass through unchanged
            logger.debug(f"No entities to geocode in: {text_info}")
            geocoded_inputs.append((tagged_text, has_entities, text_info))
    
    return geocoded_inputs


def process_inputs_with_html_transformation(geocoded_inputs: List[Tuple[str, bool, str]]) -> List[Tuple[str, bool, str]]:
    """
    Step 3: Transform geocoded XML tags into HTML hyperlinks.
    
    Converts XML tags with geocoding information into clickable map links.
    
    Args:
        geocoded_inputs (List[Tuple[str, bool, str]]): List of (geocoded_text, has_entities, text_info) tuples
        
    Returns:
        List[Tuple[str, bool, str]]: List of inputs with HTML hyperlinks
        
    Raises:
        Exception: If HTML transformation fails
    """
    logger.debug(f"Starting HTML transformation for {len(geocoded_inputs)} inputs")
    
    html_inputs = []
    
    for i, (geocoded_text, has_entities, text_info) in enumerate(geocoded_inputs):
        logger.debug(f"Transforming input {i+1}/{len(geocoded_inputs)}: {text_info}")
        
        try:
            # Transform XML tags to HTML hyperlinks
            html_text = process_geocoded_text(geocoded_text)
            html_inputs.append((html_text, has_entities, text_info))
            logger.debug(f"Successfully transformed {text_info} to HTML")
        except Exception as e:
            logger.debug(f"HTML transformation error for {text_info}: {e}")
            raise Exception(f"Error during HTML transformation: {e}")
    
    return html_inputs


def validate_geocoding_requirements(esri_api_key: str = None) -> None:
    """
    Validate that geocoding requirements are met.
    
    Args:
        esri_api_key (str): The Esri API key for geocoding
        
    Raises:
        ValueError: If API key is not configured
    """
    if not is_api_key_configured(esri_api_key or ""):
        raise ValueError("Esri API key not configured. Please provide a valid API key.")


def filter_inputs_with_entities(results: List[Tuple[str, bool, str]]) -> List[Tuple[str, bool, str]]:
    """
    Filter results to only include inputs that contain entities.
    
    Args:
        results (List[Tuple[str, bool, str]]): List of (tagged_text, has_entities, text_info) tuples
        
    Returns:
        List[Tuple[str, bool, str]]: Filtered list containing only inputs with entities
    """
    return [result for result in results if result[1]]


def text_list_to_geocoded_hypertext(text_inputs: List[str], 
                         shipengine_api_key: str = None,
                         esri_api_key: str = None,
                         area_of_interest: Optional[Dict[str, float]] = None) -> List[Tuple[str, bool, str]]:
    """
    Complete 3-step pipeline for processing text inputs through NER, geocoding, and HTML transformation.
    
    Pipeline Steps:
    1. Named Entity Recognition: Detect geographical entities and wrap in XML tags
    2. Geocoding: Enrich XML tags with coordinate information using Esri API
    3. Area-of-Interest Filtering: Remove entities outside specified area-of-interest (if provided)
    4. HTML Transformation: Convert geocoded XML tags to clickable map hyperlinks
    
    Args:
        text_inputs (List[str]): List of text inputs to process
        shipengine_api_key (str, optional): ShipEngine API key for address parsing
        esri_api_key (str, optional): Esri API key for geocoding
        area_of_interest (Dict[str, float], optional): Area-of-interest bounds for filtering entities.
            Should contain keys: 'min_lat', 'max_lat', 'min_lon', 'max_lon'.
            Only entities within these bounds will be returned.
        
    Returns:
        List[Tuple[str, bool, str]]: List of tuples containing:
            - processed_text (str): Text with entities converted to HTML hyperlinks for map viewing
            - has_entities (bool): True if geographical entities were found in the text, False otherwise
            - text_info (str): Sequential identifier in format "Text N" (e.g., "Text 1", "Text 2", etc.)
                              where N is the position of the input text in the original input list.
                              Used for logging, debugging, and tracking individual texts in batch processing.
        
        Example return value for one entry:
            ('I visited <a href="https://www.arcgis.com/apps/mapviewer/index.html?center=-74.006,40.7128&level=10">New York City</a> last summer.', 
            True, 'Text 1')
        
    Raises:
        ValueError: If API key is not configured
        Exception: If processing fails
    """
    # Steps 1 & 2: NER + Geocoding using the new reusable function
    geocoded_results = text_list_to_geotagged_text(
        text_inputs=text_inputs,
        shipengine_api_key=shipengine_api_key,
        esri_api_key=esri_api_key,
        area_of_interest=area_of_interest
    )
    
    # Step 3: HTML Transformation - Convert geocoded XML to clickable hyperlinks
    if geocoded_results:
        final_results = process_inputs_with_html_transformation(geocoded_results)
        return final_results
    else:
        return []


def text_list_to_geotagged_text(text_inputs: List[str], 
                               shipengine_api_key: str = None,
                               esri_api_key: str = None,
                               area_of_interest: Optional[Dict[str, float]] = None) -> List[Tuple[str, bool, str]]:
    """
    2-step pipeline for processing text inputs through NER and geocoding (without HTML transformation).
    
    Pipeline Steps:
    1. Named Entity Recognition: Detect geographical entities and wrap in XML tags
    2. Geocoding: Enrich XML tags with coordinate information using Esri API
    3. Area-of-Interest Filtering: Remove entities outside specified area-of-interest (if provided)
    
    Args:
        text_inputs (List[str]): List of text inputs to process
        shipengine_api_key (str, optional): ShipEngine API key for address parsing
        esri_api_key (str, optional): Esri API key for geocoding
        area_of_interest (Dict[str, float], optional): Area-of-interest bounds for filtering entities.
            Should contain keys: 'min_lat', 'max_lat', 'min_lon', 'max_lon'.
            Only entities within these bounds will be returned.
        
    Returns:
        List[Tuple[str, bool, str]]: List of tuples containing:
            - geotagged_text (str): Text with entities wrapped in geocoded XML tags
            - has_entities (bool): True if geographical entities were found in the text, False otherwise
            - text_info (str): Sequential identifier in format "Text N" (e.g., "Text 1", "Text 2", etc.)
                              where N is the position of the input text in the original input list.
        
        Example return value for one entry:
            ('I visited <entity lat="40.7128" lon="-74.006">New York City</entity> last summer.', 
            True, 'Text 1')
        
    Raises:
        ValueError: If API key is not configured
        Exception: If processing fails
    """
    # Validate geocoding requirements
    validate_geocoding_requirements(esri_api_key)
    
    # Step 1: Named Entity Recognition - Detect entities and wrap in XML tags
    ner_results = process_inputs_with_ner(text_inputs, shipengine_api_key)
    
    # Filter to only inputs with entities for geocoding
    inputs_with_entities = filter_inputs_with_entities(ner_results)
    
    # Step 2: Geocoding with optional area-of-interest filtering - Enrich XML tags with coordinate information
    if inputs_with_entities:
        geocoded_results = process_inputs_with_geocoding(inputs_with_entities, esri_api_key, area_of_interest)
        return geocoded_results
    else:
        return []


def text_to_geotagged_text(text_input: str, 
                          shipengine_api_key: str = None,
                          esri_api_key: str = None,
                          area_of_interest: Optional[Dict[str, float]] = None) -> str:
    """
    Simplified wrapper for processing a single text input through NER and geocoding (without HTML transformation).
    
    This is a convenience function that wraps text_list_to_geotagged_text for single text processing.
    
    Args:
        text_input (str): Single text input to process
        shipengine_api_key (str, optional): ShipEngine API key for address parsing
        esri_api_key (str, optional): Esri API key for geocoding
        area_of_interest (Dict[str, float], optional): Area-of-interest bounds for filtering entities.
            Should contain keys: 'min_lat', 'max_lat', 'min_lon', 'max_lon'.
            Only entities within these bounds will be returned.
        
    Returns:
        str: Processed text with entities wrapped in geocoded XML tags.
             Returns the original text if no entities are found or processing fails.
        
        Example return value:
            'I visited <entity lat="40.7128" lon="-74.006">New York City</entity> last summer.'
        
    Raises:
        ValueError: If API key is not configured
        Exception: If processing fails
    """
    # Use the main function with a single-item list
    results = text_list_to_geotagged_text(
        text_inputs=[text_input],
        shipengine_api_key=shipengine_api_key,
        esri_api_key=esri_api_key,
        area_of_interest=area_of_interest
    )
    
    # Extract the geotagged text from the first (and only) result
    if results and len(results) > 0:
        geotagged_text, has_entities, text_info = results[0]
        return geotagged_text
    else:
        # If no results or no entities found, return original text
        return text_input


def text_to_geocoded_hypertext(text_input: str, 
                              shipengine_api_key: str = None,
                              esri_api_key: str = None,
                              area_of_interest: Optional[Dict[str, float]] = None) -> str:
    """
    Simplified wrapper for processing a single text input through NER, geocoding, and transformation.
    
    This is a convenience function that wraps text_list_to_geocoded_hypertext for single text processing.
    
    Args:
        text_input (str): Single text input to process
        shipengine_api_key (str, optional): ShipEngine API key for address parsing
        esri_api_key (str, optional): Esri API key for geocoding
        area_of_interest (Dict[str, float], optional): Area-of-interest bounds for filtering entities.
            Should contain keys: 'min_lat', 'max_lat', 'min_lon', 'max_lon'.
            Only entities within these bounds will be returned.
        
    Returns:
        str: Processed text with entities converted to HTML hyperlinks for map viewing.
             Returns the original text if no entities are found or processing fails.
        
        Example return value:
            'I visited <a href="https://www.arcgis.com/apps/mapviewer/index.html?center=-74.006,40.7128&level=10">New York City</a> last summer.'
        
    Raises:
        ValueError: If API key is not configured
        Exception: If processing fails
    """
    # Use the main function with a single-item list
    results = text_list_to_geocoded_hypertext(
        text_inputs=[text_input],
        shipengine_api_key=shipengine_api_key,
        esri_api_key=esri_api_key,
        area_of_interest=area_of_interest
    )
    
    # Extract the processed text from the first (and only) result
    if results and len(results) > 0:
        processed_text, has_entities, text_info = results[0]
        return processed_text
    else:
        # If no results or no entities found, return original text
        return text_input 
    
