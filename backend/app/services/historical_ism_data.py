# backend/app/services/historical_ism_data.py
import json
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

# Define the path to the JSON file relative to this file's location
# __file__ is the path to the current file (historical_ism_data.py)
# os.path.dirname(__file__) gets the directory of the current file
# os.path.join then creates a path like /path/to/services/historical_ism_data.json
JSON_DATA_FILE = os.path.join(os.path.dirname(__file__), "historical_ism_data.json")

_historical_data_cache = None

def _load_historical_data_from_json():
    """
    Loads historical ISM data from the JSON file.
    Caches the data after the first load to avoid repeated file I/O.
    """
    global _historical_data_cache
    if _historical_data_cache is not None:
        return _historical_data_cache

    try:
        with open(JSON_DATA_FILE, 'r') as f:
            data = json.load(f)
            # Data is loaded as is; date string conversion to datetime happens in get_historical_data
            _historical_data_cache = data
            logger.info(f"Successfully loaded historical ISM data from {JSON_DATA_FILE}")
            return data
    except FileNotFoundError:
        logger.error(f"Historical ISM data file not found: {JSON_DATA_FILE}")
        _historical_data_cache = {} # Cache empty dict to prevent repeated attempts
        return {}
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from historical ISM data file: {JSON_DATA_FILE}", exc_info=True)
        _historical_data_cache = {}
        return {}
    except Exception as e:
        logger.error(f"An unexpected error occurred while loading historical ISM data: {e}", exc_info=True)
        _historical_data_cache = {}
        return {}

def get_historical_data(series_key: str, start_date_str: str, end_date_str: str):
    """
    Retrieves historical data for a given series key from the loaded JSON data,
    filtered within a specified date range.

    Args:
        series_key (str): Identifier for the series (e.g., "PMI", "NEW_ORDERS").
        start_date_str (str): Start date in 'YYYY-MM-DD' format.
        end_date_str (str): End date in 'YYYY-MM-DD' format.

    Returns:
        list: A list of {"date": datetime_object, "value": float} dicts.
    """
    all_historical_data = _load_historical_data_from_json() # Ensures data is loaded (and cached)

    if not all_historical_data or series_key not in all_historical_data:
        logger.warning(f"No historical data found for series key '{series_key}' in cache or file.")
        return []

    data_source = all_historical_data[series_key] # This is a list of {"date": "str", "value": float}

    results = []
    try:
        start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date_str, "%Y-%m-%d")
    except ValueError:
        logger.error(f"Invalid date format provided to get_historical_data: start='{start_date_str}', end='{end_date_str}'")
        return []

    for record in data_source:
        try:
            record_dt_str = record.get("date")
            record_value = record.get("value")

            if not isinstance(record_dt_str, str) or len(record_dt_str) != 10 or record_value is None:
                logger.warning(f"Skipping record with invalid format in JSON for {series_key}: {record}")
                continue
            
            record_dt = datetime.strptime(record_dt_str, "%Y-%m-%d")
            
            if start_dt <= record_dt <= end_dt:
                results.append({"date": record_dt, "value": float(record_value)})
        except ValueError: # Catches errors from strptime or float conversion
            logger.warning(f"Skipping record due to parsing error (date or value) for {series_key}: {record}")
            continue
        except TypeError: # Catches errors if record_value is not convertible to float
            logger.warning(f"Skipping record due to type error (likely for value) for {series_key}: {record}")
            continue

    results.sort(key=lambda x: x["date"])
    logger.debug(f"Returning {len(results)} historical records for {series_key} between {start_date_str} and {end_date_str}")
    return results

