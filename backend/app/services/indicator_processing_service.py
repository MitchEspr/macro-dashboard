# backend/app/services/indicator_processing_service.py

import pandas as pd
from typing import List, Optional, Tuple
from datetime import datetime
import logging
from app.core.indicator_config import (
    IndicatorMetadata,
    TransformationType,
    SignalStatus,
    DynamicThresholdType, 
    MovingAverageThresholdConfig, 
    get_indicator_metadata
)
from app.models.indicators import TimeSeriesPoint, EnrichedIndicatorData 

logger = logging.getLogger(__name__)

class IndicatorProcessingService:
    """Service for processing and enriching indicator data with transformations and signals."""

    @staticmethod
    def calculate_yoy_growth(data: List[TimeSeriesPoint]) -> List[TimeSeriesPoint]:
        if not data or len(data) < 13:
            # logger.warning("Insufficient data for YoY calculation (need at least 13 points or data is empty)")
            return []
        
        df = pd.DataFrame([{"date": point.date, "value": point.value} for point in data])
        if df.empty:
            return []
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').set_index('date')
        
        df_resampled = df.resample('ME').last()
        df_resampled['yoy_growth'] = df_resampled['value'].pct_change(periods=12) * 100
        
        result = []
        for date, row in df_resampled.iterrows():
            if pd.notna(row['yoy_growth']):
                result.append(TimeSeriesPoint(date=date, value=round(row['yoy_growth'], 2)))
        
        # logger.info(f"Calculated YoY growth for {len(result)} data points")
        return result

    @staticmethod
    def calculate_moving_average(
        data: List[TimeSeriesPoint], 
        period: int,
        ma_type: str = "simple",
        indicator_id: Optional[str] = None # Added indicator_id as a parameter
    ) -> List[TimeSeriesPoint]:
        if not data or len(data) < period:
            logger.warning(f"IndicatorProcessingService ({indicator_id if indicator_id else 'Unknown'}): Insufficient data for {period}-period MA. Have {len(data)}, need {period}.")
            return []

        df = pd.DataFrame([{"date": point.date, "value": point.value} for point in data])
        if df.empty:
            return []
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')

        if ma_type == "simple":
            df['ma'] = df['value'].rolling(window=period, min_periods=period).mean()
        else:
            logger.warning(f"Unsupported MA type: {ma_type} for indicator {indicator_id if indicator_id else 'Unknown'}. Defaulting to simple moving average.")
            df['ma'] = df['value'].rolling(window=period, min_periods=period).mean()
            
        result = []
        for _, row in df.iterrows():
            if pd.notna(row['ma']):
                result.append(TimeSeriesPoint(date=row['date'], value=round(row['ma'], 2)))
        
        logger.info(f"IndicatorProcessingService ({indicator_id if indicator_id else 'Unknown'}): Calculated {period}-period {ma_type} MA. Result length: {len(result)}. Input data length: {len(data)}")
        if indicator_id == 'SP500' and len(result) > 0:
            logger.debug(f"[SP500 MA DEBUG] First 3 MA points: {result[:3]}")
            logger.debug(f"[SP500 MA DEBUG] Last 3 MA points: {result[-3:]}")
        return result
    
    # Removed the class-level/module-level indicator_id_for_debug variable
    # indicator_id_for_debug: Optional[str] = None 


    @staticmethod
    def invert_values(data: List[TimeSeriesPoint]) -> List[TimeSeriesPoint]:
        if not data: return []
        result = [TimeSeriesPoint(date=point.date, value=-point.value) for point in data]
        # logger.info(f"Inverted values for {len(result)} data points")
        return result

    @staticmethod
    def apply_transformation(
        data: List[TimeSeriesPoint],
        transformation: TransformationType,
        metadata: IndicatorMetadata
    ) -> Tuple[List[TimeSeriesPoint], str, str]:
        transformed_data = data.copy() 
        title = metadata.name
        units = metadata.units or ""

        if not data: 
            # logger.warning(f"Cannot apply transformation for {metadata.name} as raw data is empty.")
            return [], title, units

        if transformation == TransformationType.YOY:
            yoy_data = IndicatorProcessingService.calculate_yoy_growth(data)
            if yoy_data: 
                transformed_data = yoy_data
                title = f"{metadata.name} (YoY % Change)"
                units = "% YoY"
            # else: 
                # logger.warning(f"YoY transformation failed for {metadata.name}, returning original data.")
        elif transformation == TransformationType.INVERT:
            transformed_data = IndicatorProcessingService.invert_values(data)
            title = f"{metadata.name} (Inverted)"
        
        return transformed_data, title, units

    @staticmethod
    def _determine_static_signal_status(
        value: Optional[float],
        bullish_threshold: Optional[float], 
        bearish_threshold: Optional[float], 
        invert_logic: bool = False
    ) -> SignalStatus:
        if value is None or bullish_threshold is None or bearish_threshold is None:
            return SignalStatus.NEUTRAL
        
        if invert_logic:
            if value <= bullish_threshold: return SignalStatus.BULLISH
            if value >= bearish_threshold: return SignalStatus.BEARISH
        else:
            if value >= bullish_threshold: return SignalStatus.BULLISH
            if value <= bearish_threshold: return SignalStatus.BEARISH
        return SignalStatus.NEUTRAL

    @staticmethod
    def _calculate_moving_average_crossover_signal(
        indicator_id: str, 
        data: List[TimeSeriesPoint], 
        ma_config: MovingAverageThresholdConfig
    ) -> Tuple[Optional[float], Optional[float], SignalStatus, Optional[float], List[TimeSeriesPoint]]:
        ma_series_data: List[TimeSeriesPoint] = [] 

        if not data or len(data) < ma_config.period:
            logger.warning(f"[{indicator_id}] Insufficient data for {ma_config.period}-period MA crossover signal. Data length: {len(data)}")
            return None, None, SignalStatus.NEUTRAL, None, ma_series_data

        # Pass indicator_id to calculate_moving_average for logging context
        ma_series_data = IndicatorProcessingService.calculate_moving_average(data, ma_config.period, ma_config.ma_type, indicator_id=indicator_id)
        
        if not ma_series_data: 
            logger.warning(f"[{indicator_id}] MA series calculation failed or resulted in empty list. Original data length: {len(data)}")
            return None, None, SignalStatus.NEUTRAL, None, [] 

        if not data: 
             logger.warning(f"[{indicator_id}] Original data is empty after MA calculation attempt, this should not happen.")
             return None, None, SignalStatus.NEUTRAL, None, ma_series_data


        last_price_point = data[-1]
        last_ma_point = ma_series_data[-1] 

        if last_ma_point is None or last_price_point is None: 
            logger.warning(f"[{indicator_id}] Could not get last price or MA value for crossover signal despite MA series being present.")
            return None, None, SignalStatus.NEUTRAL, None, ma_series_data

        last_value = last_price_point.value
        ma_value = last_ma_point.value
        
        signal = SignalStatus.NEUTRAL
        if last_value > ma_value:
            signal = SignalStatus.BULLISH
        elif last_value < ma_value:
            signal = SignalStatus.BEARISH
        
        logger.info(f"[{indicator_id}] MA Crossover: Last value {last_value}, MA({ma_config.period}) {ma_value}, Signal: {signal.value}. MA Series Length: {len(ma_series_data)}")
        if indicator_id == 'SP500':
            logger.debug(f"[SP500 _calculate_moving_average_crossover_signal] Returning MA series of length: {len(ma_series_data)}")
            if ma_series_data:
                 logger.debug(f"[SP500 _calculate_moving_average_crossover_signal] First 3 MA points returned: {ma_series_data[:3]}")

        return ma_value, ma_value, signal, ma_value, ma_series_data


    @staticmethod
    def process_indicator_data(
        indicator_id: str,
        raw_data: List[TimeSeriesPoint],
        original_title: str, 
        original_units: Optional[str] = None,
        original_frequency: Optional[str] = None
    ) -> EnrichedIndicatorData:
        metadata = get_indicator_metadata(indicator_id)
        if not metadata:
            logger.error(f"No metadata found for indicator {indicator_id}")
            return EnrichedIndicatorData(
                indicator_id=indicator_id, title=original_title, data=[],
                category="Unknown", bullish_threshold=0.0, bearish_threshold=0.0,
                signal_status=SignalStatus.NEUTRAL, description="Metadata not found."
            )
        
        if indicator_id == 'SP500':
            logger.debug(f"[SP500 process_indicator_data] Raw data length for SP500: {len(raw_data)}")
            if raw_data:
                logger.debug(f"[SP500 process_indicator_data] First 3 raw_data points for SP500: {raw_data[:3]}")


        display_data, processed_title, processed_units = IndicatorProcessingService.apply_transformation(
            raw_data.copy(), metadata.transformation, metadata
        )

        if not display_data: 
            logger.warning(f"No data after transformation for {indicator_id}. Using raw data for display if available, or empty.")
            display_data = raw_data if raw_data else []
            
        last_display_value: Optional[float] = None
        last_updated_date: Optional[datetime] = None
        if display_data:
            last_display_value = display_data[-1].value
            last_updated_date = display_data[-1].date

        bullish_thresh = metadata.bullish_threshold
        bearish_thresh = metadata.bearish_threshold
        signal_status = SignalStatus.NEUTRAL
        ma_series_for_response: Optional[List[TimeSeriesPoint]] = None 
        
        if metadata.dynamic_threshold:
            if indicator_id == 'SP500':
                logger.debug(f"[SP500 process_indicator_data] Processing dynamic threshold for SP500.")
            if metadata.dynamic_threshold.type == DynamicThresholdType.MOVING_AVERAGE_CROSSOVER:
                if isinstance(metadata.dynamic_threshold.config, MovingAverageThresholdConfig):
                    bt, brt, sig, ma_val, calculated_ma_series = IndicatorProcessingService._calculate_moving_average_crossover_signal(
                        indicator_id, 
                        raw_data, 
                        metadata.dynamic_threshold.config
                    )
                    bullish_thresh = ma_val 
                    bearish_thresh = ma_val
                    signal_status = sig
                    ma_series_for_response = calculated_ma_series 
                    if indicator_id == 'SP500':
                        logger.debug(f"[SP500 process_indicator_data] calculated_ma_series length: {len(calculated_ma_series if calculated_ma_series else [])}")
                        if ma_series_for_response:
                             logger.debug(f"[SP500 process_indicator_data] ma_series_for_response first 3: {ma_series_for_response[:3]}")
                else:
                    logger.error(f"Invalid config for MOVING_AVERAGE_CROSSOVER on {indicator_id}")
                    signal_status = IndicatorProcessingService._determine_static_signal_status(
                        last_display_value, bullish_thresh, bearish_thresh, metadata.invert_logic
                    )
        else: 
            signal_status = IndicatorProcessingService._determine_static_signal_status(
                last_display_value, bullish_thresh, bearish_thresh, metadata.invert_logic
            )
        
        if indicator_id == 'SP500':
            logger.debug(f"[SP500 process_indicator_data] Final ma_series_for_response length before return: {len(ma_series_for_response if ma_series_for_response else [])}")

        return EnrichedIndicatorData(
            indicator_id=indicator_id,
            title=processed_title, 
            data=display_data,    
            units=processed_units,
            frequency=metadata.frequency or original_frequency, 
            category=metadata.category,
            description=metadata.description,
            bullish_threshold=bullish_thresh if bullish_thresh is not None else 0.0, 
            bearish_threshold=bearish_thresh if bearish_thresh is not None else 0.0, 
            signal_status=signal_status,
            last_value=last_display_value, 
            last_updated=last_updated_date,
            y_axis_domain=metadata.y_axis_domain,
            ma_series_data=ma_series_for_response 
        )

