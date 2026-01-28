import { useState, useRef, useEffect } from 'react'
import { ChevronDown, Minus, ChevronUp, Check } from 'lucide-react'
import type { ItemPriority } from '@/lib/api'
import { getPriorityStyle, getPriorityLabel } from '@/lib/priorityColors'
import { useTheme } from '@/hooks/useTheme'
import { cn } from '@/lib/utils'

interface PrioritySelectProps {
  value: ItemPriority
  onChange: (priority: ItemPriority) => void
}

const priorities: ItemPriority[] = ['high', 'medium', 'low']

const priorityIcons: Record<ItemPriority, typeof ChevronDown> = {
  low: ChevronDown,
  medium: Minus,
  high: ChevronUp,
}

export default function PrioritySelect({ value, onChange }: PrioritySelectProps) {
  const [isOpen, setIsOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const { resolvedTheme } = useTheme()
  const isDark = resolvedTheme === 'dark'

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
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      setIsOpen(!isOpen)
    } else if (event.key === 'Escape') {
      setIsOpen(false)
    } else if (event.key === 'ArrowDown' && isOpen) {
      event.preventDefault()
      const currentIndex = priorities.indexOf(value)
      const nextIndex = (currentIndex + 1) % priorities.length
      onChange(priorities[nextIndex])
    } else if (event.key === 'ArrowUp' && isOpen) {
      event.preventDefault()
      const currentIndex = priorities.indexOf(value)
      const prevIndex = (currentIndex - 1 + priorities.length) % priorities.length
      onChange(priorities[prevIndex])
    }
  }

  const handleSelect = (priority: ItemPriority) => {
    onChange(priority)
    setIsOpen(false)
  }

  const CurrentIcon = priorityIcons[value]
  const currentStyle = getPriorityStyle(value, isDark)

  return (
    <div className="relative" ref={containerRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        onKeyDown={handleKeyDown}
        className={cn(
          'flex items-center gap-0.5 px-1.5 py-0.5 rounded text-xs font-medium transition-all',
          'hover:opacity-80',
          'focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-primary'
        )}
        style={{ backgroundColor: currentStyle.bg, color: currentStyle.text }}
        title={`Priority: ${getPriorityLabel(value)}`}
      >
        <CurrentIcon className="h-3 w-3" />
      </button>

      {isOpen && (
        <div className="absolute z-50 mt-1 left-0 bg-white dark:bg-gray-900 rounded-md shadow-lg border border-gray-200 dark:border-gray-700 py-1 min-w-[120px]">
          {priorities.map((priority) => {
            const Icon = priorityIcons[priority]
            const style = getPriorityStyle(priority, isDark)
            const isSelected = priority === value

            return (
              <button
                key={priority}
                type="button"
                onClick={() => handleSelect(priority)}
                className={cn(
                  'w-full flex items-center gap-2 px-2 py-1.5 text-sm',
                  'text-gray-700 dark:text-gray-200',
                  'hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors',
                  isSelected && 'bg-gray-50 dark:bg-gray-800'
                )}
              >
                <span
                  className="flex items-center justify-center w-5 h-5 rounded"
                  style={{ backgroundColor: style.bg, color: style.text }}
                >
                  <Icon className="h-3 w-3" />
                </span>
                <span className="flex-1 text-left">{getPriorityLabel(priority)}</span>
                {isSelected && (
                  <Check className="h-3.5 w-3.5 text-primary" />
                )}
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}
