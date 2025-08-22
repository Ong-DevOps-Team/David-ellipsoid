# geo_ner Package - Developer Quick Start

A Python package for Named Entity Recognition (NER) and geocoding of geographical entities in text.

## What it does

The `geo_ner` package processes text to:
1. **Extract geographical entities** using hybrid SpaCy + ShipEngine NER
2. **Geocode locations** using Esri's geocoding service with dynamic zoom level calculation
3. **Generate interactive map links** with appropriate zoom levels or tagged XML output

## Installation & Setup

### 1. Install Dependencies
```bash
pip install spacy requests toml
# Download at least one SpaCy English model (default in models.cfg is en_core_web_sm)
python -m spacy download en_core_web_sm
# Optional (install if you switch SPACY_MODEL in models.cfg):
# python -m spacy download en_core_web_md
# python -m spacy download en_core_web_lg
# python -m spacy download en_core_web_trf
```

### 2. Get API Keys (Optional but Recommended)
- **Esri API Key**: Sign up at [developers.arcgis.com](https://developers.arcgis.com) (required for geocoding)
- **ShipEngine API Key**: Sign up at [shipengine.com](https://www.shipengine.com/) (optional, improves address parsing)

## API Reference

### Import
```python
from geo_ner import (
    text_to_geocoded_hypertext,         # Single text → HTML with map links
    text_list_to_geocoded_hypertext,    # Text list → HTML with map links  
    text_to_geotagged_text,             # Single text → XML tagged entities
    text_list_to_geotagged_text         # Text list → XML tagged entities
)
```

### Entry Points

#### 1. Full Pipeline (HTML with Interactive Map Links)

**Single Text Processing:**
```python
result = text_to_geocoded_hypertext(
    text_input="Visit us at 123 Main St, Boston, MA",
    shipengine_api_key="your_shipengine_key",  # Optional
    esri_api_key="your_esri_key",              # Required
    area_of_interest={                                   # Optional: area-of-interest filter
        'min_lat': 40.0, 'max_lat': 45.0,     # Latitude bounds
        'min_lon': -75.0, 'max_lon': -70.0     # Longitude bounds  
    }
)
# Returns: str (HTML with clickable map links)
```

**Batch Text Processing:**
```python
results = text_list_to_geocoded_hypertext(
    text_inputs=["Text 1 with NYC", "Text 2 with LA"],
    shipengine_api_key="your_shipengine_key",  # Optional  
    esri_api_key="your_esri_key",              # Required
    area_of_interest={                                   # Optional: area-of-interest filter
        'min_lat': 35.0, 'max_lat': 45.0,     # Keep East Coast entities only
        'min_lon': -80.0, 'max_lon': -70.0
    }
)
# Returns: List[Tuple[str, bool, str]] 
# Each tuple: (html_text, has_entities, text_info)
```

#### 2. Partial Pipeline (XML Tagged Entities Only)

**Single Text Processing:**
```python
result = text_to_geotagged_text(
    text_input="Visit us at 123 Main St, Boston, MA",
    shipengine_api_key="your_shipengine_key",  # Optional
    esri_api_key="your_esri_key",              # Required
    area_of_interest={                                   # Optional: area-of-interest filter
        'min_lat': 40.0, 'max_lat': 45.0,     # Only return entities in this region
        'min_lon': -75.0, 'max_lon': -70.0
    }
)
# Returns: str (XML with <geo> tags including zoom_level attributes)
```

**Batch Text Processing:**
```python
results = text_list_to_geotagged_text(
    text_inputs=["Text 1 with NYC", "Text 2 with LA"],
    shipengine_api_key="your_shipengine_key",  # Optional
    esri_api_key="your_esri_key",              # Required
    area_of_interest={                                   # Optional: area-of-interest filter
        'min_lat': 32.0, 'max_lat': 49.0,     # Keep West Coast entities only
        'min_lon': -125.0, 'max_lon': -115.0
    }
)
# Returns: List[Tuple[str, bool, str]]
# Each tuple: (tagged_text, has_entities, text_info)
```

## Quick Examples

### Basic Usage
```python
from geo_ner import text_to_geocoded_hypertext

# Process text with locations
result = text_to_geocoded_hypertext(
    text_input="Our office is in San Francisco, CA at 123 Market Street.",
    shipengine_api_key=None,  # Uses mock mode
    esri_api_key="your_esri_key"
)

print(result)  # HTML with clickable map links featuring dynamic zoom levels
```

### Batch Processing
```python
from geo_ner import text_list_to_geocoded_hypertext

texts = [
    "Conference in Boston, MA",
    "Meeting at 456 Oak Ave, Seattle, WA", 
    "Visit our NYC headquarters"
]

# Define area-of-interest (East Coast only)
east_coast_area_of_interest = {
    'min_lat': 35.0, 'max_lat': 45.0,
    'min_lon': -80.0, 'max_lon': -70.0
}

results = text_list_to_geocoded_hypertext(
    text_inputs=texts,
    shipengine_api_key="your_shipengine_key",
    esri_api_key="your_esri_key",
    area_of_interest=east_coast_area_of_interest  # Only East Coast entities will be returned
)

for html_text, has_entities, text_info in results:
    if has_entities:
        print(f"{text_info}: {html_text}")
```

## Key Notes

- **ShipEngine API Key**: Optional. If not provided, uses mock address parsing mode
- **Esri API Key**: Required for geocoding. Without it, functions will raise `ValueError`
- **Area-of-Interest Parameter**: Optional geographical filtering and ambiguous entity resolution
- **Ambiguous Entity Resolution**: When multiple location candidates exist (e.g., multiple "Springfield" cities), area-of-interest automatically selects the best match within your specified region
- **Return Types**: 
  - Single-text functions return `str`
  - List functions return `List[Tuple[str, bool, str]]`
- **Zoom Levels**: Automatically calculated (3-16) based on geographical extent for optimal map viewing
- **Error Handling**: Invalid API keys or network issues raise appropriate exceptions

### Model Selection (models.cfg)

The active SpaCy model is configured (not hard-coded) via `geo_ner/models.cfg`:

```
SPACY_MODEL = "en_core_web_sm"
# Examples you can switch to:
# SPACY_MODEL = "en_core_web_md"
# SPACY_MODEL = "en_core_web_lg"
# SPACY_MODEL = "en_core_web_trf"
```

How it works:
- If `SPACY_MODEL` is absent or file missing, falls back to `en_core_web_sm`.
- Passing `model_name` explicitly to low-level helpers still overrides the config (public high-level API does not expose this).
- Make sure you have run `python -m spacy download <model>` for any model you set.

When to change:
- Use `sm` for fastest dev feedback / CI.
- Use `md` for better vectors + moderate speed.
- Use `lg` for higher accuracy (adds large vectors).
- Use `trf` for highest accuracy (slowest, requires transformer deps).

### Area-of-Interest Filtering

The optional `area_of_interest` parameter filters entities to a specific geographical region and **resolves ambiguous named entities** by selecting the best candidate within your specified bounds.

#### Resolving Ambiguous Place Names

When geocoding ambiguous locations (e.g., "Springfield", "Portland", "Washington"), Esri returns multiple candidates. The area-of-interest parameter automatically selects the candidate within your region:

```python
# Example: Resolve "Springfield" ambiguity
result = text_to_geocoded_hypertext(
    text_input="Ship to Springfield office",
    esri_api_key="your_key",
    area_of_interest={
        'min_lat': 39.0, 'max_lat': 43.0,     # Illinois region
        'min_lon': -91.5, 'max_lon': -87.0    
    }
)
# Returns Springfield, IL (not Springfield, MA or MO)
```

#### Basic Geographic Filtering

```python
# Define area-of-interest bounds
area_of_interest = {
    'min_lat': 40.0,   # Southern boundary (latitude)
    'max_lat': 45.0,   # Northern boundary (latitude)  
    'min_lon': -75.0,  # Western boundary (longitude)
    'max_lon': -70.0   # Eastern boundary (longitude)
}

# Only entities within these bounds will be included in results
result = text_to_geocoded_hypertext(
    text_input="Visit NYC, LA, and Boston",
    esri_api_key="your_key",
    area_of_interest=area_of_interest  # Only NYC and Boston returned (LA filtered out)
)
```

**Use Cases:**
- **Ambiguity resolution**: Ensure place names resolve to intended locations within your region
- **Regional analysis**: Focus on specific geographic areas for business operations
- **Performance optimization**: Reduce processing for irrelevant locations outside your scope
- **Data quality**: Filter entities to maintain geographical consistency in results

## Dynamic Zoom Levels

The package automatically calculates appropriate zoom levels (3-16) for each geocoded entity based on its geographical extent, providing optimal map viewing experience.

### How It Works

```python
# Different entity types get different zoom levels automatically
result = text_to_geocoded_hypertext(
    text_input="Visit New York State, New York City, and Times Square.",
    esri_api_key="your_esri_key"
)

# Results in HTML with different zoom levels:
# - "New York State" → zoom level 7 (wide view for large area)
# - "New York City" → zoom level 10 (city-wide view)  
# - "Times Square" → zoom level 15 (detailed street-level view)
```

### Zoom Level Calculation

The system calculates zoom levels based on the geographical extent returned by Esri's geocoding service:

```python
# Automatic zoom level assignment based on geographical extent
if max_delta >= 106:     zoom_level = 3   # Large countries/states
elif max_delta >= 53:    zoom_level = 4   # States/provinces  
elif max_delta >= 26.5:  zoom_level = 5   # Regions
# ... continuing down to ...
elif max_delta >= 0.026: zoom_level = 15  # City blocks
else:                    zoom_level = 16  # Specific addresses
```

### Generated Output Examples

**HTML Output with Dynamic Zoom:**
```html
Visit <a href="https://www.arcgis.com/apps/mapviewer/index.html?center=-74.006,40.7128&level=10&marker=-74.006,40.7128" target="_blank">New York City</a> and <a href="https://www.arcgis.com/apps/mapviewer/index.html?center=-73.9851,40.7589&level=15&marker=-73.9851,40.7589" target="_blank">Times Square</a>.
```

**XML Output with Zoom Levels:**
```xml
Visit <GPE lat="40.7128" lon="-74.006" zoom_level="10">New York City</GPE> and <LOC lat="40.7589" lon="-73.9851" zoom_level="15">Times Square</LOC>.
```

### Benefits

- **Optimal viewing experience**: Each location opens at the most appropriate zoom level
- **Context-aware mapping**: Large areas show regional context, specific locations show detail  
- **Consistent user experience**: Predictable zoom behavior across different entity types
- **Enhanced usability**: No manual zoom adjustment needed for different location types

## Support

For detailed documentation, examples, and troubleshooting, see the main project README.md in the parent directory.
