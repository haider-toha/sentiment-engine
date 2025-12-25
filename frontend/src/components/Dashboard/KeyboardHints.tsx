'use client'

import { useState } from 'react'
import { Keyboard, X } from 'lucide-react'
import { Button } from '@/components/ui/button'

export default function KeyboardHints() {
  const [isOpen, setIsOpen] = useState(false)

  const shortcuts = [
    { keys: ['⌘', 'R'], action: 'Refresh data' },
    { keys: ['Esc'], action: 'Close panel' },
    { keys: ['↑', '↓'], action: 'Navigate' },
  ]

  return (
    <div className="relative">
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setIsOpen(!isOpen)}
        className="h-8 gap-1.5 px-2 text-text-muted hover:text-foreground"
      >
        <Keyboard className="h-3 w-3" />
        <span className="hidden text-2xs sm:inline">Keys</span>
      </Button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
          <div className="absolute right-0 top-full z-50 mt-1.5 w-48 origin-top-right animate-scale-in">
            <div className="overflow-hidden rounded-lg border border-border bg-surface-elevated shadow-medium">
              <div className="flex items-center justify-between border-b border-border px-3 py-2">
                <span className="text-xs font-medium">Shortcuts</span>
                <button
                  onClick={() => setIsOpen(false)}
                  className="text-text-muted transition-colors hover:text-foreground"
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
              <div className="p-1.5">
                {shortcuts.map((shortcut, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between rounded px-2 py-1.5 transition-colors hover:bg-surface"
                  >
                    <span className="text-2xs text-text-secondary">{shortcut.action}</span>
                    <div className="flex items-center gap-0.5">
                      {shortcut.keys.map((key, j) => (
                        <span key={j} className="kbd">
                          {key}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
