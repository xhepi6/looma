import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'
import type { Item, ItemPriority } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Check, Trash2, RotateCcw } from 'lucide-react'
import LabelBadge from '@/components/LabelBadge'
import LabelInput from '@/components/LabelInput'
import PrioritySelect from '@/components/PrioritySelect'

interface ItemCardProps {
  item: Item
  onToggle: () => void
  onUpdateLabels: (labels: string[]) => void
  onUpdatePriority: (priority: ItemPriority) => void
  onDelete: () => void
  allLabels?: string[]
}

export default function ItemCard({
  item,
  onToggle,
  onUpdateLabels,
  onUpdatePriority,
  onDelete,
  allLabels = [],
}: ItemCardProps) {
  const isDone = item.status === 'done'

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.9 }}
      className={cn(
        'group flex items-center gap-2 p-3 bg-white dark:bg-gray-800 rounded-lg border shadow-sm transition-shadow',
        isDone && 'opacity-60'
      )}
    >
      {/* Priority selector */}
      <PrioritySelect
        value={item.priority || 'medium'}
        onChange={onUpdatePriority}
      />

      {/* Toggle button */}
      <Button
        variant="ghost"
        size="icon"
        className={cn(
          'h-6 w-6 rounded-full border-2 flex-shrink-0',
          isDone
            ? 'border-green-500 bg-green-500 text-white hover:bg-green-600'
            : 'border-gray-300 hover:border-primary'
        )}
        onClick={onToggle}
      >
        {isDone ? (
          <Check className="h-3 w-3" />
        ) : (
          <span className="sr-only">Mark as done</span>
        )}
      </Button>

      {/* Title and Labels */}
      <div className="flex-1 min-w-0">
        <div className="flex flex-wrap items-center gap-1.5">
          <p
            className={cn(
              'truncate',
              isDone && 'line-through text-muted-foreground'
            )}
          >
            {item.title}
          </p>
          {(item.labels || []).map((label) => (
            <LabelBadge
              key={label}
              label={label}
              onRemove={() => onUpdateLabels((item.labels || []).filter((l) => l !== label))}
            />
          ))}
          <LabelInput
            existingLabels={item.labels || []}
            onAddLabel={(label) => onUpdateLabels([...(item.labels || []), label])}
            allLabels={allLabels}
          />
        </div>
        {/* Completed by indicator */}
        {isDone && item.completed_by_username && (
          <p className="text-xs text-muted-foreground mt-0.5 flex items-center gap-1">
            <Check className="h-3 w-3" />
            Marked as done by {item.completed_by_username}
          </p>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
        {isDone && (
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={onToggle}
            title="Reopen"
          >
            <RotateCcw className="h-3.5 w-3.5" />
          </Button>
        )}
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7 text-destructive hover:text-destructive"
          onClick={onDelete}
          title="Delete"
        >
          <Trash2 className="h-3.5 w-3.5" />
        </Button>
      </div>
    </motion.div>
  )
}
