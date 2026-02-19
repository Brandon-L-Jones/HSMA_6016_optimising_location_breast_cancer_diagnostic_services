"""
geography.py
NHS geocoding and location lookup utilities.
"""

import requests
import streamlit as st
import re
import time
import logging

# Configure simple NHS-style logger
logging.basicConfig(level=logging.INFO, format="NHS GEOGRAPHY | %(levelname)s | %(message)s")

POSTCODE_REGEX = re.compile(r"^[A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2}$", re.IGNORECASE)

@st.cache_data
def get_lat_lon(postcode: str, retries: int = 2):
    """
    Look up latitude and longitude for a UK postcode using postcodes.io.
    Caches results to improve performance.

    Args:
        postcode (str): UK postcode to look up
        retries (int): number of retry attempts for network errors

    Returns:
        tuple: (latitude, longitude) or (None, None) if not found or invalid
    """
    postcode = postcode.strip().upper()

    if not POSTCODE_REGEX.match(postcode):
        logging.warning(f"Invalid postcode format: {postcode}")
        return None, None

    url = f"https://api.postcodes.io/postcodes/{postcode}"

    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                result = r.json().get("result")
                if result:
                    return result["latitude"], result["longitude"]
                else:
                    logging.info(f"No results found for postcode {postcode}")
                    return None, None
            else:
                logging.warning(f"API returned status {r.status_code} for postcode {postcode}")
        except requests.RequestException as e:
            logging.warning(f"Attempt {attempt}: network error for postcode {postcode} | {e}")
            time.sleep(1)

    logging.error(f"Failed to retrieve postcode {postcode} after {retries} attempts")
    return None, None
