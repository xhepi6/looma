import { useAuth } from '@/hooks/useAuth'
import { useTheme } from '@/hooks/useTheme'
import { Button } from '@/components/ui/button'
import { Sun, Moon, LogOut } from 'lucide-react'

export default function SettingsPage() {
  const { logout } = useAuth()
  const { resolvedTheme, setTheme } = useTheme()

  const toggleTheme = () => {
    setTheme(resolvedTheme === 'dark' ? 'light' : 'dark')
  }

  return (
    <main className="max-w-md mx-auto px-4 py-8">
      <h1 className="text-xl font-bold text-foreground mb-6">Settings</h1>

      <div className="space-y-4">
        <div className="flex items-center justify-between p-4 rounded-lg bg-card border border-border">
          <div className="flex items-center gap-3">
            {resolvedTheme === 'dark' ? <Moon className="h-5 w-5 text-muted-foreground" /> : <Sun className="h-5 w-5 text-muted-foreground" />}
            <div>
              <p className="text-sm font-medium text-foreground">Theme</p>
              <p className="text-xs text-muted-foreground">{resolvedTheme === 'dark' ? 'Dark' : 'Light'} mode</p>
            </div>
          </div>
          <Button variant="outline" size="sm" onClick={toggleTheme}>
            {resolvedTheme === 'dark' ? 'Light' : 'Dark'}
          </Button>
        </div>

        <div className="flex items-center justify-between p-4 rounded-lg bg-card border border-border">
          <div className="flex items-center gap-3">
            <LogOut className="h-5 w-5 text-muted-foreground" />
            <div>
              <p className="text-sm font-medium text-foreground">Sign out</p>
              <p className="text-xs text-muted-foreground">End your session</p>
            </div>
          </div>
          <Button variant="outline" size="sm" onClick={logout}>
            Logout
          </Button>
        </div>
      </div>
    </main>
  )
}
