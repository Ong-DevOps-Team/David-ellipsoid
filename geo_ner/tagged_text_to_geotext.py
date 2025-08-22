#!/usr/bin/env python3
"""
Text to Geotext Transformation Module

This module handles the transformation of XML tags with geocoding coordinates
into HTML hyperlink tags that open in Esri's map viewer.
"""

import re
from typing import Optional
from .logging_config import get_logger

# Get logger for this module
logger = get_logger(__name__)


def transform_xml_to_html_links(geocoded_text: str) -> str:
    """
    Transform XML tags with geocoding coordinates into HTML hyperlink tags.
    
    Args:
        geocoded_text (str): Text with XML tags containing lat/lon/zoom_level coordinates
        
    Returns:
        str: Text with HTML hyperlink tags replacing XML tags
    """
    logger.debug(f"Transforming geocoded text of length {len(geocoded_text)} characters")
    
    # Pattern to match XML tags with coordinates: <GPE lat="X" lon="Y" zoom_level="Z">text</GPE>, etc.
    pattern = r'<(GPE|LOC|address)\s+lat="([^"]+)"\s+lon="([^"]+)"\s+zoom_level="([^"]+)">([^<]+)</\1>'
    
    # Count initial XML tags
    initial_xml_tags = len(re.findall(pattern, geocoded_text))
    logger.debug(f"Found {initial_xml_tags} XML tags with coordinates and zoom levels")
    
    def replace_with_html_link(match):
        entity_type = match.group(1)
        lat = match.group(2)
        lon = match.group(3)
        zoom_level = match.group(4)
        entity_text = match.group(5)
        
        logger.debug(f"Processing {entity_type} entity: '{entity_text}' at ({lat}, {lon}) with zoom level {zoom_level}")
        
        # If coordinates are "none", remove the tag entirely
        if lat == "none" or lon == "none" or zoom_level == "none":
            logger.debug(f"Skipping entity '{entity_text}' - no valid coordinates")
            return entity_text
        
        # Create HTML hyperlink with the specified format using the zoom level
        map_url = f"https://www.arcgis.com/apps/mapviewer/index.html?center={lon},{lat}&level={zoom_level}&marker={lon},{lat}"
        logger.debug(f"Created hyperlink for '{entity_text}': {map_url}")
        return f'<a href="{map_url}" target="_blank">{entity_text}</a>'
    
    # Replace all XML tags with HTML hyperlinks
    html_text = re.sub(pattern, replace_with_html_link, geocoded_text)
    
    # Handle legacy tags without zoom levels (backward compatibility)
    legacy_pattern = r'<(GPE|LOC|address)\s+lat="([^"]+)"\s+lon="([^"]+)">([^<]+)</\1>'
    
    def replace_legacy_with_html_link(match):
        entity_type = match.group(1)
        lat = match.group(2)
        lon = match.group(3)
        entity_text = match.group(4)
        
        logger.debug(f"Processing legacy {entity_type} entity: '{entity_text}' at ({lat}, {lon})")
        
        # If coordinates are "none", remove the tag entirely
        if lat == "none" or lon == "none":
            logger.debug(f"Skipping legacy entity '{entity_text}' - no valid coordinates")
            return entity_text
        
        # Create HTML hyperlink with default zoom level 16 for legacy format
        map_url = f"https://www.arcgis.com/apps/mapviewer/index.html?center={lon},{lat}&level=16&marker={lon},{lat}"
        logger.debug(f"Created legacy hyperlink for '{entity_text}': {map_url}")
        return f'<a href="{map_url}" target="_blank">{entity_text}</a>'
    
    # Handle legacy format (for backward compatibility)
    html_text = re.sub(legacy_pattern, replace_legacy_with_html_link, html_text)
    
    # Handle tags without coordinates (from non-geocoded text) - just remove the tags
    simple_pattern = r'<(GPE|LOC|address)>([^<]+)</\1>'
    simple_tags = len(re.findall(simple_pattern, html_text))
    if simple_tags > 0:
        logger.debug(f"Removing {simple_tags} simple tags without coordinates")
        html_text = re.sub(simple_pattern, r'\2', html_text)
    
    # Handle address tags without coordinates (fallback for addresses that couldn't be geocoded)
    address_pattern = r'<address>([^<]+)</address>'
    ungeocoded_addresses = len(re.findall(address_pattern, html_text))
    if ungeocoded_addresses > 0:
        logger.debug(f"Removing {ungeocoded_addresses} ungeocoded address tags")
        html_text = re.sub(address_pattern, r'\1', html_text)
    
    # Count final hyperlinks
    hyperlink_count = html_text.count('<a href=')
    logger.debug(f"Transformation complete. Created {hyperlink_count} hyperlinks")
    
    return html_text


