#!/usr/bin/env python3
"""
Geocoding Module for PDF NER Application

This module handles geocoding of named entities using Esri's geocoding service.
It takes text with XML tags around entities and returns text with geocoding coordinates.
"""

import re
import requests
import time
from typing import Tuple, Optional
from .logging_config import get_logger

# Get logger for this module
logger = get_logger(__name__)

# Esri geocoding service URL - this is public and doesn't need to be secret
ESRI_GEOCODING_URL = "https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates"


def calculate_max_delta_from_extent(extent: dict) -> float:
    """
    Calculate the maximum delta (difference) from extent information.
    
    Handles extents that cross special coordinate boundaries (equator, prime meridian, 
    anti-prime meridian) for accurate delta calculation.

    FIXME: Investigate python packages such as geopy to handle lat/lon arithmetic (and more).
    
    Args:
        extent (dict): Extent information with xmin, xmax, ymin, ymax keys
        
    Returns:
        float: Maximum delta value from latitude and longitude differences
        
    Raises:
        ValueError: If extent is invalid or missing required keys
    """
    if not extent or not all(key in extent for key in ['xmin', 'xmax', 'ymin', 'ymax']):
        raise ValueError("Invalid extent: missing required keys (xmin, xmax, ymin, ymax)")
    
    try:
        # Extract extent boundaries
        xmin, xmax = extent['xmin'], extent['xmax']
        ymin, ymax = extent['ymin'], extent['ymax']
        
        # Calculate latitude delta (always straightforward - no wrapping - even crossing equator)
        delta_latitude = abs(ymax - ymin)
        
        # Calculate longitude delta with special handling for meridian crossings
        delta_longitude = _calculate_longitude_delta(xmin, xmax)
        
        # Take the maximum delta
        max_delta = max(delta_latitude, delta_longitude)

        # Add a percentage to maxdela so boundary cases are zoomed out one level
        max_delta *= 1.1
        
        return max_delta
    except (KeyError, ValueError, TypeError) as e:
        raise ValueError(f"Error calculating delta from extent: {e}")


def _calculate_longitude_delta(xmin: float, xmax: float) -> float:
    """
    Calculate longitude delta with proper handling for meridian crossings.
    
    Uses sign detection to determine meridian crossing type:
    - Different signs: Check if spanning prime meridian or anti-prime meridian
    - Same signs: Simple absolute difference
    
    Args:
        xmin (float): Minimum longitude (-180 to 180)
        xmax (float): Maximum longitude (-180 to 180)
        
    Returns:
        float: Longitude delta accounting for meridian crossings
    """
    # Normalize longitudes to [-180, 180] range
    xmin = _normalize_longitude(xmin)
    xmax = _normalize_longitude(xmax)
    
    # Check if xmin and xmax have different signs (one negative, one positive)
    if (xmin < 0 and xmax > 0) or (xmin > 0 and xmax < 0):
        # Different signs - determine which meridian is being crossed
        abs_sum = abs(xmin) + abs(xmax)
        
        if abs_sum <= 180:
            # Spanning prime meridian (0°) - add absolute values
            return abs_sum
        else:
            # Spanning anti-prime meridian (±180°) - add absolute values then subtract from 360°
            return 360.0 - abs_sum
    else:
        # Same signs or one is zero - normal case, no meridian crossing
        return abs(xmax - xmin)


def _normalize_longitude(longitude: float) -> float:
    """
    Normalize longitude to the [-180, 180] range.  This is probably unnecessary,
    but ensures consistent handling of longitude values even if they are nonsensically
    outside this range.
    
    Args:
        longitude (float): Longitude value (any range)
        
    Returns:
        float: Normalized longitude in [-180, 180] range
    """
    # Handle the case where longitude is exactly 180 or -180
    if longitude == 180.0 or longitude == -180.0:
        return longitude
    
    # Normalize to [-180, 180] range using modulo arithmetic
    normalized = ((longitude + 180.0) % 360.0) - 180.0
    
    return normalized


