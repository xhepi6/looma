import { ChevronDown, Minus, ChevronUp } from 'lucide-react'
import type { ItemPriority } from '@/lib/api'
import { getPriorityStyle, getPriorityLabel } from '@/lib/priorityColors'
import { useTheme } from '@/hooks/useTheme'
import { cn } from '@/lib/utils'

interface PriorityBadgeProps {
  priority: ItemPriority
  showLabel?: boolean
  className?: string
}

const priorityIcons: Record<ItemPriority, typeof ChevronDown> = {
  low: ChevronDown,
  medium: Minus,
  high: ChevronUp,
}

export default function PriorityBadge({ priority, showLabel = false, className }: PriorityBadgeProps) {
  const { resolvedTheme } = useTheme()
  const isDark = resolvedTheme === 'dark'
  const style = getPriorityStyle(priority, isDark)
  const Icon = priorityIcons[priority]

  return (
    <span
      className={cn(
        'inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-xs font-medium',
        className
      )}
      style={{ backgroundColor: style.bg, color: style.text }}
    >
      <Icon className="h-3 w-3" />
      {showLabel && <span>{getPriorityLabel(priority)}</span>}
    </span>
  )
}
