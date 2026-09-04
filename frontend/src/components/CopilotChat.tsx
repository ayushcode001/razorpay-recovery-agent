// CopilotChat: Q&A over the audit trail via Gemini.
// Shows grounding badge, toggleable raw context viewer.

import { useState, useRef, useEffect } from 'react'
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

export function CopilotChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [showContext, setShowContext] = useState(false)
  const [lastContext, setLastContext] = useState<unknown>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const copilot = useCopilot()

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

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
    <div className="bg-white border border-surface-border rounded-lg shadow-sm overflow-hidden flex flex-col">
      <div className="px-5 py-4 border-b border-surface-border flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-navy">Copilot</h2>
          <div className="text-xs text-muted mt-0.5">Read-only · Grounded on audit trail · Cannot take actions</div>
        </div>
        {Boolean(lastContext) && (
          <button
            onClick={() => setShowContext(v => !v)}
            className="text-2xs font-medium text-muted hover:text-navy transition-colors border border-surface-border px-2 py-1 rounded"
          >
            {showContext ? 'Hide' : 'Show'} Context
          </button>
        )}
      </div>

      {/* Suggested prompts */}
      {messages.length === 0 && (
        <div className="px-5 py-3 flex flex-wrap gap-2 border-b border-surface-border">
          {SUGGESTED_PROMPTS.map((p) => (
            <button
              key={p}
              onClick={() => sendMessage(p)}
              className="text-xs text-primary border border-primary-light bg-primary-50 hover:bg-primary-light px-2.5 py-1 rounded transition-colors text-left"
            >
              {p}
            </button>
          ))}
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-5 space-y-4 max-h-80">
        {messages.length === 0 && (
          <div className="text-sm text-muted text-center py-4">Ask anything about the audit trail.</div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] rounded-lg px-4 py-2.5 text-sm leading-relaxed ${
              m.role === 'user'
                ? 'bg-primary text-white'
                : 'bg-surface-subtle border border-surface-border text-navy'
            }`}>
              {m.content}
              {m.grounded_count != null && m.role === 'assistant' && (
                <div className="mt-1.5 text-2xs opacity-60">
                  {m.grounded_count} records · {m.model ?? 'Gemini'}
                </div>
              )}
            </div>
          </div>
        ))}
        {copilot.isPending && (
          <div className="flex justify-start">
            <div className="bg-surface-subtle border border-surface-border rounded-lg px-4 py-2.5">
              <span className="inline-flex gap-1 items-center text-xs text-muted">
                <span className="w-1.5 h-1.5 rounded-full bg-muted animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-1.5 h-1.5 rounded-full bg-muted animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-1.5 h-1.5 rounded-full bg-muted animate-bounce" style={{ animationDelay: '300ms' }} />
              </span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Raw context viewer */}
      {showContext && Boolean(lastContext) && (
        <div className="border-t border-surface-border">
          <pre className="p-4 text-2xs font-mono text-muted overflow-x-auto max-h-48 bg-surface-muted">
            {JSON.stringify(lastContext, null, 2)}
          </pre>
        </div>
      )}

      {/* Input */}
      <div className="border-t border-surface-border p-4 flex gap-2">
        <input
          id="copilot-input"
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage(input)}
          placeholder="Ask about the audit trail…"
          maxLength={500}
          disabled={copilot.isPending}
          className="flex-1 text-sm border border-surface-border rounded-md px-3 py-2 outline-none focus:ring-1 focus:ring-primary/30 focus:border-primary transition-colors placeholder:text-muted-light disabled:opacity-50"
        />
        <button
          id="copilot-send"
          onClick={() => sendMessage(input)}
          disabled={copilot.isPending || !input.trim()}
          className="bg-primary text-white text-sm font-medium px-4 py-2 rounded-md hover:bg-primary-dark disabled:opacity-50 transition-colors whitespace-nowrap"
        >
          Send
        </button>
      </div>
    </div>
  )
}