def calculate_zoom_level_from_extent(extent: dict) -> int:
    """
    Calculate zoom level based on extent information from Esri geocoding response.
    
    Args:
        extent (dict): Extent information with xmin, xmax, ymin, ymax keys
        
    Returns:
        int: Zoom level (3-16)
    """
    if not extent or not all(key in extent for key in ['xmin', 'xmax', 'ymin', 'ymax']):
        return 16  # Default zoom level
    
    try:
        # Calculate the maximum delta using the dedicated function
        max_delta = calculate_max_delta_from_extent(extent)
        
        # Determine zoom level based on max_delta
        if max_delta >= 106:
            zoom_level = 2
        elif max_delta >= 53:  
            zoom_level = 3
        elif max_delta >= 26.5:  
            zoom_level = 4
        elif max_delta >= 13.25:  
            zoom_level = 5
        elif max_delta >= 6.625:  
            zoom_level = 6
        elif max_delta >= 3.3125:  
            zoom_level = 7
        elif max_delta >= 1.65625:  
            zoom_level = 8
        elif max_delta >= 0.828125:  
            zoom_level = 9
        elif max_delta >= 0.4140625:  
            zoom_level = 10
        elif max_delta >= 0.20703125:
            zoom_level = 11
        elif max_delta >= 0.103515625:  
            zoom_level = 12
        elif max_delta >= 0.0517578125:  
            zoom_level = 13
        elif max_delta >= 0.02587890625:  
            zoom_level = 14
        elif max_delta >= 0.012939453125:
            zoom_level = 15
        else:  
            zoom_level = 16

        return zoom_level
    except (ValueError, TypeError):
        return 16  # Default zoom level on error


def _select_best_candidate(candidates: list, area_of_interest: Optional[dict], entity_text: str) -> Optional[dict]:
    """
    Select the best candidate from multiple geocoding candidates.
    
    If area_of_interest is specified, selects the first candidate that falls within the area.
    If no candidates fall within the area, returns the first candidate (fallback behavior).
    If area_of_interest is not specified, returns the first candidate.
    
    Args:
        candidates (list): List of candidate results from Esri geocoding API
        area_of_interest (dict, optional): Area-of-interest bounds with keys:
            - 'min_lat': Minimum latitude (float)
            - 'max_lat': Maximum latitude (float) 
            - 'min_lon': Minimum longitude (float)
            - 'max_lon': Maximum longitude (float)
        entity_text (str): The text of the entity being geocoded (for logging)
        
    Returns:
        dict or None: The selected candidate, or None if no candidates available
    """
    if not candidates:
        return None
    
    # If no area_of_interest specified, return the first candidate (original behavior)
    if not area_of_interest:
        logger.debug(f"No area_of_interest specified for '{entity_text}', selecting first candidate")
        return candidates[0]
    
    # Validate area_of_interest parameters
    required_keys = ['min_lat', 'max_lat', 'min_lon', 'max_lon']
    if not all(key in area_of_interest for key in required_keys):
        logger.warning(f"Invalid area_of_interest format for '{entity_text}'. Required keys: {required_keys}. Using first candidate.")
        return candidates[0]
    
    # Extract bounds
    min_lat, max_lat = area_of_interest['min_lat'], area_of_interest['max_lat']
    min_lon, max_lon = area_of_interest['min_lon'], area_of_interest['max_lon']
    
    # Validate bounds
    if min_lat >= max_lat or min_lon >= max_lon:
        logger.warning(f"Invalid area_of_interest bounds for '{entity_text}': min values must be less than max values. Using first candidate.")
        return candidates[0]
    
    # Look for the first candidate within the area of interest
    for i, candidate in enumerate(candidates):
        location = candidate.get('location', {})
        lat = location.get('y')
        lon = location.get('x')
        
        if lat is not None and lon is not None:
            try:
                lat_float = float(lat)
                lon_float = float(lon)
                
                # Check if coordinates are within bounds
                if min_lat <= lat_float <= max_lat and min_lon <= lon_float <= max_lon:
                    logger.debug(f"Selected candidate {i+1}/{len(candidates)} for '{entity_text}' at ({lat_float}, {lon_float}) - within area-of-interest")
                    return candidate
                else:
                    logger.debug(f"Candidate {i+1}/{len(candidates)} for '{entity_text}' at ({lat_float}, {lon_float}) - outside area-of-interest")
            except (ValueError, TypeError):
                logger.debug(f"Candidate {i+1}/{len(candidates)} for '{entity_text}' has invalid coordinates")
                continue
    
    # No candidates found within area_of_interest, fallback to first candidate
    logger.debug(f"No candidates for '{entity_text}' found within area-of-interest (checked {len(candidates)} candidates), using first candidate as fallback")
    return candidates[0]


