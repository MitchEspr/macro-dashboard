// // frontend/src/components/LeadingIndicators.tsx

// import React, { useEffect, useState, useCallback, useMemo } from 'react';
// import { 
//   Typography, 
//   Box, 
//   Button,
//   Alert,
//   Chip
// } from '@mui/material';
// import { IndicatorData } from './IndicatorCard';
// import IndicatorService from '../services/IndicatorService';
// import { useIndicators } from '../context/IndicatorContext';
// import CategoryHeader from './CategoryHeader';
// import CategoryNavigation from './CategoryNavigation';
// import IndicatorSection from './IndicatorSection';
// import DashboardConfig from '../services/DashboardConfig';

// const LeadingIndicators: React.FC = () => {
//   const { setIndicator } = useIndicators();
  
//   // Simplified state management - no more complex individual states
//   const [indicatorData, setIndicatorData] = useState<Record<string, IndicatorData>>({});
//   const [loadingStates, setLoadingStates] = useState<Record<string, boolean>>({});
//   const [errors, setErrors] = useState<Record<string, string>>({});
//   const [categories, setCategories] = useState<any[]>([]);
//   const [hasInitiallyLoaded, setHasInitiallyLoaded] = useState(false);
  
//   // Get date range from config
//   const dateRange = useMemo(() => DashboardConfig.getDefaultDateRange(), []);
  
//   // Leading indicator categories (filtered from backend)
//   const leadingCategories = useMemo(() => [
//     'Business Cycle Indicators',
//     'Global Risk Metrics', 
//     'Financial Market Indicators',
//     'Global Liquidity Metrics',
//     'Housing Market'
//   ], []);

//   const fetchCategoriesAndIndicators = useCallback(async () => {
//     try {
//       // Fetch categories from backend
//       const allCategories = await IndicatorService.getCategories();
      
//       // Filter for leading indicator categories
//       const leadingCats = allCategories.filter(cat => 
//         leadingCategories.includes(cat.name)
//       );
//       setCategories(leadingCats);
      
//       // Get all indicator IDs from leading categories
//       const allIndicatorIds = leadingCats.flatMap(cat => cat.indicators);
      
//       // Set initial loading states
//       const initialLoadingStates: Record<string, boolean> = {};
//       allIndicatorIds.forEach(id => {
//         initialLoadingStates[id] = true;
//       });
//       setLoadingStates(initialLoadingStates);
      
//       // Fetch all indicators in parallel (backend does all processing)
//       const indicatorDataResult = await IndicatorService.getMultipleIndicators(
//         allIndicatorIds,
//         dateRange.startDate,
//         dateRange.endDate
//       );
      
//       // Update state
//       setIndicatorData(indicatorDataResult);
      
//       // Update global context
//       Object.entries(indicatorDataResult).forEach(([id, data]) => {
//         setIndicator(id, data);
//       });
      
//       // Clear loading states
//       const clearedLoadingStates: Record<string, boolean> = {};
//       allIndicatorIds.forEach(id => {
//         clearedLoadingStates[id] = false;
//       });
//       setLoadingStates(clearedLoadingStates);
      
//       setHasInitiallyLoaded(true);
      
//     } catch (error) {
//       console.error('Error fetching categories and indicators:', error);
//       // Set error state for all indicators
//       const errorStates: Record<string, string> = {};
//       const allIndicatorIds = categories.flatMap(cat => cat.indicators);
//       allIndicatorIds.forEach(id => {
//         errorStates[id] = 'Failed to load data';
//       });
//       setErrors(errorStates);
//       setLoadingStates({});
//     }
//   }, [leadingCategories, categories, dateRange.startDate, dateRange.endDate, setIndicator]); // Remove loadingStates dependency

//   // Fetch categories and indicators on mount
//   useEffect(() => {
//     if (!hasInitiallyLoaded) {
//       fetchCategoriesAndIndicators();
//     }
//   }, [hasInitiallyLoaded, fetchCategoriesAndIndicators]);

//   const handleRefreshAll = useCallback(async () => {
//     // Reset states
//     setErrors({});
    
//     // Use current categories state directly (no dependency needed)
//     setCategories(currentCategories => {
//       const allIndicatorIds = currentCategories.flatMap(cat => cat.indicators);
      
//       // Set all to loading
//       const newLoadingStates: Record<string, boolean> = {};
//       allIndicatorIds.forEach(id => {
//         newLoadingStates[id] = true;
//       });
//       setLoadingStates(newLoadingStates);
      
