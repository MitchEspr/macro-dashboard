// frontend/src/services/DashboardConfig.ts

export interface DashboardCategory {
  id: string;
  name: string;
  description: string;
  displayOrder: number;
}

export interface IndicatorDisplayConfig {
  id: string;
  displayName?: string;
  highlighted?: boolean;
  chartHeight?: number;
}

// UI-focused category definitions (order matters for display)
export const DASHBOARD_CATEGORIES: DashboardCategory[] = [
  {
    id: 'business-cycle',
    name: 'Business Cycle Indicators',
    description: 'Track economic expansion and contraction cycles',
    displayOrder: 1
  },
  {
    id: 'global-risk',
    name: 'Global Risk Metrics',
    description: 'Monitor investor sentiment and risk appetite',
    displayOrder: 2
  },
  {
    id: 'financial-markets',
    name: 'Financial Market Indicators',
    description: 'Track equity and credit market trends',
    displayOrder: 3
  },
  {
    id: 'liquidity',
    name: 'Global Liquidity Metrics',
    description: 'Monitor money supply and liquidity conditions',
    displayOrder: 4
  },
  {
    id: 'housing',
    name: 'Housing Market',
    description: 'Leading indicators from the housing sector',
    displayOrder: 5
  },
  {
    id: 'economic-activity',
    name: 'Economic Activity',
    description: 'Real-time economic performance metrics',
    displayOrder: 6
  },
  {
    id: 'market-sentiment',
    name: 'Market Sentiment',
    description: 'Current investor mood and market participation',
    displayOrder: 7
  }
];

// Featured indicators to highlight on the dashboard
export const FEATURED_INDICATORS: string[] = [
  'ISM-PMI',
  'VIX',
  'GOLD-COPPER-RATIO',
  'T10Y2Y',
  'SP500'
];

// Default date ranges for different views
export const DATE_RANGES = {
  '1Y': { months: 12, label: '1 Year' },
  '2Y': { months: 24, label: '2 Years' },
  '3Y': { months: 36, label: '3 Years' },
  '4Y': { months: 48, label: '4 Years' },
  '5Y': { months: 60, label: '5 Years' },
  '10Y': { months: 120, label: '10 Years' },
  '20Y': { months: 240, label: '20 Years' }
} as const; // 'as const' makes keys and properties readonly and more specific

// Explicitly type DEFAULT_DATE_RANGE as one of the keys of DATE_RANGES
export const DEFAULT_DATE_RANGE: keyof typeof DATE_RANGES = '4Y';

// Utility functions for UI
export const getCategoryById = (categoryId: string): DashboardCategory | undefined => {
  return DASHBOARD_CATEGORIES.find(cat => cat.id === categoryId);
};

export const getCategoriesSorted = (): DashboardCategory[] => {
  return [...DASHBOARD_CATEGORIES].sort((a, b) => a.displayOrder - b.displayOrder);
};

export const getDateRange = (rangeKey: keyof typeof DATE_RANGES) => {
  const range = DATE_RANGES[rangeKey];
  const endDate = new Date();
  const startDate = new Date();
  startDate.setMonth(endDate.getMonth() - range.months);

  return {
    startDate: startDate.toISOString().split('T')[0],
    endDate: endDate.toISOString().split('T')[0],
    label: range.label
  };
};

export const getDefaultDateRangeInfo = () => { // Renamed to avoid confusion with the key constant
  return getDateRange(DEFAULT_DATE_RANGE);
};

const DashboardConfig = {
  categories: DASHBOARD_CATEGORIES,
  featuredIndicators: FEATURED_INDICATORS,
  dateRanges: DATE_RANGES, // Correctly 'dateRanges' (lowercase 'd')
  defaultDateRange: DEFAULT_DATE_RANGE, // This is now correctly typed
  getCategoryById,
  getCategoriesSorted,
  getDateRange,
  getDefaultDateRangeInfo // Use the new name for the info object
};

export default DashboardConfig;
