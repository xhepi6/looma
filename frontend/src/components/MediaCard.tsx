import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'
import type { MediaItem, MediaStatus } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Trash2, Film, Tv } from 'lucide-react'

const STATUS_OPTIONS: { value: MediaStatus; label: string }[] = [
  { value: 'want_to_watch', label: 'Want to Watch' },
  { value: 'watching', label: 'Watching' },
  { value: 'watched', label: 'Watched' },
]

const STATUS_COLORS: Record<MediaStatus, string> = {
  want_to_watch: 'text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/50',
  watching: 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/50',
  watched: 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-950/50',
}

interface MediaCardProps {
  item: MediaItem
  onUpdateStatus: (status: MediaStatus) => void
  onDelete: () => void
}

export default function MediaCard({ item, onUpdateStatus, onDelete }: MediaCardProps) {
  const isWatched = item.status === 'watched'

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.9 }}
      className={cn(
        'group flex items-center gap-3 p-3 bg-white dark:bg-gray-800 rounded-lg border shadow-sm transition-shadow',
        isWatched && 'opacity-60'
      )}
    >
      {/* Media type icon */}
      <div className="flex-shrink-0 text-muted-foreground">
        {item.media_type === 'movie' ? (
          <Film className="h-4 w-4" />
        ) : (
          <Tv className="h-4 w-4" />
        )}
      </div>

      {/* Title and metadata */}
      <div className="flex-1 min-w-0">
        <p className={cn('text-sm font-medium truncate', isWatched && 'line-through')}>
          {item.title}
        </p>
        <div className="flex items-center gap-2 mt-0.5">
          <span className={cn(
            'text-[10px] font-medium px-1.5 py-0.5 rounded-full',
            item.media_type === 'movie'
              ? 'text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-950/50'
              : 'text-teal-600 dark:text-teal-400 bg-teal-50 dark:bg-teal-950/50'
          )}>
            {item.media_type === 'movie' ? 'Movie' : 'TV Show'}
          </span>
          {item.added_by_username && (
            <span className="text-[10px] text-muted-foreground">
              {item.added_by_username}
            </span>
          )}
        </div>
      </div>

      {/* Status dropdown */}
      <select
        value={item.status}
        onChange={(e) => onUpdateStatus(e.target.value as MediaStatus)}
        className={cn(
          'text-xs font-medium px-2 py-1 rounded-md border-0 cursor-pointer appearance-none',
          STATUS_COLORS[item.status]
        )}
      >
        {STATUS_OPTIONS.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>

      {/* Delete button */}
      <Button
        variant="ghost"
        size="icon"
        className="h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-destructive"
        onClick={onDelete}
      >
        <Trash2 className="h-3.5 w-3.5" />
      </Button>
    </motion.div>
  )
}
