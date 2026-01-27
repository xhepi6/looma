import { X } from 'lucide-react'
import { getLabelColor } from '@/lib/labelColors'
import { cn } from '@/lib/utils'

interface LabelBadgeProps {
  label: string
  onRemove?: () => void
  onClick?: () => void
  isSelected?: boolean
}

export default function LabelBadge({ label, onRemove, onClick, isSelected }: LabelBadgeProps) {
  const colors = getLabelColor(label)

  const handleClick = onClick
    ? (e: React.MouseEvent) => {
        e.stopPropagation()
        onClick()
      }
    : undefined

  return (
    <span
      className={cn(
        'group inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-xs font-medium whitespace-nowrap',
        onClick && 'cursor-pointer hover:ring-2 hover:ring-offset-1 hover:ring-gray-300',
        isSelected && 'ring-2 ring-offset-1 ring-primary'
      )}
      style={{ backgroundColor: colors.bg, color: colors.text }}
      onClick={handleClick}
      data-testid={onClick ? `filter-label-${label}` : undefined}
    >
      {label}
      {onRemove && (
        <button
          onClick={(e) => {
            e.stopPropagation()
            onRemove()
          }}
          className="opacity-0 group-hover:opacity-100 hover:bg-black/10 rounded transition-opacity ml-0.5 -mr-0.5"
        >
          <X className="h-3 w-3" />
        </button>
      )}
    </span>
  )
}
