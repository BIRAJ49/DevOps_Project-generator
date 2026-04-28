import { startTransition, useEffect, useState } from 'react'
import {
  ArrowRight,
  Copy,
  FileArchive,
  FileText,
  Gauge,
  Layers3,
  LogIn,
  LogOut,
  Rocket,
  ShieldCheck,
  Sparkles,
  TerminalSquare,
  X,
} from 'lucide-react'
import './App.css'
import { buildApiUrl, request } from './api'

const AUTH_STORAGE_KEY = 'devops-project-generator-auth'

const PROJECT_OPTIONS = [
  { id: 'docker', title: 'Docker', subtitle: 'Containers' },
  { id: 'kubernetes', title: 'Kubernetes', subtitle: 'Orchestration' },
  { id: 'cicd', title: 'CI/CD', subtitle: 'Pipelines' },
  { id: 'terraform', title: 'Terraform', subtitle: 'IaC' },
]

const DIFFICULTY_OPTIONS = [
  { id: 'beginner', code: '01', title: 'Beginner', summary: 'Single service, local dev' },
  { id: 'intermediate', code: '02', title: 'Intermediate', summary: 'Multi-service, staging' },
  { id: 'advanced', code: '03', title: 'Advanced', summary: 'Production, HA, observability' },
]

const TECH_TAGS = ['Docker', 'Kubernetes', 'CI/CD', 'Terraform', 'GitHub Actions']
const HOW_IT_WORKS = [
  {
    id: '01',
    title: 'Pick stack',
    description: 'Docker, Kubernetes, CI/CD, or Terraform.',
    icon: Layers3,
  },
  {
    id: '02',
    title: 'Pick level',
    description: 'Beginner, intermediate, or advanced. Scope scales.',
    icon: Gauge,
  },
  {
    id: '03',
    title: 'Ship it',
    description: 'Architecture, code, README, steps, ZIP, and PDF.',
    icon: Rocket,
  },
]

function readStoredSession() {
  try {
    const stored = localStorage.getItem(AUTH_STORAGE_KEY)
    if (!stored) {
      return { token: '', user: null }
    }

    const parsed = JSON.parse(stored)
    return {
      token: parsed?.token || '',
      user: parsed?.user || null,
    }
  } catch {
    return { token: '', user: null }
  }
}

