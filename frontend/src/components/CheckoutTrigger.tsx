// CheckoutTrigger: creates a Razorpay test-mode order and opens Checkout.js modal.
// Failure -> user returns to dashboard -> audit trail polling picks it up within 10s.

import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '@/api/client'

const RZP_KEY_ID = import.meta.env.VITE_RZP_KEY_ID ?? ''

interface OrderResponse {
  order_id: string
  amount: number
  currency: string
  key_id: string
}

declare global {
  interface Window {
    Razorpay: new (options: Record<string, unknown>) => {
      open(): void
      on(event: string, callback: (response: unknown) => void): void
    }
  }
}

async function loadRazorpayScript(): Promise<boolean> {
  return new Promise((resolve) => {
    if (window.Razorpay) { resolve(true); return }
    const script = document.createElement('script')
    script.src = 'https://checkout.razorpay.com/v1/checkout.js'
    script.onload = () => resolve(true)
    script.onerror = () => resolve(false)
    document.body.appendChild(script)
  })
}

export function CheckoutTrigger() {
  const queryClient = useQueryClient()
  const [loading, setLoading] = useState(false)
  const [simulating, setSimulating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [amount, setAmount] = useState(50000) // ₹500 in paise
  const [copiedCard, setCopiedCard] = useState<string | null>(null)

  function copyCard(card: string) {
    navigator.clipboard.writeText(card.replace(/\s+/g, ''))
    setCopiedCard(card)
    setTimeout(() => setCopiedCard(null), 2000)
  }

  async function triggerCheckout() {
    setError(null)
    setNotice(null)
    setLoading(true)

    const loaded = await loadRazorpayScript()
    if (!loaded) {
      setError('Could not load Razorpay checkout script. Check your internet connection.')
      setLoading(false)
      return
    }

    try {
      const order = await apiFetch<OrderResponse>('/create-test-order', {
        method: 'POST',
        body: JSON.stringify({ amount }),
      })

      const rzpKeyId = order.key_id || RZP_KEY_ID

      const rzp = new window.Razorpay({
        key: rzpKeyId,
        amount: order.amount,
        currency: order.currency,
        order_id: order.order_id,
        name: 'Razorpay Recovery Agent',
        description: 'Test failure recovery: pick card or click Failure on OTP screen',
        prefill: {
          name: 'Test Customer',
          email: 'customer@example.com',
          contact: '9876543210',
        },
        theme: { color: '#0F766E' },
        handler: () => {
          setError(
            'Payment succeeded in Razorpay test mode. To test the recovery agent, click "Failure" on the Razorpay mock OTP/bank screen, or use the 1-Click Simulation below.'
          )
        },
        modal: {
          ondismiss: () => {
            setLoading(false)
            // Refresh audit trail in case a failure happened
            queryClient.invalidateQueries({ queryKey: ['audit-trail'] })
          },
        },
      })

      // Listen for payment failure event in Razorpay modal
      rzp.on('payment.failed', (resp: unknown) => {
        setLoading(false)
        const res = resp as { error?: { description?: string; reason?: string; metadata?: { payment_id?: string } } }
        const paymentId = res?.error?.metadata?.payment_id || 'pay_test'
        const reason = res?.error?.description || res?.error?.reason || 'Payment failed'
        setNotice(`Captured payment failure (${paymentId}): "${reason}". Processing recovery decision...`)
        setTimeout(() => {
          queryClient.invalidateQueries({ queryKey: ['audit-trail'] })
        }, 1200)
      })

      rzp.open()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create test order.')
    } finally {
      setLoading(false)
    }
  }

  async function triggerSimulatedFailure() {
    setError(null)
    setNotice(null)
    setSimulating(true)

    try {
      const res = await apiFetch<{
        status: string
        payment_id: string
        action: string
        category: string
        predicted_success_prob: number
        reason: string
      }>('/api/v1/simulate-test-failure', {
        method: 'POST',
        body: JSON.stringify({
          amount,
          error_code: 'bank_technical_error',
          method: 'card',
        }),
      })

      setNotice(
        `✓ Test failure generated: ${res.payment_id} (${res.category}) -> Action: "${res.action}" (P(success)=${(res.predicted_success_prob * 100).toFixed(1)}%). Added to live Audit Trail!`
      )

      queryClient.invalidateQueries({ queryKey: ['audit-trail'] })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to simulate test failure.')
    } finally {
      setSimulating(false)
    }
  }

  return (
    <div className="bg-white border border-surface-border rounded-none overflow-hidden">
      <div className="px-5 py-4 border-b border-surface-border flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-navy">Checkout Demo</h2>
          <div className="text-xs text-muted mt-0.5">Test mode · Real Razorpay modal or 1-click simulation</div>
        </div>
        <span className="text-2xs bg-primary/10 text-primary border border-primary/20 px-2 py-0.5 font-medium">
          Test Mode Active
        </span>
      </div>

      <div className="p-5 space-y-4">
        {/* Test Cards Helper */}
        <div className="text-xs text-muted space-y-2 bg-surface-subtle rounded-none p-3.5 border border-surface-border">
          <div className="flex items-center justify-between">
            <span className="font-semibold text-navy text-xs uppercase tracking-wide">Razorpay Failure Test Cards</span>
            <span className="text-2xs text-muted">Click to copy</span>
          </div>

          <div className="space-y-1.5 font-mono text-2xs">
            <div className="flex items-center justify-between p-1.5 bg-white border border-surface-border">
              <div>
                <span className="text-muted">Insufficient Funds: </span>
                <span className="text-navy font-semibold">4111 1111 1111 1111</span>
              </div>
              <button
                type="button"
                onClick={() => copyCard('4111 1111 1111 1111')}
                className="text-2xs px-2 py-0.5 bg-surface-subtle hover:bg-primary hover:text-white border border-surface-border text-navy transition-colors font-sans"
              >
                {copiedCard === '4111 1111 1111 1111' ? 'Copied!' : 'Copy'}
              </button>
            </div>

            <div className="flex items-center justify-between p-1.5 bg-white border border-surface-border">
              <div>
                <span className="text-muted">Bank Technical Error: </span>
                <span className="text-navy font-semibold">5267 3181 8797 5449</span>
              </div>
              <button
                type="button"
                onClick={() => copyCard('5267 3181 8797 5449')}
                className="text-2xs px-2 py-0.5 bg-surface-subtle hover:bg-primary hover:text-white border border-surface-border text-navy transition-colors font-sans"
              >
                {copiedCard === '5267 3181 8797 5449' ? 'Copied!' : 'Copy'}
              </button>
            </div>
          </div>

          <div className="text-2xs text-muted-dark border-t border-surface-border pt-1.5 flex items-center gap-1.5">
            <span className="font-semibold text-primary">💡 Important:</span>
            <span>On the mock bank screen, click the red <strong>[Failure]</strong> button to trigger recovery.</span>
          </div>
        </div>

        {/* Amount Input */}
        <div className="flex items-center gap-3">
          <label className="text-sm text-muted whitespace-nowrap">Amount (paise):</label>
          <input
            id="checkout-amount"
            type="number"
            value={amount}
            onChange={(e) => setAmount(Math.max(100, Number(e.target.value)))}
            min={100}
            step={100}
            className="w-28 text-sm bg-white text-navy border border-surface-border rounded-none px-2.5 py-1.5 font-mono focus:outline-none focus:ring-1 focus:ring-primary/30 focus:border-primary"
          />
          <span className="text-sm text-muted">= ₹{(amount / 100).toFixed(2)}</span>
        </div>

        {/* Status Alerts */}
        {error && (
          <div className="text-xs p-3 bg-danger/5 border border-danger/20 text-danger leading-relaxed">
            {error}
          </div>
        )}

        {notice && (
          <div className="text-xs p-3 bg-primary/5 border border-primary/30 text-primary-dark font-medium leading-relaxed">
            {notice}
          </div>
        )}

        {/* Action Buttons */}
        <div className="grid sm:grid-cols-2 gap-3 pt-1">
          <button
            id="checkout-trigger-btn"
            type="button"
            onClick={triggerCheckout}
            disabled={loading || simulating}
            className="bg-primary hover:bg-primary-dark text-white text-sm font-semibold py-2.5 px-4 rounded-none disabled:opacity-60 transition-colors duration-150 flex items-center justify-center gap-2"
          >
            {loading ? 'Opening Razorpay…' : 'Trigger Razorpay Modal'}
          </button>

          <button
            id="simulate-failure-btn"
            type="button"
            onClick={triggerSimulatedFailure}
            disabled={loading || simulating}
            className="bg-surface-subtle hover:bg-surface-muted text-navy border border-surface-border text-sm font-semibold py-2.5 px-4 rounded-none disabled:opacity-60 transition-colors duration-150 flex items-center justify-center gap-2"
          >
            {simulating ? 'Simulating…' : '⚡ 1-Click Simulate Failure'}
          </button>
        </div>

        <div className="text-xs text-muted leading-relaxed">
          Both options immediately process through the autonomous ML recovery engine and update the live PostgreSQL Audit Trail and KPI cards above.
        </div>
      </div>
    </div>
  )
}
