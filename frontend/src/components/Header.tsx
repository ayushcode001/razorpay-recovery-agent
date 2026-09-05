// Header: persistent nav used on both / and /dashboard.
// Contains: project name, anchor links, "Live Dashboard" CTA, social icons.

import { Link, useLocation } from 'react-router-dom'

const LINKEDIN = 'https://www.linkedin.com/in/aayushmaan-patel-00a062348'
const X_URL = 'https://x.com/Aysmnptl'
const REPO = 'https://github.com/ayushcode001/razorpay-recovery-agent'

function GithubIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 0C5.374 0 0 5.373 0 12c0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0 1 12 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z"/>
    </svg>
  )
}

function LinkedinIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
      <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 0 1-2.063-2.065 2.064 2.064 0 1 1 2.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
    </svg>
  )
}

function XIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
      <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.744l7.737-8.847-8.17-10.653H8.08l4.253 5.622L18.244 2.25zm-1.161 17.52h1.833L7.084 4.126H5.117L17.083 19.77z"/>
    </svg>
  )
}

export function Header() {
  const location = useLocation()
  const isLanding = location.pathname === '/'
  const isDashboard = location.pathname.startsWith('/dashboard')

  return (
    <header className="sticky top-0 z-50 backdrop-blur-md bg-white/90 border-b border-surface-border text-navy">
      <div className="container-page flex items-center justify-between h-14">
        {/* Logo / Name */}
        <Link
          to="/"
          className="flex items-center gap-2 font-semibold text-base text-navy hover:text-primary transition-colors"
        >
          <span className="w-6 h-6 rounded-none flex items-center justify-center text-xs font-bold bg-primary text-white shadow-xs">
            R
          </span>
          <span>Recovery Agent</span>
        </Link>

        {/* Nav links */}
        <nav className="hidden md:flex items-center gap-6 text-sm text-muted">
          {isLanding ? (
            <>
              <a href="#problem" className="hover:text-navy transition-colors">Problem</a>
              <a href="#solution" className="hover:text-navy transition-colors">Solution</a>
              <a href="#why" className="hover:text-navy transition-colors">Why</a>
              <a href="#how" className="hover:text-navy transition-colors">How</a>
              <a href="#results" className="hover:text-navy transition-colors">Results</a>
            </>
          ) : (
            <Link to="/" className="hover:text-navy transition-colors flex items-center gap-1">
              <span>←</span>
              <span>Back to Overview</span>
            </Link>
          )}
        </nav>

        {/* Right: Dashboard CTA + Socials */}
        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-1.5 text-muted">
            <a
              href={REPO}
              target="_blank"
              rel="noopener noreferrer"
              className="p-1.5 rounded-none text-muted hover:text-navy hover:bg-surface-muted transition-all duration-150"
              aria-label="GitHub Repo"
            >
              <GithubIcon />
            </a>
            <a
              href={LINKEDIN}
              target="_blank"
              rel="noopener noreferrer"
              className="p-1.5 rounded-none text-muted hover:text-navy hover:bg-surface-muted transition-all duration-150"
              aria-label="LinkedIn"
            >
              <LinkedinIcon />
            </a>
            <a
              href={X_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="p-1.5 rounded-none text-muted hover:text-navy hover:bg-surface-muted transition-all duration-150"
              aria-label="X / Twitter"
            >
              <XIcon />
            </a>
          </div>
          <div className="w-px h-4 hidden sm:block bg-surface-border" />
          {isDashboard ? (
            <Link
              to="/"
              className="border border-surface-border bg-surface-subtle text-navy hover:bg-surface-muted text-sm font-medium px-3.5 py-1.5 rounded-none transition-all"
            >
              Overview
            </Link>
          ) : (
            <Link
              to="/dashboard"
              className="bg-primary text-white hover:bg-primary-dark text-sm font-semibold px-3.5 py-1.5 rounded-none hover:shadow-md transition-all shadow-xs"
            >
              Live Dashboard
            </Link>
          )}
        </div>
      </div>
    </header>
  )
}
