# backend/app/services/unified_indicator_service.py

from typing import List, Optional, Dict, Set, Tuple
from datetime import datetime, timedelta
import logging
import pandas as pd
from app.core.indicator_config import (
    get_indicator_metadata,
    get_all_indicators,
    get_sorted_categories, 
    get_category_by_name,
    get_indicators_by_type,
    DataSourceType,
    TransformationType,
    IndicatorType,
    CategoryDefinition,
    SignalStatus 
)
from app.services.fred_service import FredService
from app.services.yahoo_finance_service import YahooFinanceService
from app.services.dbnom_service import DBNomicsService
from app.services.composite_indicators_service import CompositeIndicatorsService
from app.services.indicator_processing_service import IndicatorProcessingService
from app.models.indicators import (
    TimeSeriesPoint,
    EnrichedIndicatorData,
    IndicatorMetadataResponse,
    CategoryInfo, 
    MarketStatusResponse,
    IndicatorsByTypeResponse
)

logger = logging.getLogger(__name__)

class UnifiedIndicatorService:
    """Unified service for fetching, processing, and enriching indicator data with MA buffer handling."""

    def __init__(self):
        self.fred_service = FredService()
        self.yahoo_service = YahooFinanceService()
        self.dbnom_service = DBNomicsService()
        self.composite_service = CompositeIndicatorsService()
        self.processing_service = IndicatorProcessingService()

    def _adjust_start_date_for_transformation(
        self,
        start_date: Optional[str],
        transformation: TransformationType
    ) -> Optional[str]:
        # This function correctly returns the original start_date if transformation is not YOY
        # or if start_date is None initially.
        if not start_date or transformation != TransformationType.YOY:
            return start_date
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            adjusted_start_dt = start_dt - timedelta(days=365)
            return adjusted_start_dt.strftime('%Y-%m-%d')
        except ValueError:
            logger.warning(f"Invalid start_date format: {start_date}")
            return start_date

    def _get_fetch_dates_for_indicator(
        self,
        indicator_id: str,
        start_date: Optional[str],
        end_date: Optional[str]
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Calculate the actual start/end dates to use for fetching, considering:
        1. YoY transformation requirements
        2. Moving average buffer requirements
        
        Returns:
            Tuple of (fetch_start_date, fetch_end_date, original_start_date)
        """
        metadata = get_indicator_metadata(indicator_id)
        if not metadata:
            return start_date, end_date, start_date

        original_start_date = start_date
        
        # First, adjust for YoY transformation if needed
        transformation_adjusted_start = self._adjust_start_date_for_transformation(
            start_date, metadata.transformation
        )
        
        # Then, adjust for MA buffer if needed
        ma_buffer_days = IndicatorProcessingService.get_ma_buffer_days(metadata)
        final_fetch_start = IndicatorProcessingService.adjust_start_date_for_ma_buffer(
            transformation_adjusted_start, ma_buffer_days
        )
        
        logger.info(f"[{indicator_id}] Date calculations: original='{original_start_date}' -> transformation_adjusted='{transformation_adjusted_start}' -> final_fetch='{final_fetch_start}' (buffer_days={ma_buffer_days})")
        
        return final_fetch_start, end_date, original_start_date

    def _fetch_raw_data(
        self,
        indicator_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Tuple[List[TimeSeriesPoint], str, Optional[str], Optional[str]]:
        
        logger.info(f"[_fetch_raw_data for {indicator_id}] Received params -> start_date: '{start_date}', end_date: '{end_date}'")
        
        metadata = get_indicator_metadata(indicator_id)
        if not metadata:
            logger.error(f"Metadata not found for indicator_id '{indicator_id}' during raw data fetch.")
            return [], f"Unknown Indicator: {indicator_id}", None, None

        # Calculate the actual dates to fetch (including buffers)
        fetch_start_date, fetch_end_date, original_start_date = self._get_fetch_dates_for_indicator(
            indicator_id, start_date, end_date
        )
        
        logger.info(f"[_fetch_raw_data for {indicator_id}] Using fetch dates -> start: '{fetch_start_date}', end: '{fetch_end_date}'")

        df = pd.DataFrame()
        data_points: List[TimeSeriesPoint] = []
        title = metadata.name 
        units = metadata.units
        frequency = metadata.frequency

        try:
            # When calling specific services, pass the calculated fetch dates
            if metadata.data_source == DataSourceType.FRED:
                df = self.fred_service.get_series_data(metadata.series_id, fetch_start_date, fetch_end_date)
                series_info = self.fred_service.get_series_info(metadata.series_id)
                title = series_info.get("title", metadata.name) 
                units = series_info.get("units", metadata.units)
                frequency = series_info.get("frequency", metadata.frequency)
            elif metadata.data_source == DataSourceType.YAHOO:
                logger.info(f"[_fetch_raw_data for {indicator_id}] Calling Yahoo with series_id: '{metadata.series_id}', start: '{fetch_start_date}', end: '{fetch_end_date}'")
                df = self.yahoo_service.get_ticker_data(metadata.series_id, fetch_start_date, fetch_end_date)
            elif metadata.data_source == DataSourceType.DBNOMICS_ISM:
                logger.info(f"[_fetch_raw_data for {indicator_id}] Calling DBNOMICS_ISM with start: '{fetch_start_date}', end: '{fetch_end_date}'")
                if indicator_id == "ISM-PMI":
                    df = self.dbnom_service.get_ism_pmi(fetch_start_date, fetch_end_date)
                elif indicator_id == "ISM-NEW-ORDERS":
                    df = self.dbnom_service.get_ism_new_orders(fetch_start_date, fetch_end_date)
                else: 
                    logger.error(f"Unknown indicator ID: {indicator_id} for DataSourceType.DBNOMICS_ISM")
            elif metadata.data_source == DataSourceType.CUSTOM_COMPOSITE:
                logger.info(f"[_fetch_raw_data for {indicator_id}] Calling CUSTOM_COMPOSITE with start: '{fetch_start_date}', end: '{fetch_end_date}'")
                if indicator_id == "GOLD-COPPER-RATIO":
                    df = self.composite_service.get_gold_copper_ratio(fetch_start_date, fetch_end_date)
                else:
                    logger.error(f"Unknown CUSTOM_COMPOSITE indicator ID: {indicator_id}")
            else:
                logger.error(f"Unsupported data source: {metadata.data_source} for indicator {indicator_id}")

            if not df.empty:
                data_points = [
                    TimeSeriesPoint(date=row["date"], value=row["value"])
                    for _, row in df.iterrows() if pd.notna(row["value"])
                ]
            else:
                 logger.warning(f"No data returned from source for indicator {indicator_id}")
        except Exception as e:
            logger.error(f"Error fetching raw data for {indicator_id} from {metadata.data_source}: {e}", exc_info=True)
        
        logger.info(f"Fetched {len(data_points)} raw data points for {indicator_id} (including any buffer data)")
        return data_points, title, units, frequency

    def get_indicator(
        self,
        indicator_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> EnrichedIndicatorData:
        
        logger.info(f"[get_indicator for {indicator_id}] Received params -> start_date: '{start_date}', end_date: '{end_date}'")
        
        metadata = get_indicator_metadata(indicator_id)
        if not metadata:
            logger.error(f"Metadata not found for indicator {indicator_id} in get_indicator.")
            return EnrichedIndicatorData(
                indicator_id=indicator_id, title=f"Unknown Indicator: {indicator_id}", data=[],
                category="Unknown", bullish_threshold=0.0, bearish_threshold=0.0,
                signal_status=SignalStatus.NEUTRAL, description="Metadata not found for this indicator."
            )

        # Fetch raw data (with buffers included)
        raw_data, title, units, frequency = self._fetch_raw_data(indicator_id, start_date, end_date)
        
        # Process the data, passing the original start_date for proper trimming
        enriched_data = self.processing_service.process_indicator_data(
            indicator_id, raw_data, title, units, frequency, start_date
        )
        return enriched_data

    def get_all_indicators_metadata(self) -> List[IndicatorMetadataResponse]:
        all_indicators_meta = get_all_indicators() 
        response_list = []
        for indicator_id, metadata in all_indicators_meta.items():
            response_list.append(
                IndicatorMetadataResponse(
                    indicator_id=indicator_id, name=metadata.name, category=metadata.category, 
                    data_source=metadata.data_source.value, description=metadata.description,
                    units=metadata.units, frequency=metadata.frequency
                )
            )
        return response_list

    def get_categories(self) -> List[CategoryInfo]:
        sorted_category_defs = get_sorted_categories() 
        all_indicators_meta = get_all_indicators()   
        category_info_list = []
        for cat_def in sorted_category_defs:
            indicator_ids_for_category = [
                indicator_id for indicator_id, meta in all_indicators_meta.items()
                if meta.category == cat_def.name 
            ]
            category_info_list.append(
                CategoryInfo(
                    category_id=cat_def.id, name=cat_def.name,
                    description=cat_def.description, indicators=indicator_ids_for_category
                )
            )
        return category_info_list
    
    def get_enriched_indicators_by_type(
        self,
        indicator_type: IndicatorType,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> IndicatorsByTypeResponse:
        
        logger.info(f"[get_enriched_indicators_by_type for type '{indicator_type.value}'] Received params -> start_date: '{start_date}', end_date: '{end_date}'")
        
        typed_indicators_meta = get_indicators_by_type(indicator_type) 
        enriched_indicators_list: List[EnrichedIndicatorData] = []
        relevant_category_names_ordered: List[str] = [] 

        for indicator_id, metadata in typed_indicators_meta.items():
            try:
                # Pass the received start_date and end_date down
                enriched_data = self.get_indicator(indicator_id, start_date, end_date) 
                enriched_indicators_list.append(enriched_data)
                if metadata.category not in relevant_category_names_ordered:
                    relevant_category_names_ordered.append(metadata.category)
            except Exception as e:
                logger.error(f"Failed to fetch or process indicator {indicator_id} of type {indicator_type.value}: {e}", exc_info=True)
        
        final_categories_list: List[CategoryInfo] = []
        all_sorted_category_defs = get_sorted_categories() 
        for cat_def in all_sorted_category_defs:
            if cat_def.name in relevant_category_names_ordered:
                indicators_for_this_category_and_type = [
                    ind_id for ind_id, meta in typed_indicators_meta.items() if meta.category == cat_def.name
                ]
                if indicators_for_this_category_and_type:
                    final_categories_list.append(
                        CategoryInfo(
                            category_id=cat_def.id, name=cat_def.name,
                            description=cat_def.description, indicators=indicators_for_this_category_and_type 
                        )
                    )
        
        logger.info(f"Successfully fetched {len(enriched_indicators_list)} indicators of type {indicator_type.value}")
        return IndicatorsByTypeResponse(
            indicator_type=indicator_type.value, indicators=enriched_indicators_list, 
            categories=final_categories_list 
        )

    def get_indicators_by_category_name(self, category_name: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[EnrichedIndicatorData]:
        logger.info(f"[get_indicators_by_category_name for '{category_name}'] Received params -> start_date: '{start_date}', end_date: '{end_date}'")
        indicators_meta_dict = {
            ind_id: meta for ind_id, meta in get_all_indicators().items() 
            if meta.category == category_name
        }
        results = []
        if not indicators_meta_dict:
            logger.warning(f"No indicators found defined for category name: {category_name}")
            return []
        for indicator_id in indicators_meta_dict.keys(): 
            try:
                indicator_data = self.get_indicator(indicator_id, start_date, end_date) # Pass dates
                results.append(indicator_data)
            except Exception as e:
                logger.error(f"Error fetching indicator {indicator_id} for category {category_name}: {e}", exc_info=True)
                continue
        return results

    def calculate_market_status(
        self,
        indicator_ids: Optional[List[str]] = None
    ) -> MarketStatusResponse:
        if indicator_ids is None:
            indicator_ids = list(get_all_indicators().keys())
        bullish_count = 0
        bearish_count = 0
        neutral_count = 0
        risk_on_count = 0 
        risk_off_count = 0

        logger.info(f"Calculating market status using {len(indicator_ids)} indicators")

        for indicator_id in indicator_ids: 
            try:
                # Market status typically uses the latest signal, so not passing dates here by default.
                indicator_data = self.get_indicator(indicator_id) 
                if indicator_data.signal_status == SignalStatus.BULLISH:
                    bullish_count += 1
                elif indicator_data.signal_status == SignalStatus.BEARISH:
                    bearish_count += 1
                else: 
                    neutral_count += 1
                
                metadata = get_indicator_metadata(indicator_id)
                if metadata and metadata.category in ["Global Risk Metrics", "Market Sentiment", "Financial Market Indicators"]:
                    if indicator_data.signal_status == SignalStatus.BULLISH:
                        risk_on_count +=1
                    elif indicator_data.signal_status == SignalStatus.BEARISH:
                         risk_off_count +=1
            except Exception as e:
                logger.error(f"Error processing indicator {indicator_id} for market status: {e}", exc_info=True)
                neutral_count += 1
                continue
        
        total_indicators = bullish_count + bearish_count + neutral_count
        bull_bear_status_val = "NEUTRAL"
        bull_bear_score_val = 50.0
        risk_on_off_status_val = "NEUTRAL"
        risk_on_off_score_val = 50.0

        if total_indicators > 0:
            bull_ratio = bullish_count / total_indicators
            bear_ratio = bearish_count / total_indicators

            if bull_ratio > 0.6 or (bullish_count > bearish_count and bull_ratio > 0.4):
                bull_bear_status_val = "BULL"
            elif bear_ratio > 0.6 or (bearish_count > bearish_count and bear_ratio > 0.4):
                bull_bear_status_val = "BEAR"
            
            bull_bear_score_val = 50 + (bullish_count - bearish_count) * (50 / total_indicators) 
            bull_bear_score_val = max(0, min(100, bull_bear_score_val))

            total_risk_relevant_indicators = risk_on_count + risk_off_count 
            if total_risk_relevant_indicators > 0:
                if risk_on_count > risk_off_count :
                    risk_on_off_status_val = "RISK-ON"
                elif risk_off_count > risk_on_count:
                    risk_on_off_status_val = "RISK-OFF"
                
                risk_on_off_score_val = 50 + (risk_on_count - risk_off_count) * (50 / total_risk_relevant_indicators)
                risk_on_off_score_val = max(0, min(100, risk_on_off_score_val))
            else: 
                risk_on_off_status_val = "NEUTRAL"
                risk_on_off_score_val = 50.0

        logger.info(f"Market status: {bull_bear_status_val} / {risk_on_off_status_val}")
        logger.info(f"Signal breakdown: {bullish_count} bullish, {bearish_count} bearish, {neutral_count} neutral")

        return MarketStatusResponse(
            bull_bear_status=bull_bear_status_val,
            risk_on_off_status=risk_on_off_status_val,
            bull_bear_score=bull_bear_score_val,
            risk_on_off_score=risk_on_off_score_val,
            total_indicators=total_indicators,
            bullish_count=bullish_count,
            bearish_count=bearish_count,
            neutral_count=neutral_count,
            last_updated=datetime.now()
        )