def geocode_entity(entity_text: str, entity_type: str, api_key: str, area_of_interest: Optional[dict] = None) -> Tuple[Optional[float], Optional[float], Optional[int]]:
    """
    Geocode a named entity using Esri's geocoding service.
    
    When multiple candidates are found and an area_of_interest is specified,
    selects the first candidate that falls within the area of interest.
    If no candidates fall within the area, returns the first candidate (fallback behavior).
    
    Args:
        entity_text (str): The text of the entity to geocode
        entity_type (str): The type of entity (GPE, LOC, or address)
        api_key (str): The Esri API key for geocoding
        area_of_interest (dict, optional): Area-of-interest bounds with keys:
            - 'min_lat': Minimum latitude (float)
            - 'max_lat': Maximum latitude (float) 
            - 'min_lon': Minimum longitude (float)
            - 'max_lon': Maximum longitude (float)
        
    Returns:
        Tuple[Optional[float], Optional[float], Optional[int]]: (latitude, longitude, zoom_level) or (None, None, None) if not found
        
    Raises:
        ValueError: If API key is not configured or invalid
        requests.RequestException: If geocoding request fails
    """
    # Check if API key is configured
    if api_key == "YOUR_ESRI_API_KEY_HERE" or not api_key:
        raise ValueError("Esri API key not configured. Please provide a valid API key")
    
    try:
        # Prepare the geocoding request - get multiple candidates when area_of_interest is specified
        max_locations = 10 if area_of_interest else 1
        params = {
            'f': 'json',
            'singleLine': entity_text,
            'maxLocations': max_locations,
            'outFields': '*',
            'token': api_key
        }
        
        # Make the request to Esri's geocoding service
        response = requests.get(ESRI_GEOCODING_URL, params=params, timeout=10)
        
        # Check for HTTP errors
        response.raise_for_status()
        
        data = response.json()
        logger.debug(f"Geocoding API response status: {response.status_code}")
        logger.debug(f"Geocoding API found {len(data.get('candidates', []))} candidates for '{entity_text}'")
        
        # Check for API-specific errors
        if 'error' in data:
            error_msg = data['error'].get('message', 'Unknown API error')
            if 'token' in error_msg.lower() or 'invalid' in error_msg.lower():
                raise ValueError(f"Invalid or expired API key: {error_msg}")
            else:
                raise ValueError(f"Geocoding API error: {error_msg}")
        
        # Check if candidates were found
        if 'candidates' in data and len(data['candidates']) > 0:
            candidates = data['candidates']
            
            # Select the best candidate based on area_of_interest if provided
            selected_candidate = _select_best_candidate(candidates, area_of_interest, entity_text)
            
            if selected_candidate:
                location = selected_candidate.get('location', {})
                lat = location.get('y')
                lon = location.get('x')
                
                if lat is not None and lon is not None:
                    lat_float = float(lat)
                    lon_float = float(lon)
                    
                    # Extract extent information and calculate zoom level
                    extent = selected_candidate.get('extent', {})
                    zoom_level = calculate_zoom_level_from_extent(extent)
                    
                    logger.debug(f"Geocoding successful for '{entity_text}': ({lat_float}, {lon_float}) with zoom level {zoom_level}")
                    return lat_float, lon_float, zoom_level
        
        logger.debug(f"No geocoding results found for '{entity_text}'")
        return None, None, None
        
    except requests.RequestException as e:
        raise requests.RequestException(f"Geocoding request failed for '{entity_text}': {e}")
    except ValueError as e:
        # Re-raise ValueError (API key or API errors)
        raise
    except Exception as e:
        raise Exception(f"Unexpected error during geocoding for '{entity_text}': {e}")


