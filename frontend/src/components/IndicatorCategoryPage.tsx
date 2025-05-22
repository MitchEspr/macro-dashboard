// frontend/src/components/IndicatorCategoryPage.tsx
import React, { useEffect, useState, useCallback, useMemo, useRef } from 'react';
import {
  Typography,
  Box,
  Button,
  Alert,
  Chip,
  CircularProgress,
  ButtonGroup,
} from '@mui/material';
import IndicatorService, {
  CategoryInfo,
  IndicatorsByTypeAPIResponse
} from '../services/IndicatorService';
import { IndicatorData } from './IndicatorCard';
// import { useIndicators } from '../context/IndicatorContext'; // setIndicator is commented out
import CategoryHeader from './CategoryHeader';
import CategoryNavigation, { Category as NavCategory } from './CategoryNavigation';
import IndicatorSection from './IndicatorSection';
import DashboardConfig from '../services/DashboardConfig';

// Helper function to convert API response to frontend IndicatorData format
const convertToIndicatorData = (apiResponse: EnrichedIndicatorAPIResponse): IndicatorData => {
  return {
    series_id: apiResponse.indicator_id,
    title: apiResponse.title,
    data: apiResponse.data.map(point => ({
      ...point,
      date: point.date,
    })),
    units: apiResponse.units,
    frequency: apiResponse.frequency,
    lastValue: apiResponse.last_value,
    bullishThreshold: apiResponse.bullish_threshold,
    bearishThreshold: apiResponse.bearish_threshold,
    signalStatus: apiResponse.signal_status,
    yAxisDomain: apiResponse.y_axis_domain,
    description: apiResponse.description,
  };
};

// Interface for the raw enriched indicator data from the API
interface EnrichedIndicatorAPIResponse {
  indicator_id: string;
  title: string;
  data: any[]; // Should be TimeSeriesPoint[]
  units?: string;
  frequency?: string;
  category: string;
  description?: string;
  bullish_threshold: number;
  bearish_threshold: number;
  signal_status: 'bullish' | 'bearish' | 'neutral';
  last_value?: number;
  last_updated?: string;
  y_axis_domain?: [number, number];
}

interface DateRangeConfigProp {
  startDate: string;
  endDate: string;
  label: string;
}

interface IndicatorCategoryPageProps {
  pageTitle: string;
  indicatorType: 'leading' | 'coincident' | 'lagging';
  dateRangeConfig: DateRangeConfigProp;
  apiInfoChipLabel?: string;
}

