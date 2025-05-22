// frontend/src/pages/Dashboard.tsx
import React, { useState, useCallback, useMemo, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Tabs,
  Tab,
  Card,
  CardContent,
  Grid,
  LinearProgress,
  Chip,
  Alert
} from '@mui/material';
import {
  TrendingUp as BullIcon,
  TrendingDown as BearIcon,
  Help as NeutralIcon,
  Speed as RiskOnIcon,
  Security as RiskOffIcon
} from '@mui/icons-material';
import IndicatorCategoryPage from '../components/IndicatorCategoryPage';
import IndicatorService from '../services/IndicatorService';
import DashboardConfig from '../services/DashboardConfig';

interface MarketStatus {
  bull_bear_status: string;
  risk_on_off_status: string;
  bull_bear_score: number;
  risk_on_off_score: number;
  total_indicators: number;
  bullish_count: number;
  bearish_count: number;
  neutral_count: number;
  last_updated: string;
}

// These constants are no longer needed as IndicatorCategoryPage fetches by type
// const LEADING_INDICATOR_CATEGORIES_NAMES = [
//   'Business Cycle Indicators',
//   'Global Risk Metrics',
//   'Financial Market Indicators',
//   'Global Liquidity Metrics',
//   'Housing Market'
// ];

// const COINCIDENT_INDICATOR_CATEGORIES_NAMES = [
//   'Market Sentiment',
//   'Economic Activity'
// ];

// const LAGGING_INDICATOR_CATEGORIES_NAMES: string[] = [
//     // Example: 'Inflation Metrics', 'Employment Trends'
// ];


