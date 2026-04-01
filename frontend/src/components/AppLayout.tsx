import { Outlet } from 'react-router-dom'
import BottomTabBar from '@/components/BottomTabBar'

export default function AppLayout() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <div className="pb-[calc(60px+env(safe-area-inset-bottom))]">
        <Outlet />
      </div>
      <BottomTabBar />
    </div>
  )
}
