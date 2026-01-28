import { format, isToday, isTomorrow, isThisYear, isBefore, startOfDay, parseISO } from 'date-fns'

export function formatDueDate(dueAt: string | null): string {
  if (!dueAt) return ''
  const date = parseISO(dueAt)
  if (isToday(date)) return 'Today'
  if (isTomorrow(date)) return 'Tomorrow'
  if (isThisYear(date)) return format(date, 'MMM d')
  return format(date, 'MMM d, yyyy')
}

export function isOverdue(dueAt: string | null): boolean {
  if (!dueAt) return false
  return isBefore(parseISO(dueAt), startOfDay(new Date()))
}

export function isDueToday(dueAt: string | null): boolean {
  if (!dueAt) return false
  return isToday(parseISO(dueAt))
}

export function toDateInputValue(iso: string): string {
  return format(parseISO(iso), 'yyyy-MM-dd')
}

export function fromDateInputValue(dateStr: string): string {
  // Convert YYYY-MM-DD to ISO string (noon UTC to avoid timezone edge cases)
  return new Date(dateStr + 'T12:00:00Z').toISOString()
}
