"""Configuration utilities for geo_ner package.

Currently supports selecting the SpaCy model via models.cfg located
in the same package directory. Future configuration keys can be added
to the same file without changing consuming code.
"""
from __future__ import annotations

from pathlib import Path
import re
from typing import Dict, Optional
from .logging_config import get_logger

logger = get_logger(__name__)

_CONFIG_CACHE: Optional[Dict[str, str]] = None

PACKAGE_DIR = Path(__file__).parent
CONFIG_FILE = PACKAGE_DIR / "models.cfg"
DEFAULT_SPACY_MODEL = "en_core_web_sm"

LINE_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\"([^\"]+)\"\s*$")


def _parse_config(text: str) -> Dict[str, str]:
    cfg: Dict[str, str] = {}
    for ln_no, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        m = LINE_RE.match(line)
        if not m:
            logger.warning(f"Ignoring invalid config line {ln_no}: {line!r}")
            continue
        key, value = m.groups()
        cfg[key.upper()] = value
    return cfg


def load_config(force: bool = False) -> Dict[str, str]:
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None and not force:
        return _CONFIG_CACHE
    if not CONFIG_FILE.exists():
        logger.warning(f"Configuration file not found at {CONFIG_FILE}. Using defaults.")
        _CONFIG_CACHE = {}
        return _CONFIG_CACHE
    try:
        text = CONFIG_FILE.read_text(encoding="utf-8")
        _CONFIG_CACHE = _parse_config(text)
    except Exception as e:
        logger.warning(f"Failed reading config file {CONFIG_FILE}: {e}. Using defaults.")
        _CONFIG_CACHE = {}
    return _CONFIG_CACHE


def get_spacy_model_name(override: Optional[str] = None) -> str:
    """Return the SpaCy model name to use.

    Precedence:
      1. Explicit override argument
      2. SPACY_MODEL value in config
      3. Default constant
    """
    if override:
        return override
    cfg = load_config()
    model = cfg.get("SPACY_MODEL", DEFAULT_SPACY_MODEL)
    if model != cfg.get("SPACY_MODEL"):
        logger.debug(f"Using default SpaCy model '{model}' (no SPACY_MODEL specified in config).")
    else:
        logger.debug(f"Using SpaCy model from config: {model}")
    return model
