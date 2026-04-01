import { useLocation, useNavigate } from 'react-router-dom'
import { ListTodo, Tv, MessageCircle, Settings } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Tab {
  label: string
  icon: React.ElementType
  path: string | null
  enabled: boolean
}

const tabs: Tab[] = [
  { label: 'Tasks', icon: ListTodo, path: '/board/1', enabled: true },
  { label: 'Watch', icon: Tv, path: null, enabled: false },
  { label: 'Chat', icon: MessageCircle, path: null, enabled: false },
  { label: 'Settings', icon: Settings, path: '/settings', enabled: true },
]

export default function BottomTabBar() {
  const location = useLocation()
  const navigate = useNavigate()

  const isActive = (tab: Tab) => {
    if (!tab.path) return false
    if (tab.path === '/settings') return location.pathname === '/settings'
    // Match any /board/* path for the Tasks tab
    return location.pathname.startsWith('/board')
  }

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 bg-background pb-[env(safe-area-inset-bottom)]">
      <div className="flex justify-around items-center h-[60px] max-w-lg mx-auto">
        {tabs.map((tab) => {
          const active = isActive(tab)
          const Icon = tab.icon
          return (
            <button
              key={tab.label}
              onClick={() => tab.enabled && tab.path && navigate(tab.path)}
              disabled={!tab.enabled}
              className={cn(
                'flex flex-col items-center justify-center gap-0.5 w-full h-full transition-colors',
                active && 'text-primary',
                !active && tab.enabled && 'text-muted-foreground',
                !tab.enabled && 'opacity-35 pointer-events-none'
              )}
            >
              <Icon className="h-5 w-5" />
              <span className="text-[10px] leading-tight">{tab.label}</span>
            </button>
          )
        })}
      </div>
    </nav>
  )
}
