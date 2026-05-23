import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import RootLayout from './layouts/RootLayout'

const DashboardPage = lazy(() => import('./pages/DashboardPage'))
const CountryDetailPage = lazy(() => import('./pages/CountryDetailPage'))
const ScenariosPage = lazy(() => import('./pages/ScenariosPage'))
const AgentExplorerPage = lazy(() => import('./pages/AgentExplorerPage'))
const ValidationPage = lazy(() => import('./pages/ValidationPage'))
const PolicyWorkshopPage = lazy(() => import('./pages/PolicyWorkshopPage'))

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
        <Suspense fallback={<div className="p-4 text-xs text-slate-500">Loading...</div>}>
          <Routes>
            <Route element={<RootLayout />}>
              <Route index element={<DashboardPage />} />
              <Route path="/country/:code" element={<CountryDetailPage />} />
              <Route path="/country/:code/agents" element={<AgentExplorerPage />} />
              <Route path="/scenarios" element={<ScenariosPage />} />
              <Route path="/validation" element={<ValidationPage />} />
              <Route path="/policies" element={<PolicyWorkshopPage />} />
            </Route>
          </Routes>
        </Suspense>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