function App() {
  const [projectType, setProjectType] = useState('docker')
  const [difficultyLevel, setDifficultyLevel] = useState('beginner')
  const [authMode, setAuthMode] = useState('login')
  const [credentials, setCredentials] = useState({ email: '', password: '' })
  const [authState, setAuthState] = useState(readStoredSession)
  const [authOpen, setAuthOpen] = useState(false)
  const [generation, setGeneration] = useState(null)
  const [activeFilePath, setActiveFilePath] = useState('')
  const [copiedPath, setCopiedPath] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [authBusy, setAuthBusy] = useState(false)
  const [generateBusy, setGenerateBusy] = useState(false)
  const [guestRequestsRemaining, setGuestRequestsRemaining] = useState(3)

  useEffect(() => {
    if (!authState.token) {
      return
    }

    let cancelled = false

    async function verifySession() {
      try {
        const user = await request('/api/me', { token: authState.token })
        if (cancelled) {
          return
        }

        const nextState = { token: authState.token, user }
        setAuthState(nextState)
        localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(nextState))
      } catch {
        if (cancelled) {
          return
        }
        localStorage.removeItem(AUTH_STORAGE_KEY)
        setAuthState({ token: '', user: null })
      }
    }

    void verifySession()

    return () => {
      cancelled = true
    }
  }, [authState.token])

  const activeFile =
    generation?.code_files?.find((file) => file.path === activeFilePath) ||
    generation?.code_files?.[0] ||
    null
  const signedIn = Boolean(authState.token && authState.user)
  const templateCount = PROJECT_OPTIONS.length * DIFFICULTY_OPTIONS.length
  const downloadZipUrl = generation ? buildApiUrl(generation.download_zip_url) : ''
  const downloadPdfUrl = generation ? buildApiUrl(generation.download_pdf_url) : ''

  function updateCredentials(field, value) {
    setCredentials((current) => ({
      ...current,
      [field]: value,
    }))
  }

  function persistAuth(nextAuthState) {
    setAuthState(nextAuthState)
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(nextAuthState))
  }

  function openAuth(mode) {
    setAuthMode(mode)
    setAuthOpen(true)
    setError('')
  }

  function scrollToSection(sectionId) {
    document.getElementById(sectionId)?.scrollIntoView({
      behavior: 'smooth',
      block: 'start',
    })
  }

  async function handleAuthSubmit(event) {
    event.preventDefault()
    setAuthBusy(true)
    setError('')
    setMessage('')

    try {
      const response = await request(`/api/${authMode}`, {
        method: 'POST',
        body: JSON.stringify(credentials),
      })

      persistAuth({
        token: response.access_token,
        user: response.user,
      })
      setCredentials({ email: '', password: '' })
      setGuestRequestsRemaining(3)
      setAuthOpen(false)
      setMessage(
        authMode === 'signup'
          ? 'Account created. Unlimited generation is now available.'
          : 'Login successful.',
      )
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setAuthBusy(false)
    }
  }

  function handleLogout() {
    localStorage.removeItem(AUTH_STORAGE_KEY)
    setAuthState({ token: '', user: null })
    setMessage('Signed out. Guest usage limits apply again.')
    setError('')
  }

  async function handleGenerate(event) {
    event.preventDefault()

    if (!signedIn && guestRequestsRemaining === 0) {
      setError('Login required to continue')
      setAuthMode('signup')
      setAuthOpen(true)
      return
    }

    setGenerateBusy(true)
    setError('')
    setMessage('')

    try {
      const response = await request('/api/generate', {
        method: 'POST',
        token: authState.token || undefined,
        body: JSON.stringify({
          project_type: projectType,
          difficulty_level: difficultyLevel,
        }),
      })

      startTransition(() => {
        setGeneration(response)
        setActiveFilePath(response.code_files[0]?.path || '')
      })

      if (typeof response.guest_requests_remaining === 'number') {
        setGuestRequestsRemaining(response.guest_requests_remaining)
      }

      setMessage('Project bundle generated successfully.')
      scrollToSection('results')
    } catch (requestError) {
      if (requestError.message === 'Login required to continue') {
        setGuestRequestsRemaining(0)
        setAuthMode('signup')
        setAuthOpen(true)
      }
      setError(requestError.message)
    } finally {
      setGenerateBusy(false)
    }
  }

  async function handleCopy(targetPath, content) {
    try {
      await navigator.clipboard.writeText(content)
      setCopiedPath(targetPath)
      window.setTimeout(() => setCopiedPath(''), 1800)
    } catch {
      setError('Clipboard access failed in this browser session.')
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <button type="button" className="brand-lockup" onClick={() => scrollToSection('hero')}>
          <span className="brand-orb" aria-hidden="true">
            <Sparkles size={22} />
          </span>
          <span className="brand-text">
            DevOps<span>Forge</span>
          </span>
        </button>

        <div className="topbar-actions">
          <div className="quota-pill">
            <span className="quota-dot" />
            <span className="quota-label">{signedIn ? 'member' : 'guest'}</span>
            <strong>{signedIn ? 'unlocked' : `${guestRequestsRemaining}/3`}</strong>
          </div>

          {signedIn ? (
            <>
              <div className="member-pill">
                <ShieldCheck size={16} />
                <span>{authState.user.email}</span>
              </div>
              <button type="button" className="text-nav" onClick={handleLogout}>
                <LogOut size={16} />
                <span>Sign out</span>
              </button>
            </>
          ) : (
            <>
              <button type="button" className="text-nav" onClick={() => openAuth('login')}>
                <span>Log in</span>
              </button>
              <button type="button" className="cta-pill" onClick={() => openAuth('signup')}>
                <span>Sign up</span>
              </button>
            </>
          )}
        </div>
      </header>

      <main className="page-shell">
        <section className="hero-section" id="hero">
          <div className="eyebrow-pill">
            <span className="quota-dot" />
            <span>v1.0</span>
            <span>{templateCount} templates</span>
            <span>zip + pdf</span>
          </div>

          <h1 className="hero-title">
            Architect <span>DevOps</span> projects.
            <br />
            Ship in seconds.
          </h1>

          <p className="hero-copy">
            Generate complete, production-grade DevOps scaffolding with architecture,
            starter code, README, and a step-by-step build guide.{' '}
            <strong>3 free generations.</strong>
          </p>

          <div className="hero-actions">
            <button type="button" className="hero-primary" onClick={() => scrollToSection('configure')}>
              <span>Start architecting</span>
              <ArrowRight size={22} />
            </button>
            <button type="button" className="hero-secondary" onClick={() => scrollToSection('how-it-works')}>
              <span>How it works</span>
            </button>
          </div>

          <div className="tag-strip">
            {TECH_TAGS.map((tag) => (
              <span key={tag}>{tag}</span>
            ))}
          </div>
        </section>

        <section className="configure-panel" id="configure">
          <div className="panel-badge">Step 01 · Configure</div>

          <div className="configure-header">
            <div>
              <p className="section-kicker">Generator</p>
              <h2>
                Architect a <span>DevOps</span> project.
              </h2>
              <p>
                Pick a stack and complexity. We generate architecture, code, README, and a
                step-by-step guide.
              </p>
            </div>

            <div className="configure-status">
              <div>
                <span className="section-kicker">Auth</span>
                <strong>{signedIn ? 'Authenticated' : 'Guest access'}</strong>
              </div>
              {!signedIn ? (
                <button type="button" className="panel-link" onClick={() => openAuth('signup')}>
                  <LogIn size={16} />
                  <span>{guestRequestsRemaining === 0 ? 'Unlock more runs' : 'Create account'}</span>
                </button>
              ) : (
                <button type="button" className="panel-link" onClick={handleLogout}>
                  <LogOut size={16} />
                  <span>Sign out</span>
                </button>
              )}
            </div>
          </div>

          <form className="configure-form" onSubmit={handleGenerate}>
            <div className="field-group">
              <p className="field-label">Project type</p>
              <div className="project-grid">
                {PROJECT_OPTIONS.map((option) => (
                  <button
                    key={option.id}
                    type="button"
                    className={`project-card ${projectType === option.id ? 'active' : ''}`}
                    onClick={() => setProjectType(option.id)}
                  >
                    <strong>{option.title}</strong>
                    <span>{option.subtitle}</span>
                  </button>
                ))}
              </div>
            </div>

            <div className="field-group">
              <p className="field-label">Difficulty</p>
              <div className="difficulty-stack">
                {DIFFICULTY_OPTIONS.map((option) => (
                  <button
                    key={option.id}
                    type="button"
                    className={`difficulty-row ${difficultyLevel === option.id ? 'active' : ''}`}
                    onClick={() => setDifficultyLevel(option.id)}
                  >
                    <span className="difficulty-code">{option.code}</span>
                    <strong>{option.title}</strong>
                    <span className="difficulty-summary">{option.summary}</span>
                  </button>
                ))}
              </div>
            </div>

            <button type="submit" className="generate-button" disabled={generateBusy}>
              <span>{generateBusy ? 'Generating...' : 'Architect Project'}</span>
              <ArrowRight size={26} />
            </button>
          </form>
        </section>

        {(message || error) && (
          <section className="feedback-strip">
            {message ? <div className="feedback success">{message}</div> : null}
            {error ? <div className="feedback error">{error}</div> : null}
          </section>
        )}

        <section className="stats-grid">
          <article className="stat-card">
            <span>Quota</span>
            <strong>{signedIn ? '∞' : `${guestRequestsRemaining}/3`}</strong>
          </article>
          <article className="stat-card">
            <span>Templates</span>
            <strong>{templateCount}</strong>
          </article>
          <article className="stat-card">
            <span>Artifacts</span>
            <strong>ZIP + PDF</strong>
          </article>
        </section>

        <section className="manifesto-card">
          <p className="section-kicker">// manifesto</p>
          <h2>
            Click <span>→</span> Build <span>→</span> Ship.
          </h2>
          <p>
            No fluff. Real production-grade scaffolding for engineers who need a starting
            point with actual structure, deployment guidance, and exportable artifacts.
          </p>
        </section>

        <section className="terminal-card">
          <div className="terminal-header">
            <TerminalSquare size={18} />
            <span>~/devops-forge</span>
          </div>
          <pre>
            <code>{`$ forge init
→ workspace ready
$ forge generate ${projectType} --level ${difficultyLevel}
✓ architecture assembled
✓ starter code prepared
✓ artifacts ready for download`}</code>
          </pre>
        </section>

        {generation ? (
          <section className="results-panel" id="results">
            <div className="results-head">
              <div>
                <p className="section-kicker">Generated output</p>
                <h2>{generation.idea}</h2>
              </div>
              <div className="result-actions">
                <a className="result-secondary" href={downloadPdfUrl} target="_blank" rel="noreferrer">
                  <FileText size={18} />
                  <span>Download PDF</span>
                </a>
                <a className="result-primary" href={downloadZipUrl} target="_blank" rel="noreferrer">
                  <FileArchive size={18} />
                  <span>Download ZIP</span>
                </a>
              </div>
            </div>

            <div className="results-summary">
              <article>
                <p className="section-kicker">Why this matters</p>
                <p>{generation.why_this_project_matters}</p>
              </article>
              <article>
                <p className="section-kicker">Architecture</p>
                <p>{generation.architecture}</p>
              </article>
            </div>

            <div className="results-grid">
              <article className="info-card">
                <p className="section-kicker">Tools required</p>
                <ul className="compact-list">
                  {generation.tools.map((tool) => (
                    <li key={tool}>{tool}</li>
                  ))}
                </ul>
              </article>

              <article className="info-card">
                <p className="section-kicker">Implementation steps</p>
                <ol className="steps-list">
                  {generation.steps.map((step) => (
                    <li key={step}>{step}</li>
                  ))}
                </ol>
              </article>
            </div>

            <article className="code-surface">
              <div className="code-head">
                <div>
                  <p className="section-kicker">Starter code</p>
                  <h3>{activeFile?.path || 'Files'}</h3>
                </div>
                {activeFile ? (
                  <button
                    type="button"
                    className="panel-link"
                    onClick={() => handleCopy(activeFile.path, activeFile.content)}
                  >
                    <Copy size={16} />
                    <span>{copiedPath === activeFile.path ? 'Copied' : 'Copy file'}</span>
                  </button>
                ) : null}
              </div>

              <div className="tab-row" role="tablist" aria-label="Generated files">
                {generation.code_files.map((file) => (
                  <button
                    key={file.path}
                    type="button"
                    className={file.path === activeFile?.path ? 'active' : ''}
                    onClick={() => setActiveFilePath(file.path)}
                  >
                    {file.path}
                  </button>
                ))}
              </div>

              <pre className="code-block">
                <code>{activeFile?.content || 'Select a file to inspect the generated starter code.'}</code>
              </pre>
            </article>

            <article className="code-surface">
              <div className="code-head">
                <div>
                  <p className="section-kicker">README</p>
                  <h3>Deployment guide</h3>
                </div>
                <button
                  type="button"
                  className="panel-link"
                  onClick={() => handleCopy('README.md', generation.readme)}
                >
                  <Copy size={16} />
                  <span>{copiedPath === 'README.md' ? 'Copied' : 'Copy README'}</span>
                </button>
              </div>
              <pre className="code-block markdown-block">
                <code>{generation.readme}</code>
              </pre>
            </article>
          </section>
        ) : null}

        <section className="how-it-works" id="how-it-works">
          <div className="how-header">
            <h2>
              How it <span>works.</span>
            </h2>
            <div className="timeline-pill">03 steps · 30 seconds</div>
          </div>

          <div className="how-grid">
            {HOW_IT_WORKS.map((item) => {
              const Icon = item.icon
              return (
                <article key={item.id} className="how-card">
                  <div className="how-top">
                    <strong>{item.id}</strong>
                    <span className="how-icon">
                      <Icon size={22} />
                    </span>
                  </div>
                  <h3>{item.title}</h3>
                  <p>{item.description}</p>
                </article>
              )
            })}
          </div>
        </section>
      </main>

      <footer className="footer-bar">
        <div className="footer-left">
          <Sparkles size={16} />
          <span>© 2026 DevOpsForge</span>
          <span>built for engineers who ship.</span>
        </div>
        <div className="footer-right">
          <span className="quota-dot" />
          <span>operational</span>
          <span>v1.0.0</span>
          <button type="button" className="footer-link" onClick={() => openAuth('login')}>
            {signedIn ? 'Account' : 'Login'}
          </button>
        </div>
      </footer>

      {authOpen ? (
        <div className="auth-overlay" onClick={() => setAuthOpen(false)}>
          <div className="auth-modal" onClick={(event) => event.stopPropagation()}>
            <div className="auth-header">
              <div>
                <p className="section-kicker">{authMode === 'signup' ? 'Create account' : 'Welcome back'}</p>
                <h3>{authMode === 'signup' ? 'Unlock unlimited generations.' : 'Log in to continue.'}</h3>
              </div>
              <button type="button" className="icon-button" onClick={() => setAuthOpen(false)}>
                <X size={18} />
              </button>
            </div>

            <div className="auth-switch">
              <button
                type="button"
                className={authMode === 'login' ? 'active' : ''}
                onClick={() => setAuthMode('login')}
              >
                Login
              </button>
              <button
                type="button"
                className={authMode === 'signup' ? 'active' : ''}
                onClick={() => setAuthMode('signup')}
              >
                Sign up
              </button>
            </div>

            <form className="auth-form" onSubmit={handleAuthSubmit}>
              <label>
                <span>Email</span>
                <input
                  type="email"
                  value={credentials.email}
                  onChange={(event) => updateCredentials('email', event.target.value)}
                  placeholder="you@example.com"
                  required
                />
              </label>
              <label>
                <span>Password</span>
                <input
                  type="password"
                  value={credentials.password}
                  onChange={(event) => updateCredentials('password', event.target.value)}
                  placeholder="Minimum 8 characters"
                  minLength={8}
                  required
                />
              </label>
              <button type="submit" className="generate-button auth-submit" disabled={authBusy}>
                <span>
                  {authBusy ? 'Working...' : authMode === 'signup' ? 'Create account' : 'Log in'}
                </span>
                <ArrowRight size={24} />
              </button>
            </form>
          </div>
        </div>
      ) : null}
    </div>
  )
}

export default App
