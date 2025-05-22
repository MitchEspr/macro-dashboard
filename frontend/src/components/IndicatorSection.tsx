import React from 'react';
import { Box, Typography, Paper, CircularProgress } from '@mui/material';
import IndicatorCard, { IndicatorData } from './IndicatorCard';

interface IndicatorSectionProps {
  title: string;
  data: IndicatorData | null;
  isLoading: boolean;
  error: string | null | undefined;
  defaultTitle: string;
}

/**
 * A component that renders either an IndicatorCard with data or a loading/error placeholder
 */
const IndicatorSection: React.FC<IndicatorSectionProps> = ({
  title,
  data,
  isLoading,
  error,
  defaultTitle
}) => {
  return (
    <Box sx={{ mb: 3 }}>
      {data ? (
        <IndicatorCard 
          indicator={data}
          isLoading={isLoading}
          error={error}
        />
      ) : (
        <Paper sx={{ minHeight: 300, p: 2, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
          <Typography variant="h6" gutterBottom>{defaultTitle}</Typography>
          {isLoading ? (
            <>
              <Box sx={{ my: 2 }}>
                <CircularProgress />
              </Box>
              <Typography>Loading data...</Typography>
            </>
          ) : (
            <Typography color="text.secondary">No data available</Typography>
          )}
        </Paper>
      )}
    </Box>
  );
};

export default IndicatorSection;