def add_geocoding_to_xml_tags(tagged_text: str, api_key: str, area_of_interest: Optional[dict] = None) -> str:
    """
    Add geocoding information to XML tags in the text.
    
    This function processes XML tags around entities and adds geocoding coordinates.
    If geocoding fails, the entity is treated as having no coordinates ("none").
    
    Args:
        tagged_text (str): Text with XML tags around entities
        api_key (str): The Esri API key for geocoding
        area_of_interest (dict, optional): Area-of-interest bounds for candidate selection
        
    Returns:
        str: Text with geocoding information added to XML tags
        
    Raises:
        ValueError: If API key is not configured or invalid
        requests.RequestException: If geocoding request fails
    """
    # Pattern to match XML tags: <GPE>text</GPE>, <LOC>text</LOC>, or <address>text</address>
    pattern = r'<(GPE|LOC|address)>(.*?)</\1>'
    
    def replace_with_geocoding(match):
        entity_type = match.group(1)
        entity_text = match.group(2)
        
        try:
            # Geocode the entity with area_of_interest support
            lat, lon, zoom_level = geocode_entity(entity_text, entity_type, api_key, area_of_interest)
            
            # Add geocoding info to the tag
            if lat is not None and lon is not None and zoom_level is not None:
                return f'<{entity_type} lat="{lat}" lon="{lon}" zoom_level="{zoom_level}">{entity_text}</{entity_type}>'
            else:
                return f'<{entity_type} lat="none" lon="none" zoom_level="none">{entity_text}</{entity_type}>'
        except (ValueError, requests.RequestException, Exception) as e:
            # Re-raise the exception to be handled by the caller
            raise e
    
    # Replace all XML tags with geocoded versions
    geocoded_text = re.sub(pattern, replace_with_geocoding, tagged_text)
    
    return geocoded_text


def is_api_key_configured(api_key: str) -> bool:
    """
    Check if the Esri API key is properly configured.
    
    Args:
        api_key (str): The API key to check
    
    Returns:
        bool: True if API key is configured, False otherwise
    """
    return api_key != "YOUR_ESRI_API_KEY_HERE" and api_key


def get_api_key_status(api_key: str) -> str:
    """
    Get a human-readable status of the API key configuration.
    
    Args:
        api_key (str): The API key to check
    
    Returns:
        str: Status message about API key configuration
    """
    if is_api_key_configured(api_key):
        return "API key is configured"
    else:
        return "API key not configured - please provide a valid Esri API key"


def process_text_with_geocoding(tagged_text: str, api_key: str, delay: float = 0.5, area_of_interest: Optional[dict] = None) -> str:
    """
    Process text with XML tags and add geocoding information.
    
    This function processes text containing XML tags around entities and adds
    geocoding coordinates.
    
    Args:
        tagged_text (str): Text with XML tags around entities
        api_key (str): The Esri API key for geocoding
        delay (float): Delay between geocoding requests in seconds
        area_of_interest (dict, optional): Area-of-interest bounds for candidate selection
        
    Returns:
        str: Text with geocoding information added to XML tags
        
    Raises:
        ValueError: If API key is not configured or invalid
        requests.RequestException: If geocoding request fails
    """
    if not is_api_key_configured(api_key):
        raise ValueError("Esri API key not configured. Please provide a valid API key")
    
    # Add geocoding to XML tags with area_of_interest support
    geocoded_text = add_geocoding_to_xml_tags(tagged_text, api_key, area_of_interest)
    
    # Add delay to be respectful to the API
    time.sleep(delay)
    
    return geocoded_text 