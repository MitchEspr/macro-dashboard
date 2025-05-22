import React from 'react';
import { Box, Chip, Link, Typography } from '@mui/material';

export interface Category {
  id: string;
  name: string;
}

interface CategoryNavigationProps {
  categories: Category[];
}

/**
 * A component that provides navigation between different categories using quick jump chips
 */
const CategoryNavigation: React.FC<CategoryNavigationProps> = ({ categories }) => {
  // Render category quick links as chips
  const renderQuickLinks = () => {
    return (
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 3 }}>
        <Typography variant="body2" sx={{ mr: 1, alignSelf: 'center' }}>
          Quick Jump:
        </Typography>
        {categories.map((category) => (
          <Chip
            key={category.id}
            label={category.name}
            component={Link}
            href={`#${category.id}`}
            onClick={(e) => {
              e.preventDefault();
              const element = document.getElementById(category.id);
              if (element) {
                element.scrollIntoView({ behavior: 'smooth' });
              }
            }}
            sx={{ cursor: 'pointer' }}
            clickable
          />
        ))}
      </Box>
    );
  };

  return renderQuickLinks();
};

export default CategoryNavigation;