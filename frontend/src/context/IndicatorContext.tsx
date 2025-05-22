// frontend/src/context/IndicatorContext.tsx

import React, { createContext, useState, useContext, ReactNode, useCallback, useMemo } from 'react'; // Import useMemo
import { IndicatorData } from '../components/IndicatorCard';

interface IndicatorContextType {
  indicators: Record<string, IndicatorData | null>;
  setIndicator: (key: string, data: IndicatorData | null) => void;
  calculateMarketStatus: () => { bullBear: 'BULL' | 'BEAR' | 'NEUTRAL', riskOnOff: 'RISK-ON' | 'RISK-OFF' | 'NEUTRAL' };
}

const IndicatorContext = createContext<IndicatorContextType | undefined>(undefined);

export const IndicatorProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [indicators, setIndicators] = useState<Record<string, IndicatorData | null>>({});

  // This is already stable - which is good!
  const setIndicator = useCallback((key: string, data: IndicatorData | null) => {
    setIndicators(prev => ({
      ...prev,
      [key]: data
    }));
  }, []);

  const calculateMarketStatus = useCallback(() => {
    let bullishCount = 0;
    let bearishCount = 0;
    let neutralCount = 0;
    let riskOnCount = 0;
    let riskOffCount = 0;

    Object.entries(indicators).forEach(([key, indicator]) => {
      if (!indicator) return;
      const lastValue = indicator.lastValue !== undefined ? indicator.lastValue : (indicator.data?.length > 0 ? indicator.data[indicator.data.length - 1].value : undefined);

      // Ensure thresholds are numbers or explicitly handle if they can be undefined
      const bullishThreshold = typeof indicator.bullishThreshold === 'number' ? indicator.bullishThreshold : undefined;
      const bearishThreshold = typeof indicator.bearishThreshold === 'number' ? indicator.bearishThreshold : undefined;

      if (lastValue === undefined || bullishThreshold === undefined || bearishThreshold === undefined) {
        neutralCount++;
        return;
      }

      if (lastValue >= bullishThreshold) {
        bullishCount++;
      } else if (lastValue <= bearishThreshold) {
        bearishCount++;
      } else {
        neutralCount++;
      }

      // Simplified risk logic based on your existing structure, ensure thresholds are valid
      if (key.includes('ISM')) {
        if (lastValue >= 50) riskOnCount++; else riskOffCount++;
      } else if (key === 'GOLD-COPPER-RATIO') {
        if (bullishThreshold !== undefined && lastValue <= bullishThreshold) riskOnCount++;
        else if (bearishThreshold !== undefined && lastValue >= bearishThreshold) riskOffCount++;
      } else if (key === 'FRED-T10Y2Y') {
        if (lastValue > 0) riskOnCount++; else riskOffCount++;
      } else if (key === 'FRED-VIXCLS') {
        if (bullishThreshold !== undefined && lastValue >= bullishThreshold) riskOnCount++;
        else if (bearishThreshold !== undefined && lastValue <= bearishThreshold) riskOffCount++;
      } else if (key === 'FRED-M2SL') {
        if (bullishThreshold !== undefined && lastValue >= bullishThreshold) riskOnCount++;
        else if (bearishThreshold !== undefined && lastValue <= bearishThreshold) riskOffCount++;
      } else if (key.startsWith('FRED-')) {
        if (bullishThreshold !== undefined && lastValue >= bullishThreshold) riskOnCount++;
        else if (bearishThreshold !== undefined && lastValue <= bearishThreshold) riskOffCount++;
      }
    });

    let bullBear: 'BULL' | 'BEAR' | 'NEUTRAL';
    let riskOnOff: 'RISK-ON' | 'RISK-OFF' | 'NEUTRAL';
    const totalValuedIndicators = bullishCount + bearishCount + neutralCount;

    if (totalValuedIndicators === 0) {
      bullBear = 'NEUTRAL';
      riskOnOff = 'NEUTRAL';
    } else {
      const bullishScore = bullishCount / totalValuedIndicators;
      const bearishScore = bearishCount / totalValuedIndicators;

      if (bullishScore > 0.6) bullBear = 'BULL';
      else if (bearishScore > 0.6) bullBear = 'BEAR';
      else if (bullishCount > bearishCount) bullBear = 'BULL';
      else if (bearishCount > bullishCount) bullBear = 'BEAR';
      else bullBear = 'NEUTRAL';

      if (riskOnCount > riskOffCount) riskOnOff = 'RISK-ON';
      else if (riskOffCount > riskOnCount) riskOnOff = 'RISK-OFF';
      else riskOnOff = 'NEUTRAL';
    }
    return { bullBear, riskOnOff };
  }, [indicators]);

  // FIX: Memoize the context value object
  const contextValue = useMemo(() => ({
    indicators,
    setIndicator,         // Stable reference from its own useCallback
    calculateMarketStatus // Reference changes when `indicators` state changes
  }), [indicators, setIndicator, calculateMarketStatus]);
  // `setIndicator` is stable. `calculateMarketStatus` changes when `indicators` changes.
  // So, `contextValue` will get a new reference primarily when `indicators` (data) changes.

  return (
    <IndicatorContext.Provider value={contextValue}>
      {children}
    </IndicatorContext.Provider>
  );
};

export const useIndicators = () => {
  const context = useContext(IndicatorContext);
  if (context === undefined) {
    throw new Error('useIndicators must be used within an IndicatorProvider');
  }
  return context;
};