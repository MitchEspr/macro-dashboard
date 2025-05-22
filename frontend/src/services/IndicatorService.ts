// frontend/src/services/IndicatorService.ts
import axios from 'axios';
import { IndicatorData, TimeSeriesPoint } from '../components/IndicatorCard'; // Assuming IndicatorCard exports these

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interface for the raw response from /v2/indicators/{indicator_id}
export interface EnrichedIndicatorAPIResponse { // Exporting for IndicatorCategoryPage
  indicator_id: string;
  title: string;
  data: TimeSeriesPoint[];
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
  ma_series_data?: TimeSeriesPoint[]; // Added MA series data
}

// Interface for the metadata response from /v2/indicators/{indicator_id}/metadata or /v2/indicators/
interface IndicatorMetadataResponse {
  indicator_id: string;
  name: string;
  category: string;
  data_source: string;
  description?: string;
  units?: string;
  frequency?: string;
}

// Interface for category information from /v2/indicators/categories
export interface CategoryInfo { 
  category_id: string; 
  name: string; 
  description: string;
  indicators: string[]; 
}

// Interface for the market status response from /v2/indicators/market-status
interface MarketStatusResponse {
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

// Interface for the response from /v2/indicators/type/{indicator_type_value}
export interface IndicatorsByTypeAPIResponse { 
  indicator_type: string; 
  indicators: EnrichedIndicatorAPIResponse[];
  categories: CategoryInfo[]; 
}

// Helper to convert API response to frontend IndicatorData format
// This function is now also defined in IndicatorCategoryPage.tsx.
// For consistency, it's good to have it in one place, e.g., here, and export it.
// However, to avoid breaking the existing structure if IndicatorCategoryPage relies on its local version,
// I will ensure this one is up-to-date.
export const convertAPIToIndicatorData = (apiResponse: EnrichedIndicatorAPIResponse): IndicatorData => {
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
    description: apiResponse.description, // Pass description
    ma_series_data: apiResponse.ma_series_data, // Pass MA series data
  };
};


const IndicatorService = {
  async getIndicator(indicatorId: string, startDate?: string, endDate?: string): Promise<IndicatorData> {
    try {
      const timestamp = new Date().getTime(); 
      const response = await apiClient.get<EnrichedIndicatorAPIResponse>(`/v2/indicators/${indicatorId}`, {
        params: { start_date: startDate, end_date: endDate, _t: timestamp },
      });
      return convertAPIToIndicatorData(response.data);
    } catch (error) {
      console.error(`Error fetching indicator ${indicatorId}:`, error);
      throw error;
    }
  },

  async getAllIndicatorsMetadata(): Promise<IndicatorMetadataResponse[]> {
    try {
      const response = await apiClient.get<IndicatorMetadataResponse[]>('/v2/indicators/'); 
      return response.data;
    } catch (error) {
      console.error('Error fetching all indicators metadata:', error);
      throw error;
    }
  },

  async getIndicatorMetadata(indicatorId: string): Promise<IndicatorMetadataResponse> {
    try {
      const response = await apiClient.get<IndicatorMetadataResponse>(`/v2/indicators/${indicatorId}/metadata`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching metadata for ${indicatorId}:`, error);
      throw error;
    }
  },

  async getCategories(): Promise<CategoryInfo[]> {
    try {
      const response = await apiClient.get<CategoryInfo[]>('/v2/indicators/categories');
      return response.data;
    } catch (error) {
      console.error('Error fetching categories:', error);
      throw error;
    }
  },

  async getMarketStatus(indicatorIds?: string[]): Promise<MarketStatusResponse> {
    try {
      const params: any = {};
      if (indicatorIds && indicatorIds.length > 0) {
        params.indicators = indicatorIds.join(',');
      }
      const response = await apiClient.get<MarketStatusResponse>('/v2/indicators/market-status', { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching market status:', error);
      throw error;
    }
  },

  async getIndicatorsByType(
    indicatorType: 'leading' | 'coincident' | 'lagging',
    startDate?: string,
    endDate?: string
  ): Promise<IndicatorsByTypeAPIResponse> {
    try {
      const timestamp = new Date().getTime(); 
      const response = await apiClient.get<IndicatorsByTypeAPIResponse>(`/v2/indicators/type/${indicatorType}`, {
        params: { start_date: startDate, end_date: endDate, _t: timestamp },
      });
      // The response.data.indicators are EnrichedIndicatorAPIResponse[], which now include ma_series_data
      return response.data;
    } catch (error) {
      console.error(`Error fetching ${indicatorType} indicators:`, error);
      throw error;
    }
  },

  async getMultipleIndicators(
    indicatorIds: string[],
    startDate?: string,
    endDate?: string
  ): Promise<Record<string, IndicatorData | null>> {
    const indicatorDataRecord: Record<string, IndicatorData | null> = {};
    const promises = indicatorIds.map(async (id) => {
      try {
        const data = await this.getIndicator(id, startDate, endDate);
        return { id, data };
      } catch (error) {
        console.error(`Error fetching indicator ${id} in getMultipleIndicators:`, error);
        return { id, data: null }; 
      }
    });

    const results = await Promise.all(promises);
    results.forEach(({ id, data }) => {
      indicatorDataRecord[id] = data;
    });
    return indicatorDataRecord;
  },
  
  async getISMPMI(startDate?: string, endDate?: string): Promise<IndicatorData> {
    return this.getIndicator('ISM-PMI', startDate, endDate);
  },
  async getISMNewOrders(startDate?: string, endDate?: string): Promise<IndicatorData> {
    return this.getIndicator('ISM-NEW-ORDERS', startDate, endDate);
  },
  async getVIXFromYahoo(startDate?: string, endDate?: string): Promise<IndicatorData> { 
    return this.getIndicator('VIX', startDate, endDate);
  },
  async getFREDData(seriesId: string, startDate?: string, endDate?: string): Promise<IndicatorData> {
    return this.getIndicator(seriesId, startDate, endDate);
  },
  async getGoldCopperRatio(startDate?: string, endDate?: string): Promise<IndicatorData> {
    return this.getIndicator('GOLD-COPPER-RATIO', startDate, endDate);
  },
  async getSP500Data(startDate?: string, endDate?: string): Promise<IndicatorData> { 
    return this.getIndicator('SP500', startDate, endDate);
  },

  async getIndicatorsByCategoryName(categoryName: string): Promise<string[]> {
    try {
      const categories = await this.getCategories(); 
      const foundCategory = categories.find(cat => cat.name === categoryName || cat.category_id === categoryName);
      return foundCategory ? foundCategory.indicators : [];
    } catch (error) {
      console.error(`Error fetching indicators for category name ${categoryName}:`, error);
      return [];
    }
  },

  async getCategoryIndicatorData(
    categoryName: string,
    startDate?: string,
    endDate?: string
  ): Promise<Record<string, IndicatorData | null>> {
    try {
      const indicatorIds = await this.getIndicatorsByCategoryName(categoryName);
      if (indicatorIds.length === 0) {
        console.warn(`No indicators found for category by name: ${categoryName}`);
        return {};
      }
      return this.getMultipleIndicators(indicatorIds, startDate, endDate);
    } catch (error) {
      console.error(`Error fetching data for category by name ${categoryName}:`, error);
      throw error; 
    }
  }
};

export default IndicatorService;
