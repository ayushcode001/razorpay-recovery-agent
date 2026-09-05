// FloatingCopilot: Persistent floating chat widget across the entire application.
// Anchored at bottom-right, expandable/collapsible, grounded on PostgreSQL audit trail.

import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useCopilot } from '@/hooks/useApi'

const SUGGESTED_PROMPTS = [
  'How many payments were escalated to human review?',
  'What was the most common error code?',
  'Which category had the highest recovery rate?',
  'How much wasted spend was avoided by the uplift filter?',
]

interface Message {
  role: 'user' | 'assistant'
  content: string
  grounded_count?: number
  model?: string
}

export function FloatingCopilot() {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [showContext, setShowContext] = useState(false)
  const [lastContext, setLastContext] = useState<unknown>(null)
  const [showHint, setShowHint] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const copilot = useCopilot()

  // First session hint bubble
  useEffect(() => {
    const dismissed = sessionStorage.getItem('copilot_hint_dismissed')
    if (!dismissed) {
      const timer = setTimeout(() => setShowHint(true), 1200)
      return () => clearTimeout(timer)
    }
  }, [])

  function dismissHint() {
    setShowHint(false)
    sessionStorage.setItem('copilot_hint_dismissed', 'true')
  }

  function toggleOpen() {
    if (!isOpen && showHint) {
      dismissHint()
    }
    setIsOpen(v => !v)
  }

  useEffect(() => {
    if (isOpen) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, isOpen])

  async function sendMessage(question: string) {
    if (!question.trim()) return
    const q = question.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: q }])

    try {
      const res = await copilot.mutateAsync(q)
      setLastContext(res.context_used)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: res.answer,
        grounded_count: res.grounded_record_count,
        model: res.model_used,
      }])
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Unknown error'
      const isRateLimited = msg.includes('429')
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: isRateLimited
          ? 'Rate limited. Try again in a moment.'
          : `Error: ${msg}`,
      }])
    }
  }

  return (
    <aside aria-label="Copilot Assistant" className="fixed bottom-6 right-6 z-50 flex flex-col items-end">
      {/* ── FIRST-SESSION HINT BUBBLE ── */}
      <AnimatePresence>
        {!isOpen && showHint && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 6, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="mb-3 max-w-xs bg-navy text-white text-xs rounded-xl p-3.5 shadow-xl border border-navy-light relative flex items-start gap-2.5"
          >
            <div className="flex-1">
              <div className="font-semibold text-white mb-0.5">Audit Trail Copilot</div>
              <p className="text-muted-lighter text-2xs leading-relaxed">
                Ask anything about failure decisions, uplift models, or recovery telemetry.
              </p>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation()
                dismissHint()
              }}
              className="text-muted-lighter hover:text-white transition-colors text-xs p-0.5"
              aria-label="Dismiss hint"
            >
              ✕
            </button>
            <div className="absolute -bottom-1.5 right-6 w-3 h-3 bg-navy border-r border-b border-navy-light rotate-45" />
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── EXPANDED CHAT PANEL ── */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ duration: 0.25, ease: 'easeOut' }}
            className="mb-4 w-[calc(100vw-32px)] sm:w-[380px] max-h-[82vh] sm:max-h-[580px] bg-white border border-surface-border rounded-none shadow-lg overflow-hidden flex flex-col"
          >
            {/* Header */}
            <div className="px-4 py-3 bg-navy text-white flex items-center justify-between">
              <h2 className="text-sm font-semibold text-white">Copilot</h2>

              <div className="flex items-center gap-1.5">
                {Boolean(lastContext) && (
                  <button
                    onClick={() => setShowContext(v => !v)}
                    className="text-3xs font-mono text-muted-lighter hover:text-white transition-colors duration-150 border border-white/15 px-1.5 py-1 rounded-none"
                    title="Inspect grounding payload"
                  >
                    {showContext ? 'Hide' : 'Context'}
                  </button>
                )}
                <button
                  onClick={() => setIsOpen(false)}
                  className="w-7 h-7 rounded-none hover:bg-white/10 flex items-center justify-center text-muted-lighter hover:text-white transition-colors duration-150 text-sm"
                  aria-label="Close copilot"
                >
                  ✕
                </button>
              </div>
            </div>

            {/* Suggested prompt chips */}
            {messages.length === 0 && (
              <div className="p-3 bg-surface-subtle border-b border-surface-border flex flex-wrap gap-1.5">
                {SUGGESTED_PROMPTS.map((p) => (
                  <button
                    key={p}
                    onClick={() => sendMessage(p)}
                    className="text-2xs text-left text-navy bg-white border border-surface-border hover:border-surface-border-dark px-2.5 py-1.5 rounded-none transition-colors duration-150"
                  >
                    {p}
                  </button>
                ))}
              </div>
            )}

            {/* Messages Thread */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3.5 min-h-[220px] max-h-[340px] text-xs">
              {messages.length === 0 && (
                <div className="text-muted text-center py-8">
                  <div>Ask anything about payment recovery, failure reasons, or causal uplift.</div>
                </div>
              )}
              {messages.map((m, i) => (
                <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[85%] rounded-none px-3.5 py-2.5 leading-relaxed ${
                    m.role === 'user'
                      ? 'bg-primary text-white'
                      : 'bg-surface-subtle border border-surface-border text-navy'
                  }`}>
                    <div className="whitespace-pre-wrap">{m.content}</div>
                    {m.grounded_count != null && m.role === 'assistant' && (
                      <div className="mt-1 text-3xs opacity-60 flex items-center gap-1 font-mono">
                        <span>{m.grounded_count} records</span>
                        <span>·</span>
                        <span>{m.model ?? 'Gemini Flash'}</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {copilot.isPending && (
                <div className="flex justify-start">
                  <div className="bg-surface-subtle border border-surface-border rounded-none px-3.5 py-2">
                    <span className="inline-flex gap-1.5 items-center text-xs text-muted">
                      <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
                      <span className="text-3xs text-muted ml-1">Analyzing audit trail...</span>
                    </span>
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>

            {/* Raw Context Viewer */}
            {showContext && Boolean(lastContext) && (
              <div className="border-t border-surface-border bg-surface-muted max-h-36 overflow-y-auto">
                <div className="px-3 py-1 bg-surface-subtle border-b border-surface-border text-3xs font-mono text-muted flex justify-between items-center">
                  <span>GROUNDED CONTEXT PAYLOAD</span>
                  <button onClick={() => setShowContext(false)} className="hover:text-navy">✕</button>
                </div>
                <pre className="p-3 text-3xs font-mono text-muted overflow-x-auto">
                  {JSON.stringify(lastContext, null, 2)}
                </pre>
              </div>
            )}

            {/* Input Form */}
            <div className="p-3 border-t border-surface-border bg-white flex gap-2">
              <input
                id="floating-copilot-input"
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage(input)}
                placeholder="Ask about payment recoveries…"
                maxLength={500}
                disabled={copilot.isPending}
                className="flex-1 text-xs border border-surface-border rounded-none px-3 py-2 outline-none focus:border-primary transition-colors duration-150 placeholder:text-muted-light disabled:opacity-50"
              />
              <button
                id="floating-copilot-send"
                onClick={() => sendMessage(input)}
                disabled={copilot.isPending || !input.trim()}
                className="bg-primary text-white text-xs font-semibold px-3.5 py-2 rounded-none hover:bg-primary-dark disabled:opacity-50 transition-colors duration-150 shrink-0"
              >
                Send
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── FLOATING ACTION BUTTON (COLLAPSED) ── */}
      <button
        id="floating-copilot-btn"
        onClick={toggleOpen}
        aria-label={isOpen ? "Close copilot chat" : "Open copilot chat"}
        className={`w-12 h-12 sm:w-13 sm:h-13 rounded-none flex items-center justify-center transition-colors duration-150 relative ${
          isOpen
            ? 'bg-navy text-white'
            : 'bg-primary text-white hover:bg-primary-dark'
        }`}
      >
        <span className="sr-only">{isOpen ? "Close Copilot" : "Open Copilot"}</span>
        {isOpen ? (
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        ) : (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            <circle cx="9" cy="10" r="1" fill="currentColor" />
            <circle cx="12" cy="10" r="1" fill="currentColor" />
            <circle cx="15" cy="10" r="1" fill="currentColor" />
          </svg>
        )}

        {/* Live indicator dot */}
        <span className="absolute top-0 right-0 w-3.5 h-3.5 rounded-full bg-success border-2 border-white" />
      </button>
    </aside>
  )
}
