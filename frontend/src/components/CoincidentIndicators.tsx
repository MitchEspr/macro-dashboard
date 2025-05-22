import React, { useEffect, useState, useRef, useCallback, useMemo } from 'react';
import { 
  Typography, 
  Box, 
  Button
} from '@mui/material';
import { IndicatorData } from './IndicatorCard';
import IndicatorService from '../services/IndicatorService';
import { useIndicators } from '../context/IndicatorContext';
import CategoryHeader from './CategoryHeader';
import CategoryNavigation from './CategoryNavigation';
import IndicatorSection from './IndicatorSection';

const CoincidentIndicators: React.FC = () => {
  const { setIndicator } = useIndicators();
  const setIndicatorRef = useRef(setIndicator);
  
  // Update the ref when setIndicator changes
  useEffect(() => {
    setIndicatorRef.current = setIndicator;
  }, [setIndicator]);
  
  // State for S&P 500
  const [sp500Data, setSp500Data] = useState<IndicatorData | null>(null);
  const [sp500Loading, setSp500Loading] = useState<boolean>(true);
  const [sp500Error, setSp500Error] = useState<string | null>(null);
  
  // FRED series states for coincident indicators
  const [fredSeriesStates, setFredSeriesStates] = useState<{
    [seriesId: string]: {
      data: IndicatorData | null;
      loading: boolean;
      error: string | null;
    }
  }>({});
  
  // Flag to prevent automatic re-fetching
  const [hasInitiallyLoaded, setHasInitiallyLoaded] = useState<boolean>(false);
  
  // Define coincident indicators
  const coincidentIndicatorSeries = useMemo(() => [
    'INDPRO'  // Industrial Production Index
  ], []);
  
  // Categories for coincident indicators
  const categories = useMemo(() => [
    { id: 'market-sentiment', name: 'Market Sentiment' },
    { id: 'economic-activity', name: 'Economic Activity' }
  ], []);
  
  // Category descriptions
  const categoryDescriptions = useMemo(() => ({
    'economic-activity': 'Economic activity indicators move simultaneously with the business cycle, reflecting current economic conditions in real-time.',
    'market-sentiment': 'Market sentiment indicators track current investor mood and market participation, showing present-day risk appetite.'
  }), []);
  
  // Calculate the date range (last 4 years)
  const dateRange = useMemo(() => {
    const endDate = new Date();
    const formattedEndDate = endDate.toISOString().split('T')[0];
    
    const startDate = new Date();
    startDate.setFullYear(endDate.getFullYear() - 4);
    const formattedStartDate = startDate.toISOString().split('T')[0];
    
    return {
      startDate: formattedStartDate,
      endDate: formattedEndDate
    };
  }, []);

  // Fetch indicators on component mount
  useEffect(() => {
    if (!hasInitiallyLoaded) {
      const fetchCoincidentIndicators = async () => {
        
        // Fetch S&P 500
        try {
          setSp500Loading(true);
          const data = await IndicatorService.getSP500Data(dateRange.startDate, dateRange.endDate);
          setSp500Data(data);
          setIndicatorRef.current('SP500', data);
          setSp500Error(null);
        } catch (error) {
          console.error('Error fetching S&P 500 data:', error);
          setSp500Error('Failed to load S&P 500 data');
        } finally {
          setSp500Loading(false);
        }
        
        // Initialize FRED series states
        const initialFredStates = {} as any;
        coincidentIndicatorSeries.forEach(seriesId => {
          initialFredStates[seriesId] = {
            data: null,
            loading: true,
            error: null
          };
        });
        setFredSeriesStates(initialFredStates);
        
        // Fetch FRED series in parallel
        const fredPromises = coincidentIndicatorSeries.map(async (seriesId) => {
          try {
            const data = await IndicatorService.getFREDData(seriesId, dateRange.startDate, dateRange.endDate);
            setIndicatorRef.current(`FRED-${seriesId}`, data);
            return { seriesId, data, error: null };
          } catch (error) {
            console.error(`Error fetching FRED data for ${seriesId}:`, error);
            return { seriesId, data: null, error: `Failed to load ${seriesId} data from FRED` };
          }
        });
        
        // Update states for all FRED series
        const results = await Promise.all(fredPromises);
        const newFredStates = { ...initialFredStates };
        
        results.forEach(({ seriesId, data, error }) => {
          newFredStates[seriesId] = {
            data,
            loading: false,
            error
          };
        });
        
        setFredSeriesStates(newFredStates);
        setHasInitiallyLoaded(true);
      };
      
      fetchCoincidentIndicators();
    }
  }, [dateRange, coincidentIndicatorSeries, hasInitiallyLoaded]);
  
  // Refresh all data
  const handleRefreshAll = useCallback(async () => {
    setSp500Loading(true);
    
    // Update FRED loading states
    const updatedFredStates = { ...fredSeriesStates };
    Object.keys(updatedFredStates).forEach(seriesId => {
      updatedFredStates[seriesId] = {
        ...updatedFredStates[seriesId],
        loading: true
      };
    });
    setFredSeriesStates(updatedFredStates);
    
    // Refresh S&P 500
    try {
      const data = await IndicatorService.getSP500Data(dateRange.startDate, dateRange.endDate);
      setSp500Data(data);
      setIndicatorRef.current('SP500', data);
      setSp500Error(null);
    } catch (error) {
      console.error('Error refreshing S&P 500 data:', error);
      setSp500Error('Failed to refresh S&P 500 data');
    } finally {
      setSp500Loading(false);
    }
    
    // Refresh FRED series
    const fredPromises = coincidentIndicatorSeries.map(async (seriesId) => {
      try {
        const data = await IndicatorService.getFREDData(seriesId, dateRange.startDate, dateRange.endDate);
        setIndicatorRef.current(`FRED-${seriesId}`, data);
        return { seriesId, data, error: null };
      } catch (error) {
        console.error(`Error refreshing FRED data for ${seriesId}:`, error);
        return { seriesId, data: null, error: `Failed to refresh ${seriesId} data from FRED` };
      }
    });
    
    const results = await Promise.all(fredPromises);
    const newFredStates = { ...fredSeriesStates };
    
    results.forEach(({ seriesId, data, error }) => {
      newFredStates[seriesId] = {
        data,
        loading: false,
        error
      };
    });
    
    setFredSeriesStates(newFredStates);
  }, [dateRange, fredSeriesStates, coincidentIndicatorSeries]);

  // Get the most recent date from all indicators
  const mostRecentUpdateDate = useMemo(() => {
    let dates: Date[] = [];
    
    if (sp500Data?.data && sp500Data.data.length > 0) {
      dates.push(new Date(sp500Data.data[sp500Data.data.length - 1].date));
    }
    
    Object.values(fredSeriesStates).forEach(({ data }) => {
      if (data?.data && data.data.length > 0) {
        dates.push(new Date(data.data[data.data.length - 1].date));
      }
    });
    
    if (dates.length === 0) {
      return 'No data available';
    }
    
    const mostRecentDate = new Date(Math.max(...dates.map(date => date.getTime())));
    
    return mostRecentDate.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  }, [sp500Data, fredSeriesStates]);

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" component="h2">
          Coincident Indicators
        </Typography>
        <Button 
          variant="contained" 
          color="primary" 
          onClick={handleRefreshAll}
        >
          Refresh All Data
        </Button>
      </Box>
      
      {/* Category Navigation */}
      <CategoryNavigation categories={categories} />
      
      {/* Market Sentiment */}
      <Box id="market-sentiment" sx={{ mb: 4, scrollMarginTop: '80px' }}>
        <CategoryHeader 
          id="market-sentiment"
          title="Market Sentiment"
          description={categoryDescriptions['market-sentiment']}
        />
        
        {/* S&P 500 */}
        <IndicatorSection
          title="SP500"
          data={sp500Data}
          isLoading={sp500Loading}
          error={sp500Error}
          defaultTitle="S&P 500 Index"
        />
      </Box>
      
      {/* Economic Activity */}
      <Box id="economic-activity" sx={{ mb: 4, scrollMarginTop: '80px' }}>
        <CategoryHeader 
          id="economic-activity"
          title="Economic Activity"
          description={categoryDescriptions['economic-activity']}
        />
        
        {/* Industrial Production Index */}
        <IndicatorSection
          title="INDPRO"
          data={fredSeriesStates['INDPRO']?.data || null}
          isLoading={fredSeriesStates['INDPRO']?.loading || false}
          error={fredSeriesStates['INDPRO']?.error || null}
          defaultTitle="Industrial Production Index"
        />
      </Box>
      
      <Box sx={{ mt: 4, textAlign: 'right' }}>
        <Typography variant="caption" color="text.secondary">
          Last fetched: {hasInitiallyLoaded ? new Date().toLocaleString() : 'Loading...'}
        </Typography>
        <Typography variant="caption" color="text.secondary" display="block">
          Most recent data point: {mostRecentUpdateDate}
        </Typography>
      </Box>
    </Box>
  );
};

export default CoincidentIndicators;