import { QueryClient, QueryClientProvider } from 'react-query';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import ErrorBoundary from './components/ErrorBoundary';
import Dashboard from './pages/Dashboard';
import SectorRotationPage from './pages/SectorRotationPage';
import StockScreenerPage from './pages/StockScreenerPage';
import SectorComparisonPage from './pages/SectorComparisonPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter
          future={{
            v7_startTransition: true,
            v7_relativeSplatPath: true,
          }}
        >
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/sector-rotation" element={<SectorRotationPage />} />
            <Route path="/stock-screener" element={<StockScreenerPage />} />
            <Route path="/sector-comparison" element={<SectorComparisonPage />} />
          </Routes>
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;