//       // Fetch fresh data async
//       (async () => {
//         try {
//           const indicatorDataResult = await IndicatorService.getMultipleIndicators(
//             allIndicatorIds,
//             dateRange.startDate,
//             dateRange.endDate
//           );
          
//           setIndicatorData(indicatorDataResult);
          
//           // Update global context
//           Object.entries(indicatorDataResult).forEach(([id, data]) => {
//             setIndicator(id, data);
//           });
          
//         } catch (error) {
//           console.error('Error refreshing indicators:', error);
//           const errorStates: Record<string, string> = {};
//           allIndicatorIds.forEach(id => {
//             errorStates[id] = 'Failed to refresh data';
//           });
//           setErrors(errorStates);
//         } finally {
//           // Clear loading states
//           setLoadingStates({});
//         }
//       })();
      
//       return currentCategories; // Return unchanged categories
//     });
//   }, [dateRange.startDate, dateRange.endDate, setIndicator]);

//   // Get the most recent update date
//   const mostRecentUpdateDate = useMemo(() => {
//     const dates: Date[] = [];
    
//     Object.values(indicatorData).forEach(data => {
//       if (data.data && data.data.length > 0) {
//         dates.push(new Date(data.data[data.data.length - 1].date));
//       }
//     });
    
//     if (dates.length === 0) {
//       return 'No data available';
//     }
    
//     const mostRecentDate = new Date(Math.max(...dates.map(date => date.getTime())));
//     return mostRecentDate.toLocaleDateString('en-US', {
//       year: 'numeric',
//       month: 'long',
//       day: 'numeric'
//     });
//   }, [indicatorData]);

//   // Create navigation categories for UI
//   const navigationCategories = useMemo(() => {
//     return categories.map(cat => ({
//       id: cat.category_id,
//       name: cat.name
//     }));
//   }, [categories]);

//   // Show loading message if still fetching categories
//   if (!hasInitiallyLoaded && categories.length === 0) {
//     return (
//       <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 200 }}>
//         <Typography>Loading categories and indicators...</Typography>
//       </Box>
//     );
//   }

//   return (
//     <Box>
//       <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
//         <Typography variant="h5" component="h2">
//           Leading Indicators
//         </Typography>
//         <Button 
//           variant="contained" 
//           color="primary" 
//           onClick={handleRefreshAll}
//           disabled={Object.values(loadingStates).some(loading => loading)}
//         >
//           Refresh All Data
//         </Button>
//       </Box>
      
//       {/* Show data range info */}
//       <Alert severity="info" sx={{ mb: 3 }}>
//         <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
//           <Typography variant="body2">
//             <strong>Data Range:</strong> {dateRange.startDate} to {dateRange.endDate}
//           </Typography>
//           <Chip 
//             label={`${dateRange.label}`} 
//             size="small" 
//             color="primary" 
//             variant="outlined" 
//           />
//           <Chip 
//             label="v2 API (Backend Processing)" 
//             size="small" 
//             color="success" 
//             variant="outlined" 
//           />
//         </Box>
//       </Alert>
      
//       {/* Category Navigation */}
//       <CategoryNavigation categories={navigationCategories} />
      
//       {/* Render each category */}
//       {categories.map((category) => (
//         <Box key={category.category_id} id={category.category_id} sx={{ mb: 4, scrollMarginTop: '80px' }}>
//           <CategoryHeader 
//             id={category.category_id}
//             title={category.name}
//             description={category.description}
//           />
          
//           {/* Render indicators in this category */}
//           {category.indicators.map((indicatorId: string) => (
//             <IndicatorSection
//               key={indicatorId}
//               title={indicatorId}
//               data={indicatorData[indicatorId] || null}
//               isLoading={loadingStates[indicatorId] || false}
//               error={errors[indicatorId] || null}
//               defaultTitle={indicatorId}
//             />
//           ))}
//         </Box>
//       ))}
      
//       <Box sx={{ mt: 4, textAlign: 'right' }}>
//         <Typography variant="caption" color="text.secondary">
//           Last fetched: {hasInitiallyLoaded ? new Date().toLocaleString() : 'Loading...'}
//         </Typography>
//         <Typography variant="caption" color="text.secondary" display="block">
//           Most recent data point: {mostRecentUpdateDate}
//         </Typography>
//         <Typography variant="caption" color="text.secondary" display="block">
//           Processing: Server-side (v2 API) • Signals: Auto-calculated • Transformations: Backend
//         </Typography>
//       </Box>
//     </Box>
//   );
// };

// export default LeadingIndicators;
export {}