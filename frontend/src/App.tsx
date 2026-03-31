import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import RootLayout from './layouts/RootLayout'
import DashboardPage from './pages/DashboardPage'
import CountryDetailPage from './pages/CountryDetailPage'
import ScenariosPage from './pages/ScenariosPage'
import AgentExplorerPage from './pages/AgentExplorerPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 10000,
    },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<RootLayout />}>
            <Route index element={<DashboardPage />} />
            <Route path="/country/:code" element={<CountryDetailPage />} />
            <Route path="/country/:code/agents" element={<AgentExplorerPage />} />
            <Route path="/scenarios" element={<ScenariosPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
