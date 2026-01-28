import { useState, useRef, useEffect } from 'react'
import { Calendar } from 'lucide-react'
import { cn } from '@/lib/utils'
import { formatDueDate, isOverdue, isDueToday } from '@/lib/dateUtils'
import CalendarPicker from '@/components/ui/calendar'
import { parseISO } from 'date-fns'

interface DueDatePickerProps {
  value: string | null
  onChange: (dueAt: string | null) => void
  disabled?: boolean
}

export default function DueDatePicker({ value, onChange, disabled = false }: DueDatePickerProps) {
  const [isOpen, setIsOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen])

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Escape') {
      setIsOpen(false)
    }
  }

  const handleDateSelect = (date: Date) => {
    // noon UTC to avoid timezone edge cases
    const utc = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate(), 12))
    onChange(utc.toISOString())
    setIsOpen(false)
  }

  const handleClear = () => {
    onChange(null)
    setIsOpen(false)
  }

  const overdue = isOverdue(value)
  const today = isDueToday(value)
  const label = formatDueDate(value)

  return (
    <div className="relative" ref={containerRef} onKeyDown={handleKeyDown}>
      {value ? (
        <button
          type="button"
          onClick={() => !disabled && setIsOpen(!isOpen)}
          disabled={disabled}
          className={cn(
            'flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-medium transition-all',
            disabled
              ? 'opacity-50 cursor-not-allowed'
              : 'hover:opacity-80',
            overdue && !disabled
              ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
              : today
                ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
                : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
          )}
          title={disabled ? `Due: ${label} (locked)` : `Due: ${label}`}
        >
          <Calendar className="h-3 w-3" />
          {label}
        </button>
      ) : (
        <button
          type="button"
          onClick={() => !disabled && setIsOpen(!isOpen)}
          disabled={disabled}
          className={cn(
            'flex items-center gap-1 px-1.5 py-0.5 rounded text-xs text-muted-foreground transition-all',
            disabled
              ? 'hidden'
              : 'opacity-0 group-hover:opacity-100 hover:bg-gray-100 dark:hover:bg-gray-700'
          )}
          title="Set due date"
        >
          <Calendar className="h-3 w-3" />
        </button>
      )}

      {isOpen && (
        <div className="absolute z-50 mt-1 left-0 bg-white dark:bg-gray-900 rounded-md shadow-lg border border-gray-200 dark:border-gray-700 p-3">
          <CalendarPicker
            selected={value ? parseISO(value) : null}
            onSelect={handleDateSelect}
          />
          {value && (
            <button
              type="button"
              onClick={handleClear}
              className="w-full mt-1.5 px-2 py-1 text-xs text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors"
            >
              Clear due date
            </button>
          )}
        </div>
      )}
    </div>
  )
}
