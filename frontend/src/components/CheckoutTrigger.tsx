// CheckoutTrigger: creates a Razorpay test-mode order and opens Checkout.js modal.
// Failure → user returns to dashboard → audit trail polling picks it up within 10s.

import { useState } from 'react'
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
    Razorpay: new (options: Record<string, unknown>) => { open(): void }
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
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [amount, setAmount] = useState(50000) // ₹500 in paise

  async function triggerCheckout() {
    setError(null)
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
        description: 'Test payment: use failure card to trigger recovery flow',
        prefill: {
          name: 'Test User',
          email: 'test@example.com',
          contact: '9000000000',
        },
        theme: { color: '#C9962A' },
        handler: () => {
          // Rare: payment success in test mode
          setError('Payment succeeded (unexpected in demo). Try a failure card.')
        },
        modal: {
          ondismiss: () => {
            setLoading(false)
          },
        },
      })

      rzp.open()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create test order.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card-dark rounded-lg shadow-sm overflow-hidden border border-white/[0.08]">
      <div className="px-5 py-4 border-b border-white/[0.08]">
        <h2 className="text-base font-semibold text-dark-cream">Checkout Demo</h2>
        <div className="text-xs text-dark-muted mt-0.5">Test mode · Use Razorpay failure card numbers</div>
      </div>
      <div className="p-5 space-y-4">
        <div className="text-sm text-dark-muted space-y-1 bg-white/[0.025] rounded-md p-3 font-mono text-xs border border-white/[0.08]">
          <div className="font-semibold text-dark-cream text-base font-sans mb-2">Failure test cards</div>
          <div><span className="text-dark-muted">Insufficient Funds:</span> <span className="text-dark-cream">4111 1111 1111 1111</span></div>
          <div><span className="text-dark-muted">Technical Error:</span>    <span className="text-dark-cream">5267 3181 8797 5449</span></div>
          <div><span className="text-dark-muted">CVV:</span> any 3 digits &nbsp; Expiry: any future date</div>
        </div>

        <div className="flex items-center gap-3">
          <label className="text-sm text-dark-muted whitespace-nowrap">Amount (paise):</label>
          <input
            id="checkout-amount"
            type="number"
            value={amount}
            onChange={(e) => setAmount(Math.max(100, Number(e.target.value)))}
            min={100}
            step={100}
            className="w-28 text-sm bg-white/[0.04] text-dark-cream border border-white/[0.1] rounded px-2.5 py-1.5 font-mono focus:outline-none focus:ring-1 focus:ring-amber/40 focus:border-amber"
          />
          <span className="text-sm text-dark-muted">= ₹{(amount / 100).toFixed(2)}</span>
        </div>

        {error && <div className="text-sm text-rose-400">{error}</div>}

        <button
          id="checkout-trigger-btn"
          onClick={triggerCheckout}
          disabled={loading}
          className="w-full bg-amber hover:bg-amber-light text-dark-bg text-sm font-semibold py-2.5 rounded-md disabled:opacity-60 transition-colors shadow-sm shadow-amber/10"
        >
          {loading ? 'Opening Razorpay…' : 'Trigger Test Payment'}
        </button>

        <div className="text-xs text-dark-muted">
          After payment failure → return to dashboard → audit trail updates within 10s (polling).
        </div>
      </div>
    </div>
  )
}
