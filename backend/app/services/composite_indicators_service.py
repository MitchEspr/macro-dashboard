# backend/app/services/composite_indicators_service.py

import pandas as pd
from datetime import datetime
import logging
from typing import Optional
from app.services.yahoo_finance_service import YahooFinanceService

logger = logging.getLogger(__name__)

class CompositeIndicatorsService:
    """Service for creating composite indicators from multiple data sources."""
    
    def __init__(self):
        """Initialize the composite indicators service."""
        self.yahoo_finance = YahooFinanceService()
        logger.info("CompositeIndicatorsService initialized")
    
    def get_gold_copper_ratio(self, start_date: Optional[str] = None, end_date: Optional[str] = None):
        """
        Calculate the gold/copper ratio, a key indicator of economic sentiment.
        A rising ratio indicates risk-off sentiment (gold gaining vs copper), 
        while a falling ratio indicates risk-on sentiment (copper gaining vs gold).
        
        Args:
            start_date (str, optional): Start date in YYYY-MM-DD format
            end_date (str, optional): End date in YYYY-MM-DD format
            
        Returns:
            pandas.DataFrame: DataFrame with date and ratio value columns
        """
        logger.info(f"Calculating gold/copper ratio with start_date={start_date}, end_date={end_date}")
        
        # Gold and copper tickers in Yahoo Finance
        gold_ticker = "GC=F"  # Gold Futures
        copper_ticker = "HG=F"  # Copper Futures
        
        try:
            # Get gold and copper prices using the Yahoo Finance service
            gold_df = self.yahoo_finance.get_ticker_data(gold_ticker, start_date, end_date)
            copper_df = self.yahoo_finance.get_ticker_data(copper_ticker, start_date, end_date)
            
            logger.info(f"Gold data shape: {gold_df.shape}, Copper data shape: {copper_df.shape}")
            
            if gold_df.empty:
                logger.warning("No gold price data returned from Yahoo Finance")
                return pd.DataFrame(columns=["date", "value"])
            
            if copper_df.empty:
                logger.warning("No copper price data returned from Yahoo Finance")
                return pd.DataFrame(columns=["date", "value"])
            
            # If we only have one row each, we can calculate a single ratio point
            if len(gold_df) == 1 and len(copper_df) == 1:
                logger.info("Calculating ratio from single data points")
                gold_price = gold_df.iloc[0]["value"]
                copper_price = copper_df.iloc[0]["value"]
                ratio = gold_price / copper_price
                
                logger.info(f"Gold price: {gold_price}, Copper price: {copper_price}, Ratio: {ratio}")
                
                return pd.DataFrame({
                    "date": [datetime.now()],
                    "value": [ratio]
                })
            
            # For multiple data points, merge on date and calculate ratio
            logger.info("Calculating ratio from multiple data points")
            
            # Merge the two DataFrames on date
            merged_df = pd.merge(gold_df, copper_df, on="date", suffixes=("_gold", "_copper"))
            
            # Calculate the ratio
            merged_df["value"] = merged_df["value_gold"] / merged_df["value_copper"]
            
            # Create the result DataFrame
            result_df = pd.DataFrame({
                "date": merged_df["date"],
                "value": merged_df["value"]
            })
            
            logger.info(f"Generated {len(result_df)} gold/copper ratio data points")
            if not result_df.empty:
                logger.debug(f"Ratio data sample: {result_df.head(3).to_dict('records')}")
            
            return result_df
            
        except Exception as e:
            logger.error(f"Error calculating gold/copper ratio: {e}")
            import traceback
            traceback.print_exc()
            
            # Return empty DataFrame
            return pd.DataFrame(columns=["date", "value"])
    
    def get_sp500_performance(self, start_date: Optional[str] = None, end_date: Optional[str] = None):
        """
        Get S&P 500 index performance.
        
        Args:
            start_date (str, optional): Start date in YYYY-MM-DD format
            end_date (str, optional): End date in YYYY-MM-DD format
            
        Returns:
            pandas.DataFrame: DataFrame with date and value columns
        """
        logger.info(f"Fetching S&P 500 performance with start_date={start_date}, end_date={end_date}")
        
        # S&P 500 ticker in Yahoo Finance
        sp500_ticker = "^GSPC"
        
        try:
            # Get S&P 500 data directly from Yahoo Finance service
            sp500_df = self.yahoo_finance.get_ticker_data(sp500_ticker, start_date, end_date)
            
            if sp500_df.empty:
                logger.warning("No S&P 500 data returned from Yahoo Finance")
                return pd.DataFrame(columns=["date", "value"])
            
            logger.info(f"Retrieved {len(sp500_df)} S&P 500 data points")
            return sp500_df
            
        except Exception as e:
            logger.error(f"Error fetching S&P 500 data: {e}")
            import traceback
            traceback.print_exc()
            
            # Return empty DataFrame
            return pd.DataFrame(columns=["date", "value"])