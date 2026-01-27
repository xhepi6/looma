import { useState, useRef, useEffect } from 'react'
import { Plus } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'

interface LabelInputProps {
  existingLabels: string[]
  onAddLabel: (label: string) => void
  allLabels?: string[]
}

export default function LabelInput({ existingLabels, onAddLabel, allLabels = [] }: LabelInputProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [value, setValue] = useState('')
  const [highlightedIndex, setHighlightedIndex] = useState(-1)
  const inputRef = useRef<HTMLInputElement>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Filter suggestions: match typed text, exclude already added labels
  const suggestions = allLabels.filter(
    (label) =>
      !existingLabels.includes(label) &&
      label.toLowerCase().includes(value.toLowerCase()) &&
      value.trim() !== ''
  )

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isOpen])

  useEffect(() => {
    setHighlightedIndex(-1)
  }, [value])

  const handleSubmit = (labelToAdd?: string) => {
    const trimmed = (labelToAdd || value).trim()
    if (trimmed && !existingLabels.includes(trimmed)) {
      onAddLabel(trimmed)
    }
    setValue('')
    setIsOpen(false)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      if (highlightedIndex >= 0 && suggestions[highlightedIndex]) {
        handleSubmit(suggestions[highlightedIndex])
      } else {
        handleSubmit()
      }
    } else if (e.key === 'Escape') {
      setValue('')
      setIsOpen(false)
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      setHighlightedIndex((prev) =>
        prev < suggestions.length - 1 ? prev + 1 : prev
      )
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setHighlightedIndex((prev) => (prev > 0 ? prev - 1 : -1))
    }
  }

  const handleBlur = (e: React.FocusEvent) => {
    // Don't close if clicking on dropdown
    if (dropdownRef.current?.contains(e.relatedTarget as Node)) {
      return
    }
    handleSubmit()
  }

  if (!isOpen) {
    return (
      <button
        onClick={(e) => {
          e.stopPropagation()
          setIsOpen(true)
        }}
        className="opacity-0 group-hover:opacity-100 inline-flex items-center justify-center h-5 w-5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-all text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
        data-testid="add-label-btn"
      >
        <Plus className="h-3.5 w-3.5" />
      </button>
    )
  }

  return (
    <div className="relative">
      <Input
        ref={inputRef}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onBlur={handleBlur}
        onKeyDown={handleKeyDown}
        onClick={(e) => e.stopPropagation()}
        placeholder="Label"
        className="h-5 w-20 text-xs px-1.5 py-0"
        data-testid="label-input"
      />
      {suggestions.length > 0 && (
        <div
          ref={dropdownRef}
          className="absolute top-full left-0 mt-1 w-32 bg-white dark:bg-gray-800 border rounded-md shadow-lg z-50 max-h-32 overflow-y-auto"
        >
          {suggestions.map((suggestion, index) => (
            <button
              key={suggestion}
              type="button"
              className={cn(
                'w-full text-left px-2 py-1 text-xs hover:bg-gray-100 dark:hover:bg-gray-700',
                highlightedIndex === index && 'bg-gray-100 dark:bg-gray-700'
              )}
              onMouseDown={(e) => {
                e.preventDefault()
                handleSubmit(suggestion)
              }}
              onMouseEnter={() => setHighlightedIndex(index)}
            >
              {suggestion}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
