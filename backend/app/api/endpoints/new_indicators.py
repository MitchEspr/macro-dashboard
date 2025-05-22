# backend/app/api/endpoints/new_indicators.py

from fastapi import APIRouter, HTTPException, Query, Path
from typing import List, Optional
from app.services.unified_indicator_service import UnifiedIndicatorService
from app.models.indicators import (
    EnrichedIndicatorData,
    IndicatorMetadataResponse,
    CategoryInfo,
    MarketStatusResponse,
    IndicatorsByTypeResponse
)
from app.core.indicator_config import IndicatorType # For path parameter validation

router = APIRouter()
unified_service = UnifiedIndicatorService()

@router.get("/", response_model=List[IndicatorMetadataResponse])
async def get_all_indicators_metadata_list():
    """
    Get metadata for all available indicators.
    The order is determined by their definition in indicator_config.py.
    """
    try:
        # unified_service.get_all_indicators_metadata() now returns an ordered list
        return unified_service.get_all_indicators_metadata()
    except Exception as e:
        logger.error(f"Error fetching indicators metadata: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching indicators metadata: {str(e)}")

@router.get("/categories", response_model=List[CategoryInfo])
async def get_categories():
    """
    Get all available categories with their defined indicators.
    Categories are sorted by 'display_order'. Indicators within each category
    are sorted by their definition order in indicator_config.py.
    """
    try:
        # unified_service.get_categories() now returns an ordered list of CategoryInfo
        return unified_service.get_categories()
    except Exception as e:
        logger.error(f"Error fetching categories: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching categories: {str(e)}")

@router.get("/market-status", response_model=MarketStatusResponse)
async def get_market_status(
    indicators: Optional[str] = Query(None, description="Comma-separated list of indicator IDs to use")
):
    """
    Calculate overall market status based on multiple indicators.
    If 'indicators' query param is not provided, uses all indicators in their definition order.
    """
    try:
        indicator_list = None
        if indicators:
            indicator_list = [ind.strip() for ind in indicators.split(",")]

        return unified_service.calculate_market_status(indicator_list)
    except Exception as e:
        logger.error(f"Error calculating market status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error calculating market status: {str(e)}")

@router.get("/type/{indicator_type_value}", response_model=IndicatorsByTypeResponse)
async def get_indicators_by_type_endpoint( # Renamed for clarity
    indicator_type_value: str = Path(..., description="The type of indicators to fetch (e.g., 'leading', 'coincident', 'lagging')"),
    start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format")
):
    """
    Get all indicators of a specific type (leading, coincident, or lagging)
    along with their data and relevant categories.
    Indicators and categories are ordered as defined in the configuration.
    """
    try:
        indicator_type_enum = IndicatorType(indicator_type_value.lower())
    except ValueError:
        valid_types = ", ".join([it.value for it in IndicatorType])
        logger.warning(f"Invalid indicator type requested: {indicator_type_value}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid indicator type '{indicator_type_value}'. Valid types are: {valid_types}."
        )
    
    try:
        # unified_service.get_enriched_indicators_by_type() returns an IndicatorsByTypeResponse
        # with ordered lists of indicators and categories.
        return unified_service.get_enriched_indicators_by_type(indicator_type_enum, start_date, end_date)
    except ValueError as e: 
        logger.error(f"Value error for indicator type '{indicator_type_value}': {e}", exc_info=True)
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching indicators by type '{indicator_type_value}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching indicators by type '{indicator_type_value}': {str(e)}")


@router.get("/{indicator_id}", response_model=EnrichedIndicatorData)
async def get_indicator_data( 
    indicator_id: str,
    start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format")
):
    """
    Get enriched indicator data with transformations and signals for a single indicator.
    """
    try:
        return unified_service.get_indicator(indicator_id, start_date, end_date)
    except ValueError as e: 
        logger.warning(f"Indicator not found (ValueError): {indicator_id}, Error: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching indicator {indicator_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching indicator {indicator_id}: {str(e)}")

@router.get("/{indicator_id}/metadata", response_model=IndicatorMetadataResponse)
async def get_indicator_metadata_item( 
    indicator_id: str
):
    """
    Get metadata for a specific indicator.
    """
    try:
        return unified_service.get_indicator_metadata(indicator_id)
    except ValueError as e:
        logger.warning(f"Metadata not found for indicator (ValueError): {indicator_id}, Error: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching metadata for {indicator_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching metadata for {indicator_id}: {str(e)}")

@router.get("/categorydata/{category_name}", response_model=List[EnrichedIndicatorData]) # Changed path slightly for clarity
async def get_indicators_by_category_name_list( 
    category_name: str, 
    start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format")
):
    """
    Get all enriched indicators in a specific category by the category's name.
    Indicators are returned in their definition order from indicator_config.py.
    """
    try:
        # unified_service.get_indicators_by_category_name() returns an ordered list
        indicators = unified_service.get_indicators_by_category_name(category_name, start_date, end_date)
        # No specific error if category exists but has no indicators; an empty list is valid.
        return indicators
    except Exception as e:
        logger.error(f"Error fetching indicators for category '{category_name}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching indicators for category '{category_name}': {str(e)}")

# Add logger to this file if not already present at the top
import logging
logger = logging.getLogger(__name__)