const IndicatorCategoryPage: React.FC<IndicatorCategoryPageProps> = ({
  pageTitle,
  indicatorType,
  dateRangeConfig: initialDateRangeConfig,
  apiInfoChipLabel
}) => {
  // const { setIndicator } = useIndicators(); // Commented out

  const [fetchedIndicatorDetails, setFetchedIndicatorDetails] = useState<Record<string, EnrichedIndicatorAPIResponse | null>>({});
  const [displayableCategories, setDisplayableCategories] = useState<CategoryInfo[]>([]);
  const [isPageLoading, setIsPageLoading] = useState<boolean>(true);
  const [pageError, setPageError] = useState<string | null>(null);
  const [initialLoadAttempted, setInitialLoadAttempted] = useState(false);

  const prevPropsRef = useRef<{indicatorType: string, activeDateRangeKey: keyof typeof DashboardConfig.dateRanges} | null>(null);

  const [activeDateRangeKey, setActiveDateRangeKey] = useState<keyof typeof DashboardConfig.dateRanges>(() => {
    const initialKey = Object.keys(DashboardConfig.dateRanges).find(
      key => DashboardConfig.dateRanges[key as keyof typeof DashboardConfig.dateRanges].label === initialDateRangeConfig.label
    ) as keyof typeof DashboardConfig.dateRanges | undefined;
    return initialKey || DashboardConfig.defaultDateRange;
  });

  const currentDateRange = useMemo(() => {
    return DashboardConfig.getDateRange(activeDateRangeKey);
  }, [activeDateRangeKey]);

  const fetchData = useCallback(async (isRefresh = false) => {
    // Set loading true for initial load or explicit refresh/timeframe change
    setIsPageLoading(true); 
    setPageError(null);

    const rangeToFetch = currentDateRange; // Uses the state-derived currentDateRange

    try {
      const response: IndicatorsByTypeAPIResponse = await IndicatorService.getIndicatorsByType(
        indicatorType,
        rangeToFetch.startDate,
        rangeToFetch.endDate
      );

      const newFetchedDetails: Record<string, EnrichedIndicatorAPIResponse | null> = {};
      response.indicators.forEach(indicator => {
        newFetchedDetails[indicator.indicator_id] = indicator;
        // setIndicator(indicator.indicator_id, convertToIndicatorData(indicator));
      });

      setFetchedIndicatorDetails(newFetchedDetails);
      setDisplayableCategories(response.categories || []);

      if (response.indicators.length === 0) {
        console.warn(`No indicators returned for type: ${indicatorType} for page: ${pageTitle}`);
        if (response.categories.length === 0) {
            setPageError(`No indicators or categories are currently configured for "${pageTitle}" (${indicatorType} type).`);
        }
      }
    } catch (error) {
      console.error(`Error fetching ${indicatorType} indicators for ${pageTitle}:`, error);
      setPageError(`An unexpected error occurred while loading indicators for ${pageTitle}. Please try refreshing.`);
      setFetchedIndicatorDetails({});
      setDisplayableCategories([]);
    } finally {
      setIsPageLoading(false);
      if (!initialLoadAttempted) {
        setInitialLoadAttempted(true);
      }
    }
  }, [indicatorType, pageTitle, currentDateRange, initialLoadAttempted /*, setIndicator, activeDateRangeKey is implicitly handled via currentDateRange */]);

  useEffect(() => {
    const previousIndicatorType = prevPropsRef.current?.indicatorType;
    const previousActiveDateRangeKey = prevPropsRef.current?.activeDateRangeKey;

    if (!initialLoadAttempted || indicatorType !== previousIndicatorType || activeDateRangeKey !== previousActiveDateRangeKey) {
        fetchData();
    }
    prevPropsRef.current = { indicatorType, activeDateRangeKey };

  }, [fetchData, initialLoadAttempted, indicatorType, activeDateRangeKey]);


  const handleRefreshAll = useCallback(async () => {
    await fetchData(true);
  }, [fetchData]);

  const handleTimeframeChange = (newTimeframeKey: keyof typeof DashboardConfig.dateRanges) => {
    setActiveDateRangeKey(newTimeframeKey);
    // fetchData will be called by useEffect due to activeDateRangeKey change
  };

  const mostRecentUpdateDate = useMemo(() => {
    const dates: Date[] = [];
    Object.values(fetchedIndicatorDetails).forEach(detail => {
      if (detail && detail.last_updated) {
        dates.push(new Date(detail.last_updated));
      } else if (detail && detail.data && detail.data.length > 0) {
        const lastPoint = detail.data[detail.data.length - 1];
        if (lastPoint && lastPoint.date) {
          dates.push(new Date(lastPoint.date));
        }
      }
    });

    if (dates.length === 0) return 'N/A';
    const mostRecentDate = new Date(Math.max(...dates.map(date => date.getTime())));
    return mostRecentDate.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
  }, [fetchedIndicatorDetails]);

  const navigationCategories = useMemo((): NavCategory[] => {
    return displayableCategories.map(cat => ({
      id: cat.category_id,
      name: cat.name
    }));
  }, [displayableCategories]);

  // Show full page loader only on the very first load attempt *before* initialLoadAttempted is true
  if (isPageLoading && !initialLoadAttempted) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 300, flexDirection: 'column' }}>
        <CircularProgress sx={{ mb: 2 }} />
        <Typography>Loading {pageTitle}...</Typography>
      </Box>
    );
  }

  if (pageError && displayableCategories.length === 0 && Object.keys(fetchedIndicatorDetails).length === 0 && initialLoadAttempted) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography variant="h5" component="h2" gutterBottom>{pageTitle}</Typography>
        <Alert severity="error" sx={{ mb: 3 }}>{pageError}</Alert>
        <Button variant="contained" onClick={() => fetchData(false)}>Try Again</Button>
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3, flexWrap: 'wrap', gap: 2 }}>
        <Typography variant="h5" component="h2">
          {pageTitle}
        </Typography>
        <Box sx={{display: 'flex', gap: 1, flexWrap: 'wrap', alignItems: 'center'}}>
          <ButtonGroup variant="outlined" aria-label="timeframe selection button group">
            {(Object.keys(DashboardConfig.dateRanges) as Array<keyof typeof DashboardConfig.dateRanges>).map((key) => (
              <Button
                key={key}
                variant={activeDateRangeKey === key ? "contained" : "outlined"}
                onClick={() => handleTimeframeChange(key)}
              >
                {DashboardConfig.dateRanges[key].label.replace(" Years", "Y").replace(" Year", "Y")}
              </Button>
            ))}
          </ButtonGroup>
          <Button
            variant="contained"
            color="primary"
            onClick={handleRefreshAll}
            disabled={isPageLoading}
            sx={{ml: 1}}
          >
            {isPageLoading ? <CircularProgress size={24} color="inherit"/> : 'Refresh All Data'}
          </Button>
        </Box>
      </Box>

      {pageError && (initialLoadAttempted && (Object.keys(fetchedIndicatorDetails).length > 0 || displayableCategories.length > 0)) && (
         <Alert severity="warning" sx={{ mb: 3 }}>
           {pageError} Some data may be incomplete or outdated.
         </Alert>
      )}

      <Alert severity="info" sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
          <Typography variant="body2">
            <strong>Data Range:</strong> {currentDateRange.startDate} to {currentDateRange.endDate}
          </Typography>
          <Chip
            label={`${currentDateRange.label}`}
            size="small"
            color="primary"
            variant="outlined"
          />
          {apiInfoChipLabel && (
            <Chip label={apiInfoChipLabel} size="small" color="success" variant="outlined"/>
          )}
        </Box>
      </Alert>

      {navigationCategories.length > 0 && <CategoryNavigation categories={navigationCategories} />}

      {displayableCategories.length === 0 && !isPageLoading && initialLoadAttempted && !pageError && (
         <Alert severity="info" sx={{ mt: 2 }}>
            No indicators are currently available for the "{pageTitle}" ({indicatorType}) type for the selected date range.
         </Alert>
      )}

      {displayableCategories.map((category) => (
        <Box key={category.category_id} id={category.category_id} sx={{ mb: 4, scrollMarginTop: '80px' }}>
          <CategoryHeader
            id={category.category_id}
            title={category.name}
            description={category.description}
          />
          
          {category.indicators.length === 0 ? (
            <Alert severity="info" sx={{mt: 2}}>No indicators currently listed in the "{category.name}" category for this type.</Alert>
          ) : (
            category.indicators.map((indicatorId: string) => {
              const indicatorDetail = fetchedIndicatorDetails[indicatorId];
              if (!indicatorDetail) {
                return (
                  <Box key={indicatorId} sx={{mb: 2}}> 
                    <Alert severity="warning">Data for indicator {indicatorId} is unavailable.</Alert>
                  </Box>
                );
              }
              const cardData = convertToIndicatorData(indicatorDetail);
              return (
                <IndicatorSection
                  key={indicatorId}
                  title={cardData.title}
                  data={cardData}
                  // THIS IS THE CORRECTED LINE:
                  isLoading={isPageLoading} 
                  error={null}    
                  defaultTitle={indicatorDetail.title || indicatorId}
                />
              );
            })
          )}
        </Box>
      ))}

      <Box sx={{ mt: 4, textAlign: 'right' }}>
        <Typography variant="caption" color="text.secondary">
          Last successful fetch: {(!isPageLoading && initialLoadAttempted) ? new Date().toLocaleString() : 'Loading...'}
        </Typography>
        <Typography variant="caption" color="text.secondary" display="block">
          Most recent data point: {mostRecentUpdateDate}
        </Typography>
         {apiInfoChipLabel && (
            <Typography variant="caption" color="text.secondary" display="block">
                Processing: Server-side ({apiInfoChipLabel}) • Signals: Auto-calculated • Transformations: Backend
            </Typography>
        )}
      </Box>
    </Box>
  );
};

export default IndicatorCategoryPage;