function Dashboard() {
  const [tabValue, setTabValue] = useState(0);
  const [marketStatus, setMarketStatus] = useState<MarketStatus | null>(null);
  const [marketStatusLoading, setMarketStatusLoading] = useState(true);
  const [marketStatusError, setMarketStatusError] = useState<string | null>(null);

  const handleTabChange = useCallback((event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  }, []);

  const fetchMarketStatus = useCallback(async () => {
    try {
      setMarketStatusLoading(true);
      setMarketStatusError(null);
      const status = await IndicatorService.getMarketStatus();
      setMarketStatus(status);
    } catch (error) {
      console.error('Error fetching market status:', error);
      setMarketStatusError('Failed to load market status from the server.');
      setMarketStatus(null);
    } finally {
      setMarketStatusLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMarketStatus();
    const interval = setInterval(fetchMarketStatus, 5 * 60 * 1000); // Refresh every 5 minutes
    return () => clearInterval(interval);
  }, [fetchMarketStatus]);

  const getBullBearDisplay = useMemo(() => {
    if (marketStatusLoading) return { color: 'text.secondary', icon: <NeutralIcon />, label: 'LOADING', bgColor: 'grey.700' };
    if (!marketStatus || marketStatusError) return { color: 'text.secondary', icon: <NeutralIcon />, label: 'N/A', bgColor: 'grey.700' };

    switch (marketStatus.bull_bear_status) {
      case 'BULL':
        return { color: 'success.main', bgColor: 'success.dark', icon: <BullIcon />, label: 'BULL MARKET' };
      case 'BEAR':
        return { color: 'error.main', bgColor: 'error.dark', icon: <BearIcon />, label: 'BEAR MARKET' };
      default:
        return { color: 'warning.main', bgColor: 'warning.dark', icon: <NeutralIcon />, label: 'NEUTRAL MARKET' };
    }
  }, [marketStatus, marketStatusLoading, marketStatusError]);

  const getRiskDisplay = useMemo(() => {
    if (marketStatusLoading) return { color: 'text.secondary', icon: <NeutralIcon />, label: 'LOADING', bgColor: 'grey.700' };
    if (!marketStatus || marketStatusError) return { color: 'text.secondary', icon: <NeutralIcon />, label: 'N/A', bgColor: 'grey.700' };

    switch (marketStatus.risk_on_off_status) {
      case 'RISK-ON':
        return { color: 'info.main', bgColor: 'info.dark', icon: <RiskOnIcon />, label: 'RISK-ON' };
      case 'RISK-OFF':
        return { color: 'warning.main', bgColor: 'warning.dark', icon: <RiskOffIcon />, label: 'RISK-OFF' };
      default:
        return { color: 'grey.600', bgColor: 'grey.700', icon: <NeutralIcon />, label: 'NEUTRAL' };
    }
  }, [marketStatus, marketStatusLoading, marketStatusError]);

  //const defaultDateRange = DashboardConfig.getDefaultDateRange();
  // Using a consistent date range for all types for now, can be customized per tab if needed.
  // For example, leading indicators might use a longer historical range.
  const leadingDateRange = DashboardConfig.getDateRange('4Y'); // Example: 5 years for leading
  const coincidentDateRange = DashboardConfig.getDateRange('4Y'); // Example: 3 years for coincident
  const laggingDateRange = DashboardConfig.getDateRange('4Y'); // Example: 5 years for lagging

  return (
    <Container maxWidth="xl">
      <Box sx={{ my: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom align="center">
          Macro Investment Dashboard
        </Typography>

        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} md={6}>
            <Card sx={{ bgcolor: getBullBearDisplay.bgColor, color: 'white', textAlign: 'center', minHeight: 140, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 1 }}>
                  {getBullBearDisplay.icon}
                  <Typography variant="h6" component="div" sx={{ ml: 1 }}>Market Cycle</Typography>
                </Box>
                {marketStatusLoading ? (
                  <Box sx={{ mt: 2 }}><LinearProgress color="inherit" /><Typography variant="body2" sx={{ mt: 1 }}>Loading...</Typography></Box>
                ) : marketStatusError && !marketStatus ? (
                  <Box sx={{ mt: 1 }}><Typography variant="h4" component="div" sx={{ mb: 0.5 }}>{getBullBearDisplay.label}</Typography><Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.7)' }}>{marketStatusError}</Typography></Box>
                ) : marketStatus ? (
                  <><Typography variant="h4" component="div" sx={{ mt: 1, mb: 0.5 }}>{getBullBearDisplay.label}</Typography><Box sx={{ mt: 1 }}><LinearProgress variant="determinate" value={marketStatus.bull_bear_score || 0} color="inherit" sx={{ height: 8, borderRadius: 4 }} /><Typography variant="caption" sx={{ mt: 0.5, display: 'block' }}>Confidence: {marketStatus.bull_bear_score.toFixed(1)}%</Typography></Box></>
                ) : (
                  <Typography sx={{mt: 1}}>Market status unavailable.</Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card sx={{ bgcolor: getRiskDisplay.bgColor, color: 'white', textAlign: 'center', minHeight: 140, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 1 }}>
                  {getRiskDisplay.icon}
                  <Typography variant="h6" component="div" sx={{ ml: 1 }}>Risk Sentiment</Typography>
                </Box>
                 {marketStatusLoading ? (
                  <Box sx={{ mt: 2 }}><LinearProgress color="inherit" /><Typography variant="body2" sx={{ mt: 1 }}>Loading...</Typography></Box>
                ) : marketStatusError && !marketStatus ? (
                  <Box sx={{ mt: 1 }}><Typography variant="h4" component="div" sx={{ mb: 0.5 }}>{getRiskDisplay.label}</Typography><Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.7)' }}>{marketStatusError}</Typography></Box>
                ) : marketStatus ? (
                  <><Typography variant="h4" component="div" sx={{ mt: 1, mb: 0.5 }}>{getRiskDisplay.label}</Typography><Box sx={{ mt: 1 }}><LinearProgress variant="determinate" value={marketStatus.risk_on_off_score || 0} color="inherit" sx={{ height: 8, borderRadius: 4 }} /><Typography variant="caption" sx={{ mt: 0.5, display: 'block' }}>Confidence: {marketStatus.risk_on_off_score.toFixed(1)}%</Typography></Box></>
                ) : (
                  <Typography sx={{mt: 1}}>Risk sentiment unavailable.</Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {marketStatusError && !marketStatusLoading && ( // Show general error for market status if it failed
           <Alert severity="warning" sx={{ mb: 3}}>{marketStatusError}</Alert>
        )}
        {marketStatus && !marketStatusLoading && !marketStatusError && (
          <Alert severity="info" sx={{ mb: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 1 }}>
              <Typography variant="body2">
                <strong>Signal Breakdown:</strong> {marketStatus.bullish_count} Bullish, {marketStatus.bearish_count} Bearish, {marketStatus.neutral_count} Neutral
                {marketStatus.total_indicators > 0 && ` (${marketStatus.total_indicators} total indicators)`}
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
                <Chip label={`Updated: ${new Date(marketStatus.last_updated).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`} size="small" variant="outlined"/>
                <Chip label="Auto-refresh (5min)" size="small" color="primary" variant="outlined" />
              </Box>
            </Box>
          </Alert>
        )}

        <Paper sx={{ width: '100%', mb: 3, position: 'sticky', top: 0, zIndex: 1100, bgcolor: 'background.paper' }}>
          <Tabs value={tabValue} onChange={handleTabChange} indicatorColor="primary" textColor="primary" centered sx={{ '& .MuiTab-root': { fontSize: '1rem', fontWeight: 'medium', py: 2 }}}>
            <Tab label="Leading Indicators" />
            <Tab label="Coincident Indicators" />
            <Tab label="Lagging Indicators" />
          </Tabs>
        </Paper>

        {/* Tab 0: Leading Indicators */}
        {tabValue === 0 && (
          <IndicatorCategoryPage
            pageTitle="Leading Indicators"
            indicatorType="leading" // Pass indicator type
            dateRangeConfig={{
              startDate: leadingDateRange.startDate,
              endDate: leadingDateRange.endDate,
              label: leadingDateRange.label
            }}
          />
        )}

        {/* Tab 1: Coincident Indicators */}
        {tabValue === 1 && (
          <IndicatorCategoryPage
            pageTitle="Coincident Indicators"
            indicatorType="coincident" // Pass indicator type
            dateRangeConfig={{
              startDate: coincidentDateRange.startDate,
              endDate: coincidentDateRange.endDate,
              label: coincidentDateRange.label
            }}
          />
        )}

        {/* Tab 2: Lagging Indicators */}
        {tabValue === 2 && (
           <IndicatorCategoryPage
                pageTitle="Lagging Indicators"
                indicatorType="lagging" // Pass indicator type
                dateRangeConfig={{
                    startDate: laggingDateRange.startDate,
                    endDate: laggingDateRange.endDate,
                    label: laggingDateRange.label
                }}
            />
           // Placeholder if no lagging indicators are configured yet by the backend for this type
           // The IndicatorCategoryPage itself will show a message if no indicators are returned.
        )}
      </Box>

      <Box sx={{ mb: 4, mt: 8, p: 2, bgcolor: 'background.paper', borderRadius: 1, textAlign: 'center' }}>
        <Typography variant="subtitle2" color="text.secondary">
          <strong>Data Sources:</strong> Federal Reserve Economic Data (FRED), ISM, DBNomics, Yahoo Finance
        </Typography>
        <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.5 }}>
          <strong>Backend Processing:</strong> All transformations, signals, and calculations performed server-side
        </Typography>
        <Typography variant="caption" color="text.secondary" display="block">
          <strong>Dashboard loaded:</strong> {new Date().toLocaleString()}
        </Typography>
        {marketStatus && !marketStatusLoading && (
          <Typography variant="caption" color="text.secondary" display="block">
            <strong>Market status calculated:</strong> {new Date(marketStatus.last_updated).toLocaleString()}
          </Typography>
        )}
      </Box>
    </Container>
  );
}

export default Dashboard;
