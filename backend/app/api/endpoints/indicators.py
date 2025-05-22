from fastapi import APIRouter, HTTPException, Query, Path
from app.services.fred_service import FredService
from app.services.dbnom_service import DBNomicsService
from app.services.yahoo_finance_service import YahooFinanceService
from app.services.composite_indicators_service import CompositeIndicatorsService
from app.models.indicators import TimeSeriesData, TimeSeriesPoint, IndicatorSignal
from typing import List, Optional
from datetime import datetime, timedelta
import pandas as pd


router = APIRouter()
fred_service = FredService()
dbnom_service = DBNomicsService()
yahoo_finance_service = YahooFinanceService()
composite_indicators_service = CompositeIndicatorsService()

@router.get("/fred/{series_id}", response_model=TimeSeriesData)
async def get_fred_data(
    series_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Get time series data from FRED.
    """
    # Get series info for title and other metadata
    series_info = fred_service.get_series_info(series_id)
    if not series_info:
        raise HTTPException(status_code=404, detail=f"Series {series_id} not found")
    
    # Get series data
    df = fred_service.get_series_data(series_id, start_date, end_date)
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No data found for series {series_id}")
    
    # Convert to response model
    data_points = [
        TimeSeriesPoint(date=row["date"], value=row["value"]) 
        for _, row in df.iterrows() if pd.notna(row["value"])
    ]
    
    return TimeSeriesData(
        series_id=series_id,
        title=series_info.get("title", f"FRED:{series_id}"),
        data=data_points,
        units=series_info.get("units", ""),
        frequency=series_info.get("frequency", "")
    )

@router.get("/ism/pmi", response_model=TimeSeriesData)
async def get_ism_pmi(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Get ISM Manufacturing PMI data from DBNomics.
    """
    df = dbnom_service.get_ism_pmi(start_date, end_date)
    
    if df.empty:
        raise HTTPException(status_code=404, detail="No ISM PMI data found. Please check the DBNomics API.")
    
    # Convert to response model
    data_points = [
        TimeSeriesPoint(date=row["date"], value=row["value"]) 
        for _, row in df.iterrows() if pd.notna(row["value"])
    ]
    
    return TimeSeriesData(
        series_id="ISM-PMI",
        title="ISM Manufacturing PMI",
        data=data_points,
        units="Index",
        frequency="Monthly"
    )

@router.get("/ism/new-orders", response_model=TimeSeriesData)
async def get_ism_new_orders(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Get ISM New Orders Index data from DBNomics.
    """
    df = dbnom_service.get_ism_new_orders(start_date, end_date)
    
    if df.empty:
        raise HTTPException(status_code=404, detail="No ISM New Orders data found. Please check the DBNomics API.")
    
    # Convert to response model
    data_points = [
        TimeSeriesPoint(date=row["date"], value=row["value"]) 
        for _, row in df.iterrows() if pd.notna(row["value"])
    ]
    
    return TimeSeriesData(
        series_id="ISM-NEW-ORDERS",
        title="ISM Manufacturing New Orders Index",
        data=data_points,
        units="Index",
        frequency="Monthly"
    )
    
@router.get("/dbnom/providers")
async def get_providers():
    """
    Get a list of all providers from DBNomics.
    """
    return dbnom_service.get_providers()

@router.get("/dbnom/datasets/{provider_code}")
async def get_datasets(
    provider_code: str = Path(..., description="Provider code (e.g., 'ISM')")
):
    """
    Get a list of all datasets for a provider from DBNomics.
    """
    return dbnom_service.get_datasets(provider_code)

@router.get("/dbnom/debug/{provider_code}/{dataset_code}/{series_code}")
async def debug_series(
    provider_code: str = Path(..., description="Provider code (e.g., 'ISM')"),
    dataset_code: str = Path(..., description="Dataset code (e.g., 'MAN_REPORT')"),
    series_code: str = Path(..., description="Series code (e.g., 'PMI')")
):
    """
    Debug endpoint to fetch a specific series by its components.
    """
    df = dbnom_service.get_series_by_id(provider_code, dataset_code, series_code)
    
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No data found for {provider_code}/{dataset_code}/{series_code}")
    
    # Convert DataFrame to dict for JSON response
    result = {
        "series_id": f"{provider_code}/{dataset_code}/{series_code}",
        "data": df.to_dict(orient="records"),
        "total_observations": len(df)
    }
    
    return result

@router.get("/metals/gold-copper-ratio", response_model=TimeSeriesData)
async def get_gold_copper_ratio(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Get Gold/Copper ratio data, a key indicator of economic sentiment.
    A rising ratio indicates risk-off sentiment (gold gaining vs copper), 
    while a falling ratio indicates risk-on sentiment (copper gaining vs gold).
    """
    df = composite_indicators_service.get_gold_copper_ratio(start_date, end_date)
    
    if df.empty:
        raise HTTPException(status_code=404, detail="No Gold/Copper ratio data found. Please check the API connection.")
    
    # Convert to response model
    data_points = [
        TimeSeriesPoint(date=row["date"], value=row["value"]) 
        for _, row in df.iterrows() if pd.notna(row["value"])
    ]
    
    return TimeSeriesData(
        series_id="GOLD-COPPER-RATIO",
        title="Gold/Copper Ratio",
        data=data_points,
        units="Ratio",
        frequency="Daily"
    )

@router.get("/market/sp500", response_model=TimeSeriesData)
async def get_sp500(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Get S&P 500 index data.
    The S&P 500 is a stock market index tracking the stock performance of 500 large companies
    listed on stock exchanges in the United States.
    """
    df = composite_indicators_service.get_sp500_performance(start_date, end_date)
    
    if df.empty:
        raise HTTPException(status_code=404, detail="No S&P 500 data found. Please check the API connection.")
    
    # Convert to response model
    data_points = [
        TimeSeriesPoint(date=row["date"], value=row["value"]) 
        for _, row in df.iterrows() if pd.notna(row["value"])
    ]
    
    return TimeSeriesData(
        series_id="SP500",
        title="S&P 500 Index",
        data=data_points,
        units="Price",
        frequency="Daily"
    )

@router.get("/yahoo/{ticker}", response_model=TimeSeriesData)
async def get_yahoo_ticker(
    ticker: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Get price data for any Yahoo Finance ticker.
    """
    df = yahoo_finance_service.get_ticker_data(ticker, start_date, end_date)
    
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No data found for ticker {ticker}. Please check if the ticker symbol is valid.")
    
    # Convert to response model
    data_points = [
        TimeSeriesPoint(date=row["date"], value=row["value"]) 
        for _, row in df.iterrows() if pd.notna(row["value"])
    ]
    
    return TimeSeriesData(
        series_id=f"YAHOO-{ticker}",
        title=f"{ticker} Price",
        data=data_points,
        units="Price",
        frequency="Daily"
    )