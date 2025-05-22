import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import Dashboard from './pages/Dashboard';
import { IndicatorProvider } from './context/IndicatorContext';
import './App.css';

// Create a theme
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#90caf9',
    },
    secondary: {
      main: '#f48fb1',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <IndicatorProvider>
        <Router>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            {/* Add more routes here later */}
          </Routes>
        </Router>
      </IndicatorProvider>
    </ThemeProvider>
  );
}

export default App;