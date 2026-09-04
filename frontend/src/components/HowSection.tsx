import { FadeIn } from '@/components/FadeIn'
import { ArchitectureDiagram } from '@/components/ArchitectureDiagram'

export function HowSection() {
  return (
    <section
      id="how"
      className="section-pad border-b border-white/[0.08] bg-[#0E0E11] relative overflow-hidden"
    >
      <div className="absolute inset-0 bg-[radial-gradient(rgba(255,255,255,0.07)_1px,transparent_1px)] [background-size:20px_20px] pointer-events-none" />
      <div className="container-page relative z-10">
        <FadeIn>
          <div className="mb-6 md:mb-8">
            <div className="mb-2">
              <span className="font-mono text-xs uppercase tracking-wider text-amber font-semibold">
                04 · System Topology
              </span>
            </div>
            <h2 className="text-2xl md:text-3xl font-bold text-dark-cream tracking-tight">
              How It Works
            </h2>
            <p className="mt-2 text-sm text-dark-muted max-w-2xl">
              End-to-end telemetry ingestion, real-time causal uplift modeling, and bounded automated resolution.
            </p>
          </div>
        </FadeIn>
        <FadeIn delay={0.15}>
          <ArchitectureDiagram />
        </FadeIn>
      </div>
    </section>
  )
}