def extract_coordinates_from_xml(xml_text: str) -> list:
    """
    Extract coordinates from XML tags for analysis or debugging.
    
    Args:
        xml_text (str): Text with XML tags containing coordinates
        
    Returns:
        list: List of tuples (entity_type, entity_text, lat, lon, zoom_level)
    """
    # Try new format first (with zoom_level)
    pattern = r'<(GPE|LOC|address)\s+lat="([^"]+)"\s+lon="([^"]+)"\s+zoom_level="([^"]+)">([^<]+)</\1>'
    coordinates = []
    
    for match in re.finditer(pattern, xml_text):
        entity_type = match.group(1)
        lat = match.group(2)
        lon = match.group(3)
        zoom_level = match.group(4)
        entity_text = match.group(5)
        
        coordinates.append((entity_type, entity_text, lat, lon, zoom_level))
    
    # If no new format found, try legacy format (without zoom_level)
    if not coordinates:
        legacy_pattern = r'<(GPE|LOC|address)\s+lat="([^"]+)"\s+lon="([^"]+)">([^<]+)</\1>'
        
        for match in re.finditer(legacy_pattern, xml_text):
            entity_type = match.group(1)
            lat = match.group(2)
            lon = match.group(3)
            entity_text = match.group(4)
            
            coordinates.append((entity_type, entity_text, lat, lon, None))  # None for zoom_level
    
    return coordinates


def validate_xml_format(xml_text: str) -> bool:
    """
    Validate that XML tags have the correct format.
    
    Args:
        xml_text (str): Text with XML tags to validate
        
    Returns:
        bool: True if XML format is valid, False otherwise
    """
    # Pattern to match valid XML tags with coordinates and zoom levels (new format)
    pattern_new = r'<(GPE|LOC|address)\s+lat="([^"]+)"\s+lon="([^"]+)"\s+zoom_level="([^"]+)">([^<]+)</\1>'
    
    # Pattern to match legacy XML tags with coordinates only
    pattern_legacy = r'<(GPE|LOC|address)\s+lat="([^"]+)"\s+lon="([^"]+)">([^<]+)</\1>'
    
    # Find all XML tags
    xml_tags_new = re.findall(pattern_new, xml_text)
    xml_tags_legacy = re.findall(pattern_legacy, xml_text)
    
    # Check if all XML tags match either format
    all_entity_tags = re.findall(r'<(GPE|LOC|address)[^>]*>', xml_text)
    total_matching_tags = len(xml_tags_new) + len(xml_tags_legacy)
    
    return len(all_entity_tags) == total_matching_tags


def count_entities_by_type(xml_text: str) -> dict:
    """
    Count the number of entities by type in the XML text.
    
    Args:
        xml_text (str): Text with XML tags
        
    Returns:
        dict: Dictionary with entity type counts
    """
    # Count all entity tags regardless of format (new or legacy)
    gpe_count = len(re.findall(r'<GPE[^>]*>', xml_text))
    loc_count = len(re.findall(r'<LOC[^>]*>', xml_text))
    address_count = len(re.findall(r'<address[^>]*>', xml_text))
    
    return {
        'GPE': gpe_count,
        'LOC': loc_count,
        'address': address_count,
        'total': gpe_count + loc_count + address_count
    }


# Convenience function for external use
def process_geocoded_text(geocoded_text: str) -> str:
    """
    Process geocoded text and convert XML tags to HTML hyperlinks.
    
    Args:
        geocoded_text (str): Text with XML tags containing coordinates
        
    Returns:
        str: Text with HTML hyperlink tags replacing XML tags
    """
    return transform_xml_to_html_links(geocoded_text) 