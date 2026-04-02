import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useAuth } from '@/hooks/useAuth'
import { useTheme } from '@/hooks/useTheme'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import * as api from '@/lib/api'
import { User, Sun, Moon, Lock, LogOut } from 'lucide-react'

export default function SettingsPage() {
  const { user, logout } = useAuth()
  const { resolvedTheme, setTheme } = useTheme()
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const toggleTheme = () => {
    setTheme(resolvedTheme === 'dark' ? 'light' : 'dark')
  }

  const passwordMutation = useMutation({
    mutationFn: () => api.changePassword(newPassword, confirmPassword),
    onSuccess: () => {
      setNewPassword('')
      setConfirmPassword('')
      setMessage({ type: 'success', text: 'Password updated successfully' })
    },
    onError: (error: Error) => {
      setMessage({ type: 'error', text: error.message })
    },
  })

  const handlePasswordSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setMessage(null)
    passwordMutation.mutate()
  }

  const memberSince = user?.created_at
    ? new Date(user.created_at).toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' })
    : null

  return (
    <main className="max-w-md mx-auto px-4 py-8">
      <h1 className="text-xl font-bold text-foreground mb-6">Settings</h1>

      <div className="space-y-4">
        {/* User info */}
        <div className="p-4 rounded-lg bg-card border border-border">
          <div className="flex items-center gap-3">
            <User className="h-5 w-5 text-muted-foreground" />
            <div>
              <p className="text-sm font-medium text-foreground">{user?.username}</p>
              {memberSince && (
                <p className="text-xs text-muted-foreground">Member since {memberSince}</p>
              )}
            </div>
          </div>
        </div>

        {/* Theme toggle */}
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

        {/* Password change */}
        <form onSubmit={handlePasswordSubmit} className="p-4 rounded-lg bg-card border border-border space-y-3">
          <div className="flex items-center gap-3 mb-1">
            <Lock className="h-5 w-5 text-muted-foreground" />
            <p className="text-sm font-medium text-foreground">Change password</p>
          </div>
          <Input
            type="password"
            placeholder="New password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
          />
          <Input
            type="password"
            placeholder="Confirm password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
          />
          {message && (
            <p className={`text-xs ${message.type === 'success' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
              {message.text}
            </p>
          )}
          <Button
            type="submit"
            size="sm"
            disabled={!newPassword || !confirmPassword || passwordMutation.isPending}
          >
            {passwordMutation.isPending ? 'Updating...' : 'Update password'}
          </Button>
        </form>

        {/* Sign out */}
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
