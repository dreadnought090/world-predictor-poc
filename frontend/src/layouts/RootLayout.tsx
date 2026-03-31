import { Outlet } from 'react-router-dom'
import { Toaster } from 'sonner'
import Header from './Header'

export default function RootLayout() {
  return (
    <div className="min-h-screen relative z-[1]">
      <Header />
      <main className="max-w-[1600px] mx-auto p-4 flex flex-col gap-4">
        <Outlet />
      </main>
      <Toaster
        position="bottom-right"
        theme="dark"
        toastOptions={{
          style: {
            background: '#0f1724',
            border: '1px solid rgba(255,255,255,0.08)',
            color: '#e2e8f0',
            fontSize: '13px',
          },
        }}
      />
    </div>
  )
}
