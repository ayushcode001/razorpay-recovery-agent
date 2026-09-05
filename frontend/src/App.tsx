import { useEffect, useState, type ReactNode } from 'react'
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AnimatePresence, motion } from 'framer-motion'
import { ReactLenis, useLenis } from 'lenis/react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { Header } from '@/components/Header'
import { FloatingCopilot } from '@/components/FloatingCopilot'
import { Landing } from '@/pages/Landing'
import { Dashboard } from '@/pages/Dashboard'

gsap.registerPlugin(ScrollTrigger)

/**
 * Synchronizes Lenis smooth scrolling with GSAP ticker & ScrollTrigger.
 * Driving Lenis via gsap.ticker ensures both libraries share the exact same
 * frame loop, eliminating jitter.
 */
function ScrollTriggerSync() {
  const lenis = useLenis()

  useEffect(() => {
    if (!lenis) return

    const update = (time: number) => {
      lenis.raf(time * 1000)
    }

    gsap.ticker.add(update)
    gsap.ticker.lagSmoothing(0)

    const unsubscribe = lenis.on('scroll', () => {
      ScrollTrigger.update()
    })

    return () => {
      gsap.ticker.remove(update)
      unsubscribe()
    }
  }, [lenis])

  return null
}

/**
 * Handles route transitions: immediately resets scroll position to top and refreshes ScrollTrigger.
 */
function RouteScrollManager() {
  const { pathname } = useLocation()
  const lenis = useLenis()

  useEffect(() => {
    if (lenis) {
      lenis.scrollTo(0, { immediate: true })
    } else {
      window.scrollTo(0, 0)
    }

    const timer = setTimeout(() => {
      ScrollTrigger.refresh()
    }, 150)

    return () => clearTimeout(timer)
  }, [pathname, lenis])

  return null
}

function SmoothScrollProvider({ children }: { children: ReactNode }) {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(() => {
    if (typeof window === 'undefined') return false
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches
  })

  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)')
    const onChange = (e: MediaQueryListEvent) => setPrefersReducedMotion(e.matches)
    mq.addEventListener('change', onChange)
    return () => mq.removeEventListener('change', onChange)
  }, [])

  // If user prefers reduced motion, completely skip Lenis and use native browser scrolling
  if (prefersReducedMotion) {
    return <>{children}</>
  }

  return (
    <ReactLenis
      root
      autoRaf={false}
      options={{
        duration: 1.4,
        easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
        orientation: 'vertical',
        gestureOrientation: 'vertical',
        smoothWheel: true,
        wheelMultiplier: 1.0,
        touchMultiplier: 1.5,
      }}
    >
      <ScrollTriggerSync />
      {children}
    </ReactLenis>
  )
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      retryDelay: (attempt: number) => Math.min(1000 * 2 ** attempt, 10_000),
    },
  },
})

function AnimatedRoutes() {
  const location = useLocation()

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={location.pathname}
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.2, ease: 'easeOut' }}
      >
        <Routes location={location}>
          <Route path="/" element={<Landing />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="*" element={<Landing />} />
        </Routes>
      </motion.div>
    </AnimatePresence>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <SmoothScrollProvider>
          <RouteScrollManager />
          <Header />
          <main>
            <AnimatedRoutes />
          </main>
          <FloatingCopilot />
        </SmoothScrollProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
