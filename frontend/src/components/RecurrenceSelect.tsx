import { useState, useRef, useEffect } from 'react'
import { Repeat, Check } from 'lucide-react'
import type { RecurrenceType } from '@/lib/api'
import { useTheme } from '@/hooks/useTheme'
import { cn } from '@/lib/utils'

interface RecurrenceSelectProps {
  recurrenceType: RecurrenceType | null
  recurrenceDays: string[] | null
  onChange: (type: RecurrenceType | null, days: string[] | null) => void
  disabled?: boolean
  size?: 'sm' | 'md'
  align?: 'left' | 'right'
}

const RECURRENCE_OPTIONS: { value: RecurrenceType | null; label: string; description: string }[] = [
  { value: null, label: 'No repeat', description: 'One-time task' },
  { value: 'daily', label: 'Daily', description: 'Every day' },
  { value: 'weekdays', label: 'Weekdays', description: 'Mon through Fri' },
  { value: 'weekly', label: 'Weekly', description: 'Same day each week' },
  { value: 'monthly', label: 'Monthly', description: 'Same date each month' },
  { value: 'custom', label: 'Custom days', description: 'Pick specific days' },
]

const WEEKDAYS = [
  { value: 'mon', label: 'Mo' },
  { value: 'tue', label: 'Tu' },
  { value: 'wed', label: 'We' },
  { value: 'thu', label: 'Th' },
  { value: 'fri', label: 'Fr' },
  { value: 'sat', label: 'Sa' },
  { value: 'sun', label: 'Su' },
]

/** Human-readable summary of recurrence for inline display. */
export function getRecurrenceSummary(
  type: RecurrenceType | null,
  days: string[] | null
): string {
  if (!type) return ''
  switch (type) {
    case 'daily':
      return 'Daily'
    case 'weekdays':
      return 'Weekdays'
    case 'weekly':
      return 'Weekly'
    case 'monthly':
      return 'Monthly'
    case 'custom': {
      if (!days || days.length === 0) return 'Custom'
      const dayLabels = days
        .sort((a, b) => WEEKDAYS.findIndex(w => w.value === a) - WEEKDAYS.findIndex(w => w.value === b))
        .map(d => WEEKDAYS.find(w => w.value === d)?.label ?? d)
      return dayLabels.join(', ')
    }
    default:
      return ''
  }
}

export default function RecurrenceSelect({
  recurrenceType,
  recurrenceDays,
  onChange,
  disabled = false,
  size = 'sm',
  align = 'left',
}: RecurrenceSelectProps) {
  const [isOpen, setIsOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const { resolvedTheme } = useTheme()
  const isDark = resolvedTheme === 'dark'
  const isActive = recurrenceType !== null

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [isOpen])

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      setIsOpen(!isOpen)
    } else if (event.key === 'Escape') {
      setIsOpen(false)
    }
  }

  const handleSelect = (type: RecurrenceType | null) => {
    if (type === 'custom') {
      onChange(type, recurrenceDays ?? [])
    } else {
      onChange(type, null)
      setIsOpen(false)
    }
  }

  const handleDayToggle = (day: string) => {
    const current = recurrenceDays ?? []
    const next = current.includes(day)
      ? current.filter((d) => d !== day)
      : [...current, day]
    onChange('custom', next.length > 0 ? next : [])
  }

  const summary = getRecurrenceSummary(recurrenceType, recurrenceDays)

  const activeColor = isActive
    ? isDark
      ? 'hsl(260, 60%, 65%)'
      : 'hsl(260, 60%, 48%)'
    : undefined
  const activeBg = isActive
    ? isDark
      ? 'hsla(260, 60%, 65%, 0.15)'
      : 'hsla(260, 60%, 48%, 0.1)'
    : undefined

  return (
    <div className="relative" ref={containerRef}>
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        onKeyDown={disabled ? undefined : handleKeyDown}
        disabled={disabled}
        className={cn(
          'flex items-center rounded font-medium transition-all',
          size === 'sm'
            ? 'gap-1 px-1.5 py-0.5 text-xs'
            : 'gap-1.5 px-3 h-9 text-sm border border-gray-200 dark:border-gray-700',
          disabled ? 'opacity-50 cursor-not-allowed' : 'hover:opacity-80',
          !isActive && 'text-muted-foreground',
          'focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-primary'
        )}
        style={isActive ? { backgroundColor: activeBg, color: activeColor } : undefined}
        title={
          disabled
            ? `Recurrence: ${summary || 'none'} (locked)`
            : isActive
              ? `Repeats: ${summary}`
              : 'Set recurrence'
        }
      >
        <Repeat className={size === 'sm' ? 'h-3 w-3' : 'h-4 w-4'} />
        {size === 'sm' && isActive && <span>{summary}</span>}
        {size === 'md' && <span>{isActive ? summary : 'Repeat'}</span>}
      </button>

      {isOpen && (
        <div className={cn(
          'absolute z-50 mt-1 bg-white dark:bg-gray-900 rounded-md shadow-lg border border-gray-200 dark:border-gray-700 py-1 min-w-[180px]',
          align === 'right' ? 'right-0' : 'right-0 sm:right-auto sm:left-0'
        )}>
          {RECURRENCE_OPTIONS.map((option) => {
            const isSelected = option.value === recurrenceType

            return (
              <button
                key={option.value ?? 'none'}
                type="button"
                onClick={() => handleSelect(option.value)}
                className={cn(
                  'w-full flex items-center gap-2 px-3 py-2 text-left',
                  'hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors',
                  isSelected && 'bg-gray-50 dark:bg-gray-800'
                )}
              >
                <div className="flex-1 min-w-0">
                  <span className={cn(
                    'block text-sm',
                    isSelected ? 'font-medium text-foreground' : 'text-gray-700 dark:text-gray-200'
                  )}>
                    {option.label}
                  </span>
                  <span className="block text-xs text-muted-foreground">
                    {option.description}
                  </span>
                </div>
                {isSelected && <Check className="h-3.5 w-3.5 text-primary flex-shrink-0" />}
              </button>
            )
          })}

          {recurrenceType === 'custom' && (
            <div className="px-3 py-2.5 border-t border-gray-200 dark:border-gray-700">
              <div className="flex gap-1">
                {WEEKDAYS.map((day) => {
                  const isDayActive = (recurrenceDays ?? []).includes(day.value)
                  return (
                    <button
                      key={day.value}
                      type="button"
                      onClick={() => handleDayToggle(day.value)}
                      className={cn(
                        'w-8 h-8 rounded-full text-xs font-medium transition-colors',
                        isDayActive
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
                      )}
                    >
                      {day.label}
                    </button>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
