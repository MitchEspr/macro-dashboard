# backend/app/models/indicators.py

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.core.indicator_config import SignalStatus

class TimeSeriesPoint(BaseModel):
    date: datetime
    value: float

class TimeSeriesData(BaseModel):
    series_id: str
    title: str
    data: List[TimeSeriesPoint]
    units: Optional[str] = None
    frequency: Optional[str] = None

# Legacy model for backward compatibility
class IndicatorSignal(BaseModel):
    indicator_name: str
    indicator_value: float
    signal: str  # "bullish", "bearish", or "neutral"
    signal_threshold_bullish: float
    signal_threshold_bearish: float
    last_updated: datetime
    chart_data: List[TimeSeriesPoint]
    metadata: Optional[dict] = None

class EnrichedIndicatorData(BaseModel):
    """Enriched indicator data with transformations, signals, and metadata."""
    indicator_id: str
    title: str
    data: List[TimeSeriesPoint] # Primary data series (e.g., price, transformed value)
    units: Optional[str] = None
    frequency: Optional[str] = None
    category: str 
    description: Optional[str] = None
    bullish_threshold: float
    bearish_threshold: float
    signal_status: SignalStatus
    last_value: Optional[float] = None
    last_updated: Optional[datetime] = None
    y_axis_domain: Optional[List[float]] = None
    ma_series_data: Optional[List[TimeSeriesPoint]] = None # New field for MA line data

class IndicatorMetadataResponse(BaseModel):
    """Response model for indicator metadata."""
    indicator_id: str
    name: str
    category: str
    data_source: str
    description: Optional[str] = None
    units: Optional[str] = None
    frequency: Optional[str] = None

class CategoryInfo(BaseModel):
    """Information about an indicator category."""
    category_id: str 
    name: str
    description: str
    indicators: List[str]

class MarketStatusResponse(BaseModel):
    """Overall market status calculation."""
    bull_bear_status: str
    risk_on_off_status: str
    bull_bear_score: float
    risk_on_off_score: float
    total_indicators: int
    bullish_count: int
    bearish_count: int
    neutral_count: int
    last_updated: datetime

class IndicatorsByTypeResponse(BaseModel):
    """Response model for fetching indicators by their type (e.g., leading, coincident)."""
    indicator_type: str
    indicators: List[EnrichedIndicatorData]
    categories: List[CategoryInfo]
