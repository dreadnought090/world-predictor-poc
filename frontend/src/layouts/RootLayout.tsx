import { Outlet } from 'react-router-dom'
import Header from './Header'

export default function RootLayout() {
  return (
    <div className="min-h-screen relative z-[1]">
      <Header />
      <main className="max-w-[1600px] mx-auto p-4 flex flex-col gap-4">
        <Outlet />
      </main>
    </div>
  )
}
