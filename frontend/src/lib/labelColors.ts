// djb2 hash function
function hashString(str: string): number {
  let hash = 5381
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) + hash) ^ str.charCodeAt(i)
  }
  return Math.abs(hash)
}

const LABEL_HUES = [0, 25, 45, 120, 180, 200, 280, 320, 340]

export function getLabelColor(label: string): { bg: string; text: string } {
  const hash = hashString(label.toLowerCase().trim())
  const hue = LABEL_HUES[hash % LABEL_HUES.length]
  return {
    bg: `hsl(${hue}, 85%, 92%)`,
    text: `hsl(${hue}, 70%, 30%)`,
  }
}
