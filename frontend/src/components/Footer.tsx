// Footer: social links, repo link, one-line credit.

const GITHUB_PROFILE = 'https://github.com/ayushcode001'
const LINKEDIN = 'https://www.linkedin.com/in/aayushmaan-patel-00a062348'
const X_URL = 'https://x.com/Aysmnptl'
const REPO = 'https://github.com/ayushcode001/razorpay-recovery-agent'

export function Footer() {
  return (
    <footer className="border-t border-white/[0.08] bg-[#08080A]">
      <div className="container-page py-8 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="text-sm text-dark-muted">
          Built by{' '}
          <a
            href={LINKEDIN}
            target="_blank"
            rel="noopener noreferrer"
            className="text-dark-cream hover:text-amber transition-colors font-medium"
          >
            Aayushmaan Patel
          </a>{' '}
          · Razorpay AI Buildathon · Track 03
        </div>
        <div className="flex items-center gap-4 text-sm text-dark-muted">
          <a
            href={REPO}
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-dark-cream transition-colors"
          >
            GitHub Repo
          </a>
          <a
            href={GITHUB_PROFILE}
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-dark-cream transition-colors"
          >
            @ayushcode001
          </a>
          <a
            href={LINKEDIN}
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-dark-cream transition-colors"
          >
            LinkedIn
          </a>
          <a
            href={X_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-dark-cream transition-colors"
          >
            X
          </a>
        </div>
      </div>
    </footer>
  )
}
