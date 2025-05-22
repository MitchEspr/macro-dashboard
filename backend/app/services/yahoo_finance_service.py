# backend/app/services/yahoo_finance_service.py

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import logging
import traceback

logger = logging.getLogger(__name__)

class YahooFinanceService:
    """Service for fetching price data using Yahoo Finance."""
    
    def __init__(self):
        """Initialize the Yahoo Finance service."""
        logger.info("YahooFinanceService initialized")
    
    def get_ticker_data(self, ticker_symbol: str, start_date=None, end_date=None):
        """
        Fetch ticker price data from Yahoo Finance.
        
        Args:
            ticker_symbol (str): The Yahoo Finance ticker symbol
            start_date (str, optional): Start date in YYYY-MM-DD format
            end_date (str, optional): End date in YYYY-MM-DD format
            
        Returns:
            pandas.DataFrame: DataFrame with date and value columns
        """
        logger.info(f"Fetching price data for ticker {ticker_symbol} from Yahoo Finance with start_date={start_date}, end_date={end_date}")
        
        try:
            # Convert string dates to datetime if provided
            start_dt = pd.to_datetime(start_date) if start_date else datetime.now() - timedelta(days=30)
            end_dt = pd.to_datetime(end_date) if end_date else datetime.now()
            
            # Fetch price data from Yahoo Finance
            logger.info(f"Fetching data for {ticker_symbol} from {start_dt} to {end_dt}")
            ticker_data = yf.download(ticker_symbol, start=start_dt, end=end_dt)
            
            # Check if data was returned
            if ticker_data.empty:
                logger.warning(f"No data returned from Yahoo Finance for {ticker_symbol}")
                return pd.DataFrame(columns=["date", "value"])
            
            # Log data sample for debugging at debug level
            logger.debug(f"Data shape: {ticker_data.shape}, columns: {ticker_data.columns.tolist()}")
            logger.debug(f"Data sample:\n{ticker_data.head(3).to_string()}")
            
            # Extract the closing prices and create a new DataFrame
            try:
                # Handle different column structures (could be multi-level)
                if isinstance(ticker_data.columns, pd.MultiIndex):
                    logger.debug(f"{ticker_symbol} data has multi-level columns")
                    close_cols = [col for col in ticker_data.columns if isinstance(col, tuple) and col[0] == 'Close']
                    if close_cols:
                        close_col = close_cols[0]
                    else:
                        logger.warning(f"Couldn't find 'Close' column in multi-level columns for {ticker_symbol}")
                        close_col = ticker_data.columns[0]  # Fall back to first column
                else:
                    close_col = 'Close'
                
                # Create a DataFrame with the date index and Close column value
                df = pd.DataFrame()
                df["date"] = ticker_data.index
                df["value"] = ticker_data[close_col].values
                
                logger.info(f"Successfully processed {len(df)} price data points for {ticker_symbol}")
                return df
                
            except Exception as e:
                logger.error(f"Error processing {ticker_symbol} data: {e}")
                traceback.print_exc()
                
                # Fallback: try a simpler approach with just the last data point
                logger.debug("Trying fallback method for ticker data")
                try:
                    latest_date = ticker_data.index[-1]
                    if isinstance(ticker_data.columns, pd.MultiIndex):
                        close_cols = [col for col in ticker_data.columns if isinstance(col, tuple) and col[0] == 'Close']
                        if close_cols:
                            latest_close = ticker_data.loc[latest_date, close_cols[0]]
                        else:
                            latest_close = ticker_data.iloc[-1, 0]  # Just get the first column's last value
                    else:
                        latest_close = ticker_data.loc[latest_date, 'Close']
                    
                    # Make sure we have a scalar value
                    if hasattr(latest_close, 'item'):
                        latest_close = latest_close.item()
                    
                    logger.debug(f"Fallback: Latest price at {latest_date}: {latest_close}")
                    
                    return pd.DataFrame({
                        "date": [latest_date],
                        "value": [latest_close]
                    })
                    
                except Exception as e2:
                    logger.error(f"Fallback method for {ticker_symbol} data failed: {e2}")
                    traceback.print_exc()
                    return pd.DataFrame(columns=["date", "value"])
            
        except Exception as e:
            logger.error(f"Error fetching price data for {ticker_symbol}: {e}")
            traceback.print_exc()
            return pd.DataFrame(columns=["date", "value"])