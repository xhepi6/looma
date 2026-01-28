import type { ItemPriority } from './api'

interface PriorityStyle {
  bg: string
  text: string
  darkBg: string
  darkText: string
}

const priorityStyles: Record<ItemPriority, PriorityStyle> = {
  low: {
    bg: 'hsl(210, 40%, 92%)',
    text: 'hsl(210, 40%, 35%)',
    darkBg: 'hsl(210, 50%, 32%)',
    darkText: 'hsl(210, 60%, 85%)',
  },
  medium: {
    bg: 'hsl(45, 90%, 88%)',
    text: 'hsl(40, 80%, 30%)',
    darkBg: 'hsl(40, 70%, 32%)',
    darkText: 'hsl(45, 100%, 85%)',
  },
  high: {
    bg: 'hsl(0, 85%, 92%)',
    text: 'hsl(0, 70%, 35%)',
    darkBg: 'hsl(0, 65%, 35%)',
    darkText: 'hsl(0, 100%, 88%)',
  },
}

export function getPriorityStyle(priority: ItemPriority, isDark: boolean = false): { bg: string; text: string } {
  const style = priorityStyles[priority]
  return {
    bg: isDark ? style.darkBg : style.bg,
    text: isDark ? style.darkText : style.text,
  }
}

export function getPriorityLabel(priority: ItemPriority): string {
  const labels: Record<ItemPriority, string> = {
    low: 'Low',
    medium: 'Medium',
    high: 'High',
  }
  return labels[priority]
}
