#!/usr/bin/env python3
"""
GeoNER Package - Named Entity Recognition and Geocoding

This package provides functionality for:
- Named Entity Recognition (NER) using hybrid approach (ShipEngine + SpaCy)
- Geocoding of detected entities using Esri's service
- Transformation of XML tags to HTML hyperlinks

Main modules:
- text_to_geocode: Main processing pipeline
- ner: Named Entity Recognition functionality
- address_parser: Address parsing using ShipEngine API
- geocode: Geocoding functionality using Esri API
- tagged_text_to_geotext: XML to HTML transformation
- logging_config: Logging configuration

Note: API key management is the responsibility of the calling program.
"""

from .text_to_geocode import text_list_to_geocoded_hypertext, text_to_geocoded_hypertext, text_list_to_geotagged_text, text_to_geotagged_text

__version__ = "1.0.0"
__author__ = "Ellipsoid Labs"

# Make main functionality easily accessible
__all__ = [
    'text_list_to_geocoded_hypertext',
    'text_to_geocoded_hypertext',
    'text_list_to_geotagged_text',
    'text_to_geotagged_text'
]
