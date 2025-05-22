import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  CircularProgress,
  Divider
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Help as HelpIcon
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  TooltipProps
  // Legend // Removed Legend import
} from 'recharts';
import { NameType, ValueType } from 'recharts/types/component/DefaultTooltipContent';

// Type definitions
export interface TimeSeriesPoint {
  date: string; 
  value: number;
}

export interface IndicatorData {
  series_id: string;
  title: string;
  data: TimeSeriesPoint[]; // Primary data series
  units?: string;
  frequency?: string;
  lastValue?: number;
  bullishThreshold?: number;
  bearishThreshold?: number;
  signalStatus?: 'bullish' | 'bearish' | 'neutral';
  yAxisDomain?: [number, number];
  description?: string; 
  ma_series_data?: TimeSeriesPoint[]; 
}

export type SignalStatus = 'bullish' | 'bearish' | 'neutral';

interface IndicatorCardProps {
  indicator: IndicatorData;
  isLoading?: boolean;
  error?: string | null;
}

const formatDateDutch = (date: Date): string => {
  return date.toLocaleDateString('nl-NL', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
};

// Y-axis formatter function
const formatYAxisValue = (value: number): string => {
  if (typeof value !== 'number' || isNaN(value)) return '';
  
  // Format to max 3 decimal places, removing trailing zeros
  return Number(value.toFixed(3)).toString();
};

const CustomTooltipContent: React.FC<TooltipProps<ValueType, NameType> & { indicatorTitle: string, indicatorUnits?: string, maLabel?: string }> = ({ active, payload, indicatorTitle, indicatorUnits, maLabel }) => {
  if (active && payload && payload.length) {
    const dataPoint = payload[0].payload as { timestamp: number; originalDate: Date; value: number; maValue?: number }; 
    if (!dataPoint) return null;

    return (
      <Box sx={{
        backgroundColor: 'background.paper', 
        padding: '10px',
        border: '1px solid',
        borderColor: 'divider', 
        borderRadius: '4px',
        boxShadow: '0 2px 5px rgba(0,0,0,0.15)',
        color: 'text.primary' 
      }}>
        <Typography variant="caption" display="block" sx={{ fontWeight: 'bold', mb: 0.5 }}>
          {indicatorTitle}
        </Typography>
        <Typography variant="caption" display="block">
          Date: {formatDateDutch(dataPoint.originalDate)}
        </Typography>
        <Typography variant="caption" display="block">
          {indicatorUnits ? `${indicatorUnits}: ` : 'Value: '}
          {typeof dataPoint.value === 'number' ? dataPoint.value.toFixed(2) : 'N/A'}
        </Typography>
        {/* Display MA value in tooltip if present and is a number */}
        {payload.find(p => p.dataKey === 'maValue') && typeof dataPoint.maValue === 'number' && (
          <Typography variant="caption" display="block" sx={{color: '#ff7300'}}>
            {maLabel || 'MA'}: {dataPoint.maValue.toFixed(2)}
          </Typography>
        )}
      </Box>
    );
  }
  return null;
};


const IndicatorCard: React.FC<IndicatorCardProps> = ({
  indicator,
  isLoading = false,
  error = null
}) => {
  // --- DEBUGGING LOGS START ---
  if (indicator.series_id === 'SP500') { // Log only for S&P 500 to avoid console spam
    console.log(`[IndicatorCard SP500] Received indicator prop:`, JSON.parse(JSON.stringify(indicator)));
    if (indicator.ma_series_data) {
      console.log(`[IndicatorCard SP500] ma_series_data (length ${indicator.ma_series_data.length}):`, JSON.parse(JSON.stringify(indicator.ma_series_data.slice(0, 5)))); // Log first 5 MA points
    } else {
      console.log(`[IndicatorCard SP500] ma_series_data is undefined or empty.`);
    }
  }
  // --- DEBUGGING LOGS END ---

  const chartData = React.useMemo(() =>
    indicator.data?.map(point => {
      const dateObj = new Date(point.date);
      return {
        timestamp: dateObj.getTime(),
        originalDate: dateObj,
        value: point.value
      };
    }).sort((a, b) => a.timestamp - b.timestamp) || []
  , [indicator.data]);

  const combinedChartData = React.useMemo(() => {
    if (!indicator.ma_series_data || indicator.ma_series_data.length === 0) {
      return chartData.map(p => ({ ...p, maValue: undefined })); 
    }

    const maDataMap = new Map<number, number>();
    indicator.ma_series_data.forEach(point => {
      if (point && typeof point.date === 'string' && typeof point.value === 'number') { 
        maDataMap.set(new Date(point.date).getTime(), point.value);
      }
    });

    return chartData.map(primaryPoint => ({
      ...primaryPoint,
      maValue: maDataMap.get(primaryPoint.timestamp) 
    }));
  }, [chartData, indicator.ma_series_data]);

  // --- DEBUGGING LOGS START ---
  if (indicator.series_id === 'SP500') {
    console.log(`[IndicatorCard SP500] combinedChartData (length ${combinedChartData.length}):`, JSON.parse(JSON.stringify(combinedChartData.slice(0, 5)))); // Log first 5 combined points
    const pointsWithMaValue = combinedChartData.filter(p => typeof p.maValue === 'number');
    console.log(`[IndicatorCard SP500] Number of points with actual maValue: ${pointsWithMaValue.length}`);
    if (pointsWithMaValue.length > 0) {
        console.log(`[IndicatorCard SP500] First few points with maValue:`, JSON.parse(JSON.stringify(pointsWithMaValue.slice(0,5))));
    }
  }
  // --- DEBUGGING LOGS END ---


  const lastValue = indicator.lastValue ?? (chartData.length > 0 ? chartData[chartData.length - 1].value : undefined);

  const signalStatus = indicator.signalStatus || ((): SignalStatus => {
    if (lastValue === undefined || indicator.bullishThreshold === undefined || indicator.bearishThreshold === undefined) {
      return 'neutral';
    }
    if (indicator.bullishThreshold < indicator.bearishThreshold) { 
        if (lastValue <= indicator.bullishThreshold) return 'bullish';
        if (lastValue >= indicator.bearishThreshold) return 'bearish';
    } else { 
        if (lastValue >= indicator.bullishThreshold) return 'bullish';
        if (lastValue <= indicator.bearishThreshold) return 'bearish';
    }
    return 'neutral';
  })();

  const getSignalColor = (status: SignalStatus): string => {
    switch (status) {
      case 'bullish': return '#4caf50'; 
      case 'bearish': return '#f44336'; 
      default: return '#ff9800'; 
    }
  };

  const getSignalIcon = (status: SignalStatus) => {
    switch (status) {
      case 'bullish': return <TrendingUpIcon />;
      case 'bearish': return <TrendingDownIcon />;
      default: return <HelpIcon />;
    }
  };

  const calculateYAxisDomain = React.useCallback((): [number | string, number | string] => {
    if (indicator.yAxisDomain) return indicator.yAxisDomain as [number | string, number | string];
    
    let allValues: number[] = [];
    if (chartData.length > 0) {
        allValues.push(...chartData.map(d => d.value).filter(v => typeof v === 'number'));
    }
    if (indicator.ma_series_data && indicator.ma_series_data.length > 0) {
        allValues.push(...indicator.ma_series_data.map(d => d.value).filter(v => typeof v === 'number'));
    }

    if (allValues.length === 0) return ['auto', 'auto'];

    let dataMin = Math.min(...allValues);
    let dataMax = Math.max(...allValues);

    if (indicator.bullishThreshold !== undefined) {
        dataMin = Math.min(dataMin, indicator.bullishThreshold);
        dataMax = Math.max(dataMax, indicator.bullishThreshold);
    }
    if (indicator.bearishThreshold !== undefined) {
        dataMin = Math.min(dataMin, indicator.bearishThreshold);
        dataMax = Math.max(dataMax, indicator.bearishThreshold);
    }
     if (indicator.series_id.includes('ISM') || (indicator.bullishThreshold === 50 && (indicator.bearishThreshold === 45 || indicator.bearishThreshold === 50)) ) {
         dataMin = Math.min(dataMin, 30); 
         dataMax = Math.max(dataMax, 70);
     }

    if (dataMin === dataMax) {
        const padding = Math.abs(dataMin * 0.1) || 10; 
        return [dataMin - padding, dataMax + padding];
    }
    
    const range = dataMax - dataMin;
    const padding = range * 0.1; 

    return [dataMin - padding, dataMax + padding];
  }, [chartData, indicator.ma_series_data, indicator.yAxisDomain, indicator.bullishThreshold, indicator.bearishThreshold, indicator.series_id]);

  const yAxisDomain = calculateYAxisDomain();

  const needsReferenceLine50 = (): boolean => {
    return indicator.series_id.includes('ISM') ||
           (indicator.bullishThreshold === 50 && (indicator.bearishThreshold === 45 || indicator.bearishThreshold === 50));
  };

  const getLatestDate = (): string => {
    if (!chartData || chartData.length === 0) return 'N/A';
    const latestPoint = chartData[chartData.length -1];
    return formatDateDutch(latestPoint.originalDate);
  };

  const getMonthlyXAxisTicks = React.useCallback((): number[] => {
    if (!combinedChartData.length) return [];
    const monthlyTicksMap = new Map<string, number>();
    combinedChartData.forEach(point => {
      if (point && point.originalDate) { 
        const yearMonth = `${point.originalDate.getFullYear()}-${String(point.originalDate.getMonth() + 1).padStart(2, '0')}`;
        if (!monthlyTicksMap.has(yearMonth)) {
          monthlyTicksMap.set(yearMonth, point.timestamp);
        }
      }
    });
    return Array.from(monthlyTicksMap.values()).sort((a,b) => a - b);
  }, [combinedChartData]);

  const monthlyTicks = getMonthlyXAxisTicks();
  
  const maLabel = indicator.series_id === 'SP500' && indicator.bullishThreshold === indicator.bearishThreshold ? `MA (${(indicator.bullishThreshold || 125).toFixed(0)})` : 'MA';


  if (isLoading) {
    return (
      <Card sx={{ minHeight: 300, display: 'flex', justifyContent: 'center', alignItems: 'center', mb: 2 }}>
        <CircularProgress />
      </Card>
    );
  }

  if (error) {
    return (
      <Card sx={{ minHeight: 300, mb: 2 }}>
        <CardContent>
          <Typography color="error" variant="h6">Error</Typography>
          <Typography color="error">{error}</Typography>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card sx={{ minHeight: 300, mb: 2, boxShadow: 3 }}>
      <CardContent sx={{ '&:last-child': { pb: 2 } }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
          <Box sx={{maxWidth: 'calc(100% - 100px)'}}>
            <Typography variant="h6" component="div" noWrap title={indicator.title}>
              {indicator.title}
            </Typography>
          </Box>
          <Chip
            icon={getSignalIcon(signalStatus)}
            label={signalStatus.toUpperCase()}
            sx={{ bgcolor: getSignalColor(signalStatus), color: 'white', fontWeight: 'bold', ml:1 }}
            size="small"
          />
        </Box>

        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Typography variant="body2" color="text.secondary">
            {indicator.frequency || ''} {indicator.units ? `(${indicator.units})` : ''}
            {chartData.length > 0 && (
              <span> • Last: {getLatestDate()}</span>
            )}
          </Typography>
          {lastValue !== undefined && (
            <Typography variant="h6" sx={{ fontWeight: 'medium' }}>
              {lastValue.toFixed(2)}
            </Typography>
          )}
        </Box>

        <Divider sx={{ mb: 2 }} />

        {combinedChartData.length > 0 ? (
          <Box sx={{ height: 220, width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={combinedChartData} 
                margin={{ top: 5, right: 50, left: 0, bottom: 40 }} 
              >
                <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.3} />
                <XAxis
                  dataKey="timestamp"
                  type="number"
                  scale="time"
                  domain={['dataMin', 'dataMax']}
                  ticks={monthlyTicks}
                  tickFormatter={(tickItem) => formatDateDutch(new Date(tickItem))}
                  angle={-45}
                  textAnchor="end"
                  height={55} 
                  dy={10}    
                  interval="preserveStartEnd" 
                  tick={{ fontSize: 10 }} 
                />
                <YAxis
                    domain={yAxisDomain}
                    allowDataOverflow={false}
                    tick={{ fontSize: 10 }}
                    width={45}
                    tickFormatter={formatYAxisValue}
                />
                <Tooltip
                  content={<CustomTooltipContent indicatorTitle={indicator.title} indicatorUnits={indicator.units} maLabel={maLabel}/>}
                  cursor={{ stroke: '#8884d8', strokeWidth: 1, strokeDasharray: '3 3' }}
                />
                {/* <Legend verticalAlign="top" height={30}/> Removed Legend */}

                {needsReferenceLine50() && (
                  <ReferenceLine y={50} stroke="#666" strokeDasharray="3 3" strokeOpacity={0.7} />
                )}

                {(!indicator.ma_series_data || indicator.bullishThreshold !== indicator.ma_series_data?.[indicator.ma_series_data.length-1]?.value) && indicator.bullishThreshold !== undefined && (
                  <ReferenceLine
                    y={indicator.bullishThreshold}
                    stroke={getSignalColor('bullish')}
                    strokeWidth={1}
                    strokeDasharray="5 5"
                    label={{
                      value: `Bull (${indicator.bullishThreshold.toFixed(1)})`,
                      position: 'insideTopRight',
                      dx: -5, dy: -2, fill: getSignalColor('bullish'), fontSize: 9, fontWeight: 'bold'
                    }}
                  />
                )}

                {(!indicator.ma_series_data || indicator.bearishThreshold !== indicator.ma_series_data?.[indicator.ma_series_data.length-1]?.value) && indicator.bearishThreshold !== undefined && (
                  <ReferenceLine
                    y={indicator.bearishThreshold}
                    stroke={getSignalColor('bearish')}
                    strokeWidth={1}
                    strokeDasharray="5 5"
                    label={{
                      value: `Bear (${indicator.bearishThreshold.toFixed(1)})`,
                      position: 'insideBottomRight',
                      dx: -5, dy: 2, fill: getSignalColor('bearish'), fontSize: 9, fontWeight: 'bold'
                    }}
                  />
                )}

                <Line
                  type="monotone"
                  dataKey="value"
                  name={indicator.title} 
                  stroke="#8884d8" 
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 5, strokeWidth: 0, fill: '#8884d8' }}
                />
                {indicator.ma_series_data && indicator.ma_series_data.length > 0 && (
                  <Line
                    type="monotone"
                    dataKey="maValue" 
                    name={maLabel} 
                    stroke="#ff7300" 
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 5, strokeWidth: 0, fill: '#ff7300' }}
                    connectNulls={true} 
                  />
                )}
              </LineChart>
            </ResponsiveContainer>
          </Box>
        ) : (
          <Box sx={{ height: 220, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              No data available for the selected range.
            </Typography>
          </Box>
        )}

        {indicator.description && (
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1.5, display: 'block', fontStyle: 'italic', lineHeight: 1.4, borderTop: '1px dashed', borderColor: 'divider', pt: 1 }}>
            {indicator.description}
          </Typography>
        )}
      </CardContent>
    </Card>
  );
};

export default IndicatorCard;