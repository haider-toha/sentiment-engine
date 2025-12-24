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
        className="gap-1.5 text-text-muted hover:text-foreground h-8 px-2"
      >
        <Keyboard className="w-3 h-3" />
        <span className="hidden sm:inline text-2xs">Keys</span>
      </Button>

      {isOpen && (
        <>
          <div 
            className="fixed inset-0 z-40" 
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 top-full mt-1.5 z-50 w-48 animate-scale-in origin-top-right">
            <div className="bg-surface-elevated rounded-lg border border-border shadow-medium overflow-hidden">
              <div className="flex items-center justify-between px-3 py-2 border-b border-border">
                <span className="text-xs font-medium">Shortcuts</span>
                <button 
                  onClick={() => setIsOpen(false)}
                  className="text-text-muted hover:text-foreground transition-colors"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
              <div className="p-1.5">
                {shortcuts.map((shortcut, i) => (
                  <div 
                    key={i}
                    className="flex items-center justify-between px-2 py-1.5 rounded hover:bg-surface transition-colors"
                  >
                    <span className="text-2xs text-text-secondary">{shortcut.action}</span>
                    <div className="flex items-center gap-0.5">
                      {shortcut.keys.map((key, j) => (
                        <span key={j} className="kbd">{key}</span>
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
