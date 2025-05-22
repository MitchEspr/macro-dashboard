import requests
import pandas as pd
from datetime import datetime, timedelta
import logging
from typing import Optional, List, Dict, Any

# Import for historical data
from app.services.historical_ism_data import get_historical_data as get_hardcoded_historical_ism_data

logger = logging.getLogger(__name__)

class DBNomicsService:
    """Service for fetching data from db.nomics.world API based on proper API structure."""

    BASE_URL = "https://api.db.nomics.world/v22"

    def __init__(self):
        pass

    def _merge_and_convert_to_df(
        self,
        historical_data_dicts: List[Dict[str, Any]], # Expects list of {'date': datetime, 'value': float}
        dbnomics_df_raw: pd.DataFrame, # Expects 'date' (datetime) and 'value' (float) columns
        requested_start_dt: Optional[datetime] = None,
        requested_end_dt: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Merges historical data with DBNomics data. DBNomics data takes precedence for overlapping dates.
        Sorts, removes duplicates, and filters by the originally requested date range.
        """
        
        # Convert historical data dicts to DataFrame
        if historical_data_dicts:
            df_historical = pd.DataFrame(historical_data_dicts)
            df_historical['date'] = pd.to_datetime(df_historical['date'])
        else:
            df_historical = pd.DataFrame(columns=['date', 'value'])

        # Prepare DBNomics DataFrame
        if not dbnomics_df_raw.empty:
            df_dbnomics = dbnomics_df_raw.copy()
            df_dbnomics['date'] = pd.to_datetime(df_dbnomics['date'])
        else:
            df_dbnomics = pd.DataFrame(columns=['date', 'value'])

        # Concatenate historical data first, then DBNomics data
        # This way, if keep='last' is used for duplicates, DBNomics data is preferred
        combined_df = pd.concat([df_historical, df_dbnomics], ignore_index=True)
        
        if combined_df.empty:
            return pd.DataFrame(columns=["date", "value"])

        # Ensure date column is datetime
        combined_df['date'] = pd.to_datetime(combined_df['date'])
        
        # Sort by date
        combined_df.sort_values(by="date", inplace=True)
        
        # Drop duplicates on 'date', keeping the DBNomics version (the 'last' one for a given date)
        combined_df.drop_duplicates(subset=["date"], keep="last", inplace=True)

        # Final filtering based on the originally requested date range
        if requested_start_dt:
            combined_df = combined_df[combined_df["date"] >= requested_start_dt]
        if requested_end_dt:
            combined_df = combined_df[combined_df["date"] <= requested_end_dt]
            
        return combined_df.reset_index(drop=True)


    def get_series_by_id(self, provider_code: str, dataset_code: str, series_code: str, params: Optional[dict] = None, fetch_observations: bool = True):
        series_id = f"{provider_code}/{dataset_code}/{series_code}"
        endpoint = f"{self.BASE_URL}/series"

        query_params = {
            "series_ids": series_id,
        }

        if fetch_observations:
            query_params["observations"] = "true"
        
        # We will not pass start/end date params to DBNomics here,
        # as we want all available data from them to merge correctly with historical.
        # Date filtering will happen after merging.

        try:
            logger.info(f"Fetching ALL available series {series_id} from DBNomics with params: {query_params}")
            response = requests.get(endpoint, params=query_params)
            response.raise_for_status()
            data = response.json()

            if not data or "series" not in data or not isinstance(data.get("series"), dict) or "docs" not in data["series"]:
                logger.warning(f"No 'series.docs' key or expected structure in DBNomics response for {series_id}. Response: {data}")
                return pd.DataFrame(columns=["date", "value"])

            series_docs = data["series"]["docs"]

            if not isinstance(series_docs, list) or len(series_docs) == 0:
                logger.warning(f"'series.docs' is not a list or is empty for {series_id}. Full DBNomics response: {data}")
                return pd.DataFrame(columns=["date", "value"])

            series_data = series_docs[0]

            if fetch_observations: # This will always be true for our ISM calls
                if "period" not in series_data or "value" not in series_data:
                    logger.warning(f"Missing 'period' or 'value' in series data for {series_id}. Series data: {series_data}")
                    return pd.DataFrame(columns=["date", "value"])

                periods = series_data.get("period")
                values = series_data.get("value")

                if not isinstance(periods, list) or not isinstance(values, list) or len(periods) != len(values):
                    logger.warning(f"Period and value arrays have different lengths or are not lists for {series_id}")
                    return pd.DataFrame(columns=["date", "value"])

                if not periods:
                     logger.info(f"No observations (empty period list) returned for {series_id} from DBNomics.")
                     return pd.DataFrame(columns=["date", "value"])

                df = pd.DataFrame({
                    "date": pd.to_datetime(periods),
                    "value": pd.to_numeric(values, errors="coerce")
                })
                df = df.dropna(subset=['value'])
                
                logger.info(f"Successfully fetched {len(df)} observations for {series_id} from DBNomics.")
                return df
            else:
                # This path should ideally not be taken if fetch_observations is true.
                logger.info(f"Fetched metadata (no observations) for {series_id}")
                return pd.DataFrame(columns=["date", "value"])

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching series from DBNomics for {series_id}: {e}", exc_info=True)
            return pd.DataFrame(columns=["date", "value"])
        except ValueError as e: 
            logger.error(f"Error processing DBNomics response for {series_id}: {e}", exc_info=True)
            return pd.DataFrame(columns=["date", "value"])
        except Exception as e:
            logger.error(f"Unexpected error fetching series from DBNomics for {series_id}: {e}", exc_info=True)
            return pd.DataFrame(columns=["date", "value"])

    def _get_augmented_ism_series(
        self,
        provider: str,
        dataset: str,
        series: str,
        historical_series_key: str, 
        observation_start: Optional[str] = None,
        observation_end: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Fetches ISM series, augments with all relevant hardcoded historical data,
        prioritizes DBNomics data for overlaps, and then filters to the requested date range.
        """
        requested_start_dt = pd.to_datetime(observation_start) if observation_start else None
        requested_end_dt = pd.to_datetime(observation_end) if observation_end else datetime.now()

        # 1. Fetch ALL available historical data within the user's requested window.
        # If no start/end is given, historical_ism_data.py's helper will return all it has for the key.
        # For robustness, we pass the user's requested window to the historical data fetcher.
        historical_data_dicts: List[Dict[str, Any]] = []
        if requested_start_dt: # Only fetch historical if a start date is actually requested
            logger.info(f"Fetching hardcoded historical {historical_series_key} data from {requested_start_dt.strftime('%Y-%m-%d')} to {requested_end_dt.strftime('%Y-%m-%d')}")
            historical_data_dicts = get_hardcoded_historical_ism_data(
                historical_series_key,
                requested_start_dt.strftime("%Y-%m-%d"),
                requested_end_dt.strftime("%Y-%m-%d") 
            )
        else: # If no observation_start, we might not need very old historical data unless DBNomics is empty.
              # However, to ensure all PDF data is available if DBNomics fails or has gaps, fetch all historical.
              # The final filtering in _merge_and_convert_to_df will handle the range.
              # To be safe and ensure all provided PDF data is considered:
            logger.info(f"Fetching all available hardcoded historical {historical_series_key} data up to {requested_end_dt.strftime('%Y-%m-%d')}")
            # A very early start date to get all historical data up to requested_end_dt
            # This ensures if DBNomics is empty, we still get the full historical range.
            # The get_hardcoded_historical_ism_data will only return what's in the lists.
            earliest_possible_historical_start = "1900-01-01" # Or some other suitably early date
            historical_data_dicts = get_hardcoded_historical_ism_data(
                historical_series_key,
                earliest_possible_historical_start, # Fetch all historical data available
                requested_end_dt.strftime("%Y-%m-%d")
            )


        # 2. Fetch ALL available data from DBNomics (get_series_by_id fetches all, no date params passed)
        dbnomics_df_raw = self.get_series_by_id(provider, dataset, series, fetch_observations=True)
        
        # 3. Merge, prioritize DBNomics, and filter to the originally requested date range
        final_df = self._merge_and_convert_to_df(
            historical_data_dicts,
            dbnomics_df_raw,
            requested_start_dt, 
            requested_end_dt  
        )
        
        logger.info(f"Returning {len(final_df)} total points for {historical_series_key} after augmentation and final date filtering.")
        return final_df


    def get_ism_pmi(self, observation_start: Optional[str] = None, observation_end: Optional[str] = None):
        return self._get_augmented_ism_series(
            provider="ISM",
            dataset="pmi",
            series="pm",
            historical_series_key="PMI",
            observation_start=observation_start,
            observation_end=observation_end
        )

    def get_ism_new_orders(self, observation_start: Optional[str] = None, observation_end: Optional[str] = None):
        return self._get_augmented_ism_series(
            provider="ISM",
            dataset="neword", 
            series="in",      
            historical_series_key="NEW_ORDERS",
            observation_start=observation_start,
            observation_end=observation_end
        )

    # --- Other methods (get_providers, get_datasets) remain unchanged ---
    def get_providers(self):
        endpoint = f"{self.BASE_URL}/providers"
        try:
            logger.info("Fetching providers list from DBNomics")
            response = requests.get(endpoint)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching providers from DBNomics: {str(e)}", exc_info=True)
            return {}
        except ValueError as e: 
            logger.error(f"JSON decode error fetching providers from DBNomics: {str(e)}", exc_info=True)
            return {}

    def get_datasets(self, provider_code: str):
        endpoint = f"{self.BASE_URL}/datasets/{provider_code}"
        try:
            logger.info(f"Fetching datasets for provider {provider_code}")
            response = requests.get(endpoint)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching datasets for {provider_code} from DBNomics: {str(e)}", exc_info=True)
            return {}
        except ValueError as e: 
            logger.error(f"JSON decode error fetching datasets for {provider_code} from DBNomics: {str(e)}", exc_info=True)
            return {}
