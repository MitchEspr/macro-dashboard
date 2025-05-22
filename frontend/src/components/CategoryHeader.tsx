import React from 'react';
import { Paper, Typography } from '@mui/material';

interface CategoryHeaderProps {
  id: string;
  title: string;
  description: string;
}

/**
 * A component that renders a category header with a title and description
 */
const CategoryHeader: React.FC<CategoryHeaderProps> = ({ id, title, description }) => {
  return (
    <Paper 
      id={id} 
      sx={{ 
        p: 3, 
        mb: 2, 
        bgcolor: 'primary.dark', 
        color: 'white', 
        borderRadius: 2,
        scrollMarginTop: '80px' 
      }}
    >
      <Typography variant="h5" gutterBottom fontWeight="bold">
        {title}
      </Typography>
      <Typography variant="body1">
        {description}
      </Typography>
    </Paper>
  );
};

export default CategoryHeader;