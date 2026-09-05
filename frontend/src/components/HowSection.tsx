import { useRef } from 'react'
import { useGSAP } from '@gsap/react'
import gsap from 'gsap'
import { ArchitectureDiagram } from '@/components/ArchitectureDiagram'

export function HowSection() {
  const sectionRef = useRef<HTMLElement>(null)

  useGSAP(
    () => {
      const mm = gsap.matchMedia()

      mm.add(
        {
          isDesktop: '(min-width: 768px)',
          reduceMotion: '(prefers-reduced-motion: reduce)',
        },
        (context) => {
          const { isDesktop, reduceMotion } = context.conditions as {
            isDesktop: boolean
            reduceMotion: boolean
          }

          // Strict gate: disable pin-and-reveal on mobile viewports (< 768px) and prefers-reduced-motion
          if (!isDesktop || reduceMotion) return

          const q = gsap.utils.selector(sectionRef)

          // Initial blueprint state on desktop: subtle wireframe transparency
          gsap.set(
            [
              q('[data-arch="comp-1"]'),
              q('[data-arch="comp-2"]'),
              q('[data-arch="comp-3"]'),
              q('[data-arch="comp-4"]'),
              q('[data-arch="actions"]'),
              q('[data-arch="audit"]'),
              q('[data-arch="comp-5"]'),
              q('[data-arch="comp-6"]'),
              q('[data-arch="comp-7"]'),
              q('[data-arch="comp-8"]'),
            ],
            { opacity: 0.22, y: 8, scale: 0.98 },
          )

          gsap.set(
            [
              q('[data-arch="arrow-top"]'),
              q('[data-arch="arrow-mid"]'),
              q('[data-arch="arrow-actions"]'),
              q('[data-arch="arrow-audit"]'),
              q('[data-arch="support-header"]'),
            ],
            { opacity: 0.25 },
          )

          const tl = gsap.timeline({
            scrollTrigger: {
              trigger: sectionRef.current,
              start: 'top 56px',
              end: '+=1600',
              pin: true,
              pinSpacing: true,
              scrub: 0.5,
              anticipatePin: 1,
            },
          })

          // Step 1: Incoming Webhook connects to Component 1 (Deterministic Taxonomy)
          tl.to(q('[data-arch="arrow-top"]'), { opacity: 1, duration: 0.2 }, '+=0.05')
            .to(
              q('[data-arch="comp-1"]'),
              { opacity: 1, y: 0, scale: 1, duration: 0.35, ease: 'power2.out' },
              '<',
            )

          // Step 2: Component 2 (Success Predictor)
          tl.to(
            q('[data-arch="comp-2"]'),
            { opacity: 1, y: 0, scale: 1, duration: 0.35, ease: 'power2.out' },
            '+=0.1',
          )

          // Step 3: Connector down to Component 3 (Causal Uplift Modeler)
          tl.to(q('[data-arch="arrow-mid"]'), { opacity: 1, duration: 0.2 }, '+=0.1')
            .to(
              q('[data-arch="comp-3"]'),
              { opacity: 1, y: 0, scale: 1, duration: 0.35, ease: 'power2.out' },
              '<',
            )

          // Step 4: Component 4 (Policy Engine)
          tl.to(
            q('[data-arch="comp-4"]'),
            { opacity: 1, y: 0, scale: 1, duration: 0.35, ease: 'power2.out' },
            '+=0.1',
          )

          // Step 5: Bounded Actions execution
          tl.to(q('[data-arch="arrow-actions"]'), { opacity: 1, duration: 0.2 }, '+=0.1')
            .to(
              q('[data-arch="actions"]'),
              { opacity: 1, y: 0, scale: 1, duration: 0.35, ease: 'power2.out' },
              '<',
            )

          // Step 6: Immutable PostgreSQL Audit Trail
          tl.to(q('[data-arch="arrow-audit"]'), { opacity: 1, duration: 0.2 }, '+=0.1')
            .to(
              q('[data-arch="audit"]'),
              { opacity: 1, y: 0, scale: 1, duration: 0.35, ease: 'power2.out' },
              '<',
            )

          // Step 7: Supporting Agents header + Component 5 (Degradation Forecaster)
          tl.to(q('[data-arch="support-header"]'), { opacity: 1, duration: 0.2 }, '+=0.1')
            .to(
              q('[data-arch="comp-5"]'),
              { opacity: 1, y: 0, scale: 1, duration: 0.3, ease: 'power2.out' },
              '<',
            )

          // Step 8: Component 6 (Contextual Retry Bandit)
          tl.to(
            q('[data-arch="comp-6"]'),
            { opacity: 1, y: 0, scale: 1, duration: 0.3, ease: 'power2.out' },
            '+=0.08',
          )

          // Step 9: Component 7 (Audit Trail Copilot)
          tl.to(
            q('[data-arch="comp-7"]'),
            { opacity: 1, y: 0, scale: 1, duration: 0.3, ease: 'power2.out' },
            '+=0.08',
          )

          // Step 10: Component 8 (Drift-Check Agent)
          tl.to(
            q('[data-arch="comp-8"]'),
            { opacity: 1, y: 0, scale: 1, duration: 0.3, ease: 'power2.out' },
            '+=0.08',
          )

          // Hold full architectural diagram in clear illumination before unpinning
          tl.to({}, { duration: 0.4 })
        },
      )

      return () => mm.revert()
    },
    { scope: sectionRef },
  )

  return (
    <section
      id="how"
      ref={sectionRef}
      className="section-pad md:py-14 border-b border-surface-border bg-surface-muted relative overflow-hidden md:min-h-[calc(100vh-56px)] md:flex md:flex-col md:justify-center"
    >
      <div className="container-page relative z-10">
        <div className="mb-6 md:mb-8">
          <div className="mb-2">
            <span className="font-mono text-xs uppercase tracking-wider text-primary font-semibold">
              04 · System Topology
            </span>
          </div>
          <h2 className="text-2xl md:text-3xl font-bold text-navy tracking-tight">
            How It Works
          </h2>
          <p className="mt-2 text-sm text-muted max-w-2xl">
            End-to-end telemetry ingestion, real-time causal uplift modeling, and bounded automated resolution.
          </p>
        </div>
        <ArchitectureDiagram />
      </div>
    </section>
  )
}
