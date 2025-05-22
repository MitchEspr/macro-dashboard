# backend/app/core/indicator_config.py

from typing import Dict, List, Optional, Union, Literal
from pydantic import BaseModel
from enum import Enum

class DataSourceType(str, Enum):
    FRED = "fred"
    YAHOO = "yahoo"
    DBNOMICS_ISM = "dbnomics_ism" # Specific for ISM data via DBNomics
    CUSTOM_COMPOSITE = "custom_composite" # For indicators calculated from multiple sources

class TransformationType(str, Enum):
    NONE = "none"
    YOY = "yoy"
    INVERT = "invert"

class SignalStatus(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"

class IndicatorType(str, Enum):
    LEADING = "leading"
    COINCIDENT = "coincident"
    LAGGING = "lagging"

# --- Dynamic Threshold Configuration Models ---
class DynamicThresholdType(str, Enum):
    MOVING_AVERAGE_CROSSOVER = "moving_average_crossover"
    # Future types can be added here, e.g., BOLLINGER_BAND, PERCENTILE_RANK

class MovingAverageThresholdConfig(BaseModel):
    period: int
    ma_type: Literal["simple"] = "simple" # Could be extended to "ema" etc.

# Union for different dynamic threshold configurations
DynamicThresholdDetail = Union[MovingAverageThresholdConfig, None] # Add other config types to Union if needed

class DynamicThresholdConfig(BaseModel):
    type: DynamicThresholdType
    config: Optional[DynamicThresholdDetail] = None
# --- End Dynamic Threshold Configuration Models ---

class IndicatorMetadata(BaseModel):
    name: str
    category: str # This will be the category NAME, used to link to CategoryDefinition
    indicator_type: IndicatorType
    data_source: DataSourceType
    series_id: Optional[str] = None # For FRED, Yahoo
    # custom_endpoint: Optional[str] = None # Deprecated and removed
    
    # Static thresholds are still useful for many indicators or as fallbacks
    bullish_threshold: Optional[float] = None
    bearish_threshold: Optional[float] = None
    
    # New field for dynamic threshold logic
    dynamic_threshold: Optional[DynamicThresholdConfig] = None
    
    transformation: TransformationType
    description: Optional[str] = None
    y_axis_domain: Optional[List[float]] = None
    invert_logic: bool = False
    units: Optional[str] = None
    frequency: Optional[str] = None

class CategoryDefinition(BaseModel):
    id: str 
    name: str 
    description: str
    display_order: int

CATEGORY_DEFINITIONS_LIST: List[CategoryDefinition] = [
    CategoryDefinition(id="business-cycle-indicators", name="Business Cycle Indicators", display_order=1, description="Business cycle indicators track the expansion and contraction of the economy. ISM PMI and New Orders are particularly strong leading indicators with 3-9 month lead time."),
    CategoryDefinition(id="global-risk-metrics", name="Global Risk Metrics", display_order=2, description="Global risk metrics track investor sentiment and appetite for risk. The Gold/Copper ratio and VIX typically lead market turns by 3-6 months."),
    CategoryDefinition(id="financial-market-indicators", name="Financial Market Indicators", display_order=3, description="Financial market indicators help identify trends in equity and credit markets. The yield curve historically precedes recessions by 12-24 months."),
    CategoryDefinition(id="global-liquidity-metrics", name="Global Liquidity Metrics", display_order=4, description="Liquidity metrics track the availability of money and credit in the financial system. According to investors like Raoul Pal, liquidity drives everything in markets."),
    CategoryDefinition(id="housing-market", name="Housing Market", display_order=5, description="Housing market indicators are powerful leading indicators with 3-9 month forecast windows. Druckenmiller cites housing as a key sector to watch."),
    CategoryDefinition(id="market-sentiment", name="Market Sentiment", display_order=6, description="Market sentiment indicators track current investor mood and market participation, showing present-day risk appetite."),
    CategoryDefinition(id="economic-activity", name="Economic Activity", display_order=7, description="Economic activity indicators move simultaneously with the business cycle, reflecting current economic conditions in real-time."),
        CategoryDefinition(
        id="labor-market", 
        name="Labor Market", 
        display_order=8, 
        description="Labor market indicators track employment conditions and wage dynamics, typically lagging economic cycles by 2-6 months."
    ),
    CategoryDefinition(
        id="inflation", 
        name="Inflation", 
        display_order=9, 
        description="Inflation indicators track price pressures in the economy, helping assess Fed policy direction and purchasing power trends."
    )
]

INDICATOR_DEFINITIONS: Dict[str, IndicatorMetadata] = {
    "ISM-PMI": IndicatorMetadata(
        name="ISM Manufacturing PMI",
        category="Business Cycle Indicators", indicator_type=IndicatorType.LEADING,
        data_source=DataSourceType.DBNOMICS_ISM, # series_id not needed if data_source implies it
        bullish_threshold=50.0, bearish_threshold=45.0, transformation=TransformationType.NONE,
        y_axis_domain=[30.0, 70.0], units="Index", frequency="Monthly",
        description="ISM Manufacturing PMI is a leading indicator with 3-6 month forecast window. Above 50 indicates expansion, below 45 indicates contraction."
    ),
    "ISM-NEW-ORDERS": IndicatorMetadata(
        name="ISM Manufacturing New Orders Index",
        category="Business Cycle Indicators", indicator_type=IndicatorType.LEADING,
        data_source=DataSourceType.DBNOMICS_ISM, # series_id not needed
        bullish_threshold=50.0, bearish_threshold=45.0, transformation=TransformationType.NONE,
        y_axis_domain=[30.0, 70.0], units="Index", frequency="Monthly",
        description="ISM New Orders Index is a leading indicator with 3-9 month forecast window. More forward-looking than PMI itself."
    ),
    "M2SL": IndicatorMetadata(
        name="M2 Money Supply",
        category="Global Liquidity Metrics", indicator_type=IndicatorType.LEADING,
        data_source=DataSourceType.FRED, series_id="M2SL",
        bullish_threshold=5.0, bearish_threshold=2.0, transformation=TransformationType.YOY,
        units="Percentage", frequency="Monthly",
        description="M2 Money Supply growth is a key liquidity indicator that precedes major market moves. When M2 growth exceeds 5% YoY, it typically creates a bullish environment for risk assets."
    ),
    "HOUST": IndicatorMetadata(
        name="Housing Starts",
        category="Housing Market", indicator_type=IndicatorType.LEADING,
        data_source=DataSourceType.FRED, series_id="HOUST",
        bullish_threshold=10.0, bearish_threshold=-10.0, transformation=TransformationType.YOY,
        units="Percentage", frequency="Monthly",
        description="Housing Starts are a leading indicator with a 3-6 month forecast window. YoY growth over 10% typically indicates an expanding economy."
    ),
    "PERMIT": IndicatorMetadata(
        name="Building Permits",
        category="Housing Market", indicator_type=IndicatorType.LEADING,
        data_source=DataSourceType.FRED, series_id="PERMIT",
        bullish_threshold=15.0, bearish_threshold=-5.0, transformation=TransformationType.YOY,
        units="Percentage", frequency="Monthly",
        description="Building Permits are an even earlier indicator than Housing Starts, with a 6-9 month lead time. They represent future construction activity."
    ),
    "T10Y2Y": IndicatorMetadata(
        name="Yield Curve (10Y-2Y)",
        category="Financial Market Indicators", indicator_type=IndicatorType.LEADING,
        data_source=DataSourceType.FRED, series_id="T10Y2Y",
        bullish_threshold=0.5, bearish_threshold=0.0, transformation=TransformationType.NONE,
        units="Percentage Points", frequency="Daily",
        description="The 10Y-2Y yield spread is a powerful predictor of recessions. When negative (inverted), it has historically preceded recessions by 12-24 months."
    ),
    "BAMLH0A0HYM2": IndicatorMetadata(
        name="Credit Spreads (High Yield)",
        category="Financial Market Indicators", indicator_type=IndicatorType.LEADING,
        data_source=DataSourceType.FRED, series_id="BAMLH0A0HYM2",
        bullish_threshold=4.0, bearish_threshold=6.0, transformation=TransformationType.NONE,
        invert_logic=True, units="Percentage Points", frequency="Daily",
        description="High-yield credit spreads measure risk appetite in credit markets and typically lead equity market moves by 1-3 months. Lower spreads indicate investor confidence."
    ),
    "VIX": IndicatorMetadata(
        name="VIX (Volatility Index)",
        category="Global Risk Metrics", indicator_type=IndicatorType.LEADING,
        data_source=DataSourceType.YAHOO, series_id="^VIX",
        bullish_threshold=20.0, bearish_threshold=30.0, transformation=TransformationType.NONE,
        invert_logic=True, y_axis_domain=[10.0, 50.0], units="Index", frequency="Daily",
        description="The VIX is a real-time market estimate of expected volatility. Lower values indicate risk-on sentiment, higher values indicate fear and risk-off sentiment."
    ),
    "GOLD-COPPER-RATIO": IndicatorMetadata(
        name="Gold/Copper Ratio",
        category="Global Risk Metrics", indicator_type=IndicatorType.LEADING,
        data_source=DataSourceType.CUSTOM_COMPOSITE, # series_id not applicable
        # Static thresholds are placeholders; dynamic logic takes precedence
        bullish_threshold=0.0, bearish_threshold=0.0, 
        dynamic_threshold=DynamicThresholdConfig(
            type=DynamicThresholdType.MOVING_AVERAGE_CROSSOVER,
            config=MovingAverageThresholdConfig(period=200)
        ),
        transformation=TransformationType.NONE,
        invert_logic=True, units="Ratio", frequency="Daily",
        description="The Gold/Copper ratio is a key market sentiment indicator. A falling ratio (copper outperforming gold) signals risk-on sentiment, while a rising ratio signals risk-off."
    ),
    "SP500": IndicatorMetadata(
        name="S&P 500 Index",
        category="Market Sentiment", indicator_type=IndicatorType.COINCIDENT,
        data_source=DataSourceType.YAHOO, series_id="^GSPC",
        # Static thresholds are placeholders; dynamic logic takes precedence
        bullish_threshold=0.0, bearish_threshold=0.0, 
        dynamic_threshold=DynamicThresholdConfig(
            type=DynamicThresholdType.MOVING_AVERAGE_CROSSOVER,
            config=MovingAverageThresholdConfig(period=125)
        ),
        transformation=TransformationType.NONE, units="Price", frequency="Daily",
        description="The S&P 500 index. Signal is dynamically determined by its position relative to the 125-day simple moving average (SMA). Above SMA is bullish, below is bearish."
    ),
    "INDPRO": IndicatorMetadata(
        name="Industrial Production Index",
        category="Economic Activity", indicator_type=IndicatorType.COINCIDENT,
        data_source=DataSourceType.FRED, series_id="INDPRO",
        bullish_threshold=2.0, bearish_threshold=-2.0, transformation=TransformationType.YOY,
        units="Percentage", frequency="Monthly",
        description="Industrial Production Index measures the real output of manufacturing, mining, and utilities. YoY growth above 2% typically indicates economic expansion."
    ),
    "DXY": IndicatorMetadata(
        name="US Dollar Index (DXY)",
        category="Global Risk Metrics", 
        indicator_type=IndicatorType.LEADING,
        data_source=DataSourceType.YAHOO, 
        series_id="DX-Y.NYB",
        bullish_threshold=95.0,  # Strong dollar (risk-off for global markets)
        bearish_threshold=105.0,   # Weak dollar (risk-on for global markets)
        transformation=TransformationType.NONE,
        invert_logic=True,  # Lower DXY values are bullish for risk assets
        units="Index", 
        frequency="Daily",
        description="US Dollar Index measures the dollar against a basket of major currencies. A weakening dollar typically supports risk assets and commodities, while a strengthening dollar indicates risk-off conditions."
    ),
    "W875RX1": IndicatorMetadata(
        name="Personal Income Less Transfer Payments",
        category="Economic Activity", 
        indicator_type=IndicatorType.COINCIDENT,
        data_source=DataSourceType.FRED, 
        series_id="W875RX1",
        bullish_threshold=3.0,  # >3% YoY growth
        bearish_threshold=0.0,  # Negative growth
        transformation=TransformationType.YOY,
        units="Percentage", 
        frequency="Monthly"
    ),
    "RSXFS": IndicatorMetadata(
        name="Retail Sales Ex-Auto",
        category="Economic Activity", 
        indicator_type=IndicatorType.COINCIDENT,
        data_source=DataSourceType.FRED, 
        series_id="RSXFS",
        bullish_threshold=4.0,  # >4% YoY growth
        bearish_threshold=1.0,  # <1% growth
        transformation=TransformationType.YOY,
        units="Percentage", 
        frequency="Monthly"
    ),
    "UNRATE": IndicatorMetadata(
        name="Unemployment Rate",
        category="Labor Market", 
        indicator_type=IndicatorType.LAGGING,
        data_source=DataSourceType.FRED, 
        series_id="UNRATE",
        bullish_threshold=4.0,   # <4% = tight labor market
        bearish_threshold=6.0,   # >6% = slack
        transformation=TransformationType.NONE,
        invert_logic=True,  # Lower unemployment is bullish
        units="Percentage", 
        frequency="Monthly"
    ),

    "CPILFESL": IndicatorMetadata(
        name="Core CPI (Inflation)",
        category="Inflation", 
        indicator_type=IndicatorType.LAGGING,
        data_source=DataSourceType.FRED, 
        series_id="CPILFESL",
        bullish_threshold=3.0,   # 2-3% target range
        bearish_threshold=4.0,   # >4% high inflation
        transformation=TransformationType.YOY,
        invert_logic=True,  # Lower inflation is generally bullish for markets
        units="Percentage", 
        frequency="Monthly"
    ),

    "AHETPI": IndicatorMetadata(
        name="Average Hourly Earnings (Production Workers)",
        category="Labor Market", 
        indicator_type=IndicatorType.LAGGING,
        data_source=DataSourceType.FRED, 
        series_id="AHETPI",
        bullish_threshold=4.0,   # >4% YoY wage inflation pressure
        bearish_threshold=2.0,   # <2% weak wage growth
        transformation=TransformationType.YOY,
        units="Percentage", 
        frequency="Monthly"
    ),
    "UMCSENT": IndicatorMetadata(
        name="University of Michigan Consumer Sentiment",
        category="Business Cycle Indicators", 
        indicator_type=IndicatorType.LEADING,
        data_source=DataSourceType.FRED, 
        series_id="UMCSENT",
        bullish_threshold=90.0,   # >90 indicates strong confidence
        bearish_threshold=70.0,   # <70 indicates weak confidence  
        transformation=TransformationType.NONE,
        units="Index", 
        frequency="Monthly",
        description="University of Michigan Consumer Sentiment Index measures consumer confidence and future spending intentions. As a leading indicator with 3-6 month forecast window, it predicts retail sales and GDP growth. Readings above 90 typically signal economic optimism."
    ),
    
    "DGS5": IndicatorMetadata(
        name="5-Year Treasury Constant Maturity Rate",
        category="Financial Market Indicators", 
        indicator_type=IndicatorType.LEADING,
        data_source=DataSourceType.FRED, 
        series_id="DGS5",
        bullish_threshold=3.5,    # Normal/rising rates in expansion
        bearish_threshold=2.0,    # Very low rates signal easing/recession fears
        transformation=TransformationType.NONE,
        units="Percentage", 
        frequency="Daily",
        description="5-Year Treasury yield reflects medium-term interest rate expectations and Fed policy outlook. Rising yields often precede economic acceleration, while falling yields signal growth concerns or easing expectations."
    ),
    
    # === COINCIDENT INDICATORS ===
    
    "GDP": IndicatorMetadata(
        name="Gross Domestic Product",
        category="Economic Activity", 
        indicator_type=IndicatorType.LAGGING,
        data_source=DataSourceType.FRED, 
        series_id="GDP",
        bullish_threshold=3.0,    # >3% YoY growth is strong
        bearish_threshold=1.0,    # <1% growth is weak
        transformation=TransformationType.YOY,
        units="Percentage", 
        frequency="Quarterly",
        description="GDP measures the total economic output and is the definitive measure of economic activity. YoY growth above 3% indicates strong expansion, while growth below 1% suggests economic weakness."
    ),
    
    "WTI_OIL": IndicatorMetadata(
        name="WTI Crude Oil Price",
        category="Global Risk Metrics", 
        indicator_type=IndicatorType.COINCIDENT,
        data_source=DataSourceType.YAHOO, 
        series_id="CL=F",
        bullish_threshold=80.0,   # Higher oil = economic strength (demand-driven)
        bearish_threshold=60.0,   # Lower oil could signal demand weakness
        transformation=TransformationType.NONE,
        units="USD per Barrel", 
        frequency="Daily",
        description="WTI Crude Oil price reflects global economic demand and geopolitical risk. Rising oil prices can signal economic strength (demand-driven) but also pose inflation risks. Context matters for interpretation."
    ),
    
    # === MARKET SENTIMENT INDICATORS (Coincident with market cycles) ===
    
    "NASDAQ": IndicatorMetadata(
        name="NASDAQ Composite Index",
        category="Market Sentiment", 
        indicator_type=IndicatorType.COINCIDENT,
        data_source=DataSourceType.YAHOO, 
        series_id="^IXIC",
        # Dynamic thresholds based on 200-day moving average
        bullish_threshold=0.0,    # Above 200-day MA
        bearish_threshold=0.0,    # Below 200-day MA
        dynamic_threshold=DynamicThresholdConfig(
            type=DynamicThresholdType.MOVING_AVERAGE_CROSSOVER,
            config=MovingAverageThresholdConfig(period=200)
        ),
        transformation=TransformationType.NONE,
        units="Index Value", 
        frequency="Daily",
        description="NASDAQ Composite Index is heavily weighted toward technology and growth stocks. It reflects risk appetite for growth assets and liquidity conditions. Position relative to 200-day MA indicates trend."
    ),
    
    "RUSSELL2000": IndicatorMetadata(
        name="Russell 2000 Small Cap Index",
        category="Market Sentiment", 
        indicator_type=IndicatorType.COINCIDENT,
        data_source=DataSourceType.YAHOO, 
        series_id="^RUT",
        # Dynamic thresholds based on 200-day moving average
        bullish_threshold=0.0,    # Above 200-day MA
        bearish_threshold=0.0,    # Below 200-day MA
        dynamic_threshold=DynamicThresholdConfig(
            type=DynamicThresholdType.MOVING_AVERAGE_CROSSOVER,
            config=MovingAverageThresholdConfig(period=200)
        ),
        transformation=TransformationType.NONE,
        units="Index Value", 
        frequency="Daily",
        description="Russell 2000 tracks small-cap US stocks, which are more sensitive to domestic economic conditions and credit availability. Strong performance indicates healthy domestic economy and risk appetite."
    ),
    
    "USDJPY": IndicatorMetadata(
        name="USD/JPY Exchange Rate",
        category="Global Risk Metrics", 
        indicator_type=IndicatorType.LEADING,
        data_source=DataSourceType.YAHOO, 
        series_id="JPY=X",
        bullish_threshold=140.0,  # Strong USD/weak JPY = risk-on
        bearish_threshold=120.0,  # Weak USD/strong JPY = risk-off (yen strengthening)
        transformation=TransformationType.NONE,
        invert_logic=False,  # Higher USD/JPY is typically risk-on
        units="JPY per USD", 
        frequency="Daily",
        description="USD/JPY exchange rate is a key risk sentiment indicator. Yen strength (lower USD/JPY) typically signals risk-off conditions as investors flee to safety, while yen weakness indicates risk-on sentiment."
    ),
    "FEDFUNDS": IndicatorMetadata(
        name="Federal Funds Target Rate",
        category="Financial Market Indicators", 
        indicator_type=IndicatorType.LEADING,
        data_source=DataSourceType.FRED, 
        series_id="FEDFUNDS",
        bullish_threshold=2.0,    # Normal/neutral rate environment
        bearish_threshold=5.0,    # Restrictive territory (market negative)
        transformation=TransformationType.NONE,
        invert_logic=True,  # Lower rates are generally bullish for risk assets
        units="Percentage", 
        frequency="Monthly",
        description="Federal Funds Target Rate is the most important price in global markets. Lower rates boost liquidity and risk asset prices, while higher rates restrict growth and pressure valuations. Rate changes lead economic cycles by 12-18 months."
    ),
    "BITCOIN": IndicatorMetadata(
        name="Bitcoin (BTC/USD)",
        category="Global Liquidity Metrics", 
        indicator_type=IndicatorType.LEADING,
        data_source=DataSourceType.YAHOO, 
        series_id="BTC-USD",
        # Dynamic thresholds based on 200-day moving average (institutional standard)
        bullish_threshold=0.0,    # Above 200-day MA
        bearish_threshold=0.0,    # Below 200-day MA
        dynamic_threshold=DynamicThresholdConfig(
            type=DynamicThresholdType.MOVING_AVERAGE_CROSSOVER,
            config=MovingAverageThresholdConfig(period=200)
        ),
        transformation=TransformationType.NONE,
        units="USD", 
        frequency="Daily",
        description="Bitcoin is now 'the ultimate macro asset' with 0.94 correlation to global liquidity. It's the purest expression of global liquidity conditions, leading risk-on/risk-off cycles by 3-6 months. Institutional adoption via ETFs has made it a critical macro indicator for global capital flows and monetary policy effects."
    )
}

# --- Helper functions ---
def get_indicator_metadata(indicator_id: str) -> Optional[IndicatorMetadata]:
    return INDICATOR_DEFINITIONS.get(indicator_id)

def get_all_indicators() -> Dict[str, IndicatorMetadata]:
    return INDICATOR_DEFINITIONS

def get_sorted_categories() -> List[CategoryDefinition]:
    return sorted(CATEGORY_DEFINITIONS_LIST, key=lambda cat: cat.display_order)

def get_category_by_name(name: str) -> Optional[CategoryDefinition]:
    for cat_def in CATEGORY_DEFINITIONS_LIST:
        if cat_def.name == name:
            return cat_def
    return None

def get_indicators_by_category_name(category_name: str) -> Dict[str, IndicatorMetadata]:
    return {
        indicator_id: metadata
        for indicator_id, metadata in INDICATOR_DEFINITIONS.items()
        if metadata.category == category_name
    }

def get_indicators_by_type(indicator_type: IndicatorType) -> Dict[str, IndicatorMetadata]:
    return {
        indicator_id: metadata
        for indicator_id, metadata in INDICATOR_DEFINITIONS.items()
        if metadata.indicator_type == indicator_type
    }

