import requests
import pandas as pd
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class FredService:
    """Service for fetching data from the Federal Reserve Economic Data (FRED) API."""

    BASE_URL = "https://api.stlouisfed.org/fred"

    def __init__(self, api_key=None):
        self.api_key = api_key or settings.FRED_API_KEY
        if not self.api_key:
            logger.warning("FRED API key not provided. Service will not function properly.")

    def get_series_data(self, series_id, observation_start=None, observation_end=None):
        """
        Fetch time series data for a specific FRED series.
        Data will be fetched at its highest available frequency by default.

        Args:
            series_id (str): The FRED series ID (e.g., "UNRATE" for unemployment rate)
            observation_start (str, optional): Start date in YYYY-MM-DD format
            observation_end (str, optional): End date in YYYY-MM-DD format

        Returns:
            pandas.DataFrame: DataFrame with date and value columns
        """
        endpoint = f"{self.BASE_URL}/series/observations"

        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
            # "frequency": "m", # Removed to get highest available frequency
            "units": "lin",    # Levels (not percent change) - adjust if other units are needed
        }

        if observation_start:
            params["observation_start"] = observation_start
        if observation_end:
            params["observation_end"] = observation_end

        try:
            logger.info(f"Fetching FRED series {series_id} with params: {params}")
            response = requests.get(endpoint, params=params)
            response.raise_for_status() # Will raise an HTTPError for bad responses (4XX or 5XX)
            data = response.json()

            if "observations" in data and data["observations"]:
                df = pd.DataFrame(data["observations"])
                # Ensure 'date' is datetime and 'value' is numeric, handling potential FRED non-numeric values like '.'
                df["date"] = pd.to_datetime(df["date"])
                df["value"] = pd.to_numeric(df["value"], errors="coerce") # Coerce non-numeric to NaN
                df = df.dropna(subset=["value"]) # Remove rows where value became NaN
                
                logger.info(f"Successfully fetched {len(df)} observations for FRED series {series_id}")
                return df[["date", "value"]] # Ensure correct column order
            else:
                logger.warning(f"No data ('observations' key missing or empty) returned for FRED series {series_id}")
                return pd.DataFrame(columns=["date", "value"])

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching data from FRED for series {series_id}: {e}", exc_info=True)
            return pd.DataFrame(columns=["date", "value"])
        except ValueError as e: # Includes JSONDecodeError
            logger.error(f"Error decoding JSON or processing data for FRED series {series_id}: {e}", exc_info=True)
            return pd.DataFrame(columns=["date", "value"])
        except Exception as e:
            logger.error(f"Unexpected error fetching data from FRED for series {series_id}: {e}", exc_info=True)
            return pd.DataFrame(columns=["date", "value"])

    def get_series_info(self, series_id):
        """
        Get metadata about a specific FRED series.

        Args:
            series_id (str): The FRED series ID

        Returns:
            dict: Series metadata, or an empty dict if an error occurs or no info is found.
        """
        endpoint = f"{self.BASE_URL}/series"

        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
        }

        try:
            logger.info(f"Fetching series info for FRED series {series_id}")
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()

            if "seriess" in data and data["seriess"]: # Note: FRED API uses "seriess" for the list
                return data["seriess"][0]
            else:
                logger.warning(f"No info found ('seriess' key missing or empty) for FRED series {series_id}")
                return {}

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching series info from FRED for {series_id}: {e}", exc_info=True)
            return {}
        except ValueError as e: # Includes JSONDecodeError
            logger.error(f"Error decoding JSON for FRED series info {series_id}: {e}", exc_info=True)
            return {}
        except Exception as e:
            logger.error(f"Unexpected error fetching series info from FRED for {series_id}: {e}", exc_info=True)
            return {}

