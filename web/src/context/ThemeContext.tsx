/* eslint-disable react-refresh/only-export-components */
import React, { createContext, type ReactNode } from 'react';
import { theme, type Theme } from '../styles/theme';

export interface ThemeContextType {
  theme: Theme;
}

export const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  return <ThemeContext.Provider value={{ theme }}>{children}</ThemeContext.Provider>;
};
