import { startTransition, useEffect, useState } from 'react'
import {
  Boxes,
  Copy,
  Download,
  LogIn,
  LogOut,
  ShieldCheck,
  Sparkles,
} from 'lucide-react'
import './App.css'
import { buildApiUrl, request } from './api'

const AUTH_STORAGE_KEY = 'devops-project-generator-auth'
const PROJECT_TYPES = ['docker', 'kubernetes', 'cicd', 'terraform']
const DIFFICULTY_LEVELS = ['beginner', 'intermediate', 'advanced']

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
  const downloadUrl = generation ? buildApiUrl(generation.download_url) : ''

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
    } catch (requestError) {
      if (requestError.message === 'Login required to continue') {
        setGuestRequestsRemaining(0)
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
      <aside className="control-rail">
        <div className="rail-header">
          <div>
            <p className="eyebrow">SaaS-style internal tool</p>
            <h1>DevOps Project Generator</h1>
          </div>
          <div className="status-chip">
            <ShieldCheck size={16} />
            <span>{signedIn ? 'Authenticated' : 'Guest access'}</span>
          </div>
        </div>

        <section className="rail-section">
          <div className="section-title">
            <LogIn size={16} />
            <h2>Account</h2>
          </div>

          <div className="segmented-control" role="tablist" aria-label="Authentication mode">
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

          {signedIn ? (
            <div className="signed-in-panel">
              <p className="supporting-label">Current user</p>
              <strong>{authState.user.email}</strong>
              <button type="button" className="secondary-button" onClick={handleLogout}>
                <LogOut size={16} />
                <span>Sign out</span>
              </button>
            </div>
          ) : (
            <form className="stack-form" onSubmit={handleAuthSubmit}>
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
              <button type="submit" className="primary-button" disabled={authBusy}>
                <LogIn size={16} />
                <span>{authBusy ? 'Working...' : authMode === 'signup' ? 'Create account' : 'Login'}</span>
              </button>
            </form>
          )}
        </section>

        <section className="rail-section">
          <div className="section-title">
            <Sparkles size={16} />
            <h2>Generator</h2>
          </div>

          <form className="stack-form" onSubmit={handleGenerate}>
            <label>
              <span>Project type</span>
              <select value={projectType} onChange={(event) => setProjectType(event.target.value)}>
                {PROJECT_TYPES.map((option) => (
                  <option key={option} value={option}>
                    {option.toUpperCase()}
                  </option>
                ))}
              </select>
            </label>

            <label>
              <span>Difficulty level</span>
              <select
                value={difficultyLevel}
                onChange={(event) => setDifficultyLevel(event.target.value)}
              >
                {DIFFICULTY_LEVELS.map((option) => (
                  <option key={option} value={option}>
                    {option.charAt(0).toUpperCase() + option.slice(1)}
                  </option>
                ))}
              </select>
            </label>

            <button type="submit" className="primary-button" disabled={generateBusy}>
              <Boxes size={16} />
              <span>{generateBusy ? 'Generating...' : 'Generate project'}</span>
            </button>
          </form>

          {!signedIn ? (
            <p className="quota-line">
              Guest requests remaining: <strong>{guestRequestsRemaining}</strong> / 3
            </p>
          ) : (
            <p className="quota-line">
              Usage tracking is now tied to <strong>{authState.user.email}</strong>.
            </p>
          )}
        </section>

        <section className="rail-section">
          <div className="section-title">
            <ShieldCheck size={16} />
            <h2>Safeguards</h2>
          </div>
          <ul className="compact-list">
            <li>JWT auth with 1 hour expiry</li>
            <li>bcrypt password hashing</li>
            <li>IP-based guest generation cap</li>
            <li>Enum-based request validation</li>
            <li>Rate limited API access</li>
            <li>Predefined local templates only</li>
          </ul>
        </section>
      </aside>

      <main className="workspace">
        <header className="workspace-header">
          <div>
            <p className="eyebrow">Generated output</p>
            <h2>Project bundle</h2>
          </div>
          {generation ? (
            <a className="secondary-button" href={downloadUrl} target="_blank" rel="noreferrer">
              <Download size={16} />
              <span>Download ZIP</span>
            </a>
          ) : null}
        </header>

        {message ? <div className="feedback success">{message}</div> : null}
        {error ? <div className="feedback error">{error}</div> : null}

        {generation ? (
          <div className="result-grid">
            <section className="result-section result-summary">
              <div className="summary-header">
                <div>
                  <p className="eyebrow">Generated idea</p>
                  <h3>{generation.idea}</h3>
                </div>
                <div className="summary-tags">
                  <span>{generation.project_type}</span>
                  <span>{generation.difficulty_level}</span>
                </div>
              </div>
              <p>{generation.why_this_project_matters}</p>
            </section>

            <section className="result-section">
              <p className="eyebrow">Architecture</p>
              <p>{generation.architecture}</p>
            </section>

            <section className="result-section split-section">
              <div>
                <p className="eyebrow">Tools required</p>
                <ul className="compact-list">
                  {generation.tools.map((tool) => (
                    <li key={tool}>{tool}</li>
                  ))}
                </ul>
              </div>
              <div>
                <p className="eyebrow">Implementation steps</p>
                <ol className="steps-list">
                  {generation.steps.map((step) => (
                    <li key={step}>{step}</li>
                  ))}
                </ol>
              </div>
            </section>

            <section className="result-section code-section">
              <div className="code-header">
                <div>
                  <p className="eyebrow">Starter code</p>
                  <h3>{activeFile?.path || 'Files'}</h3>
                </div>
                {activeFile ? (
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() => handleCopy(activeFile.path, activeFile.content)}
                  >
                    <Copy size={16} />
                    <span>{copiedPath === activeFile.path ? 'Copied' : 'Copy file'}</span>
                  </button>
                ) : null}
              </div>

              <div className="file-tabs" role="tablist" aria-label="Generated code files">
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
            </section>

            <section className="result-section">
              <div className="code-header">
                <div>
                  <p className="eyebrow">README</p>
                  <h3>Deployment guide</h3>
                </div>
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => handleCopy('README.md', generation.readme)}
                >
                  <Copy size={16} />
                  <span>{copiedPath === 'README.md' ? 'Copied' : 'Copy README'}</span>
                </button>
              </div>
              <pre className="code-block markdown-block">
                <code>{generation.readme}</code>
              </pre>
            </section>
          </div>
        ) : (
          <section className="empty-state">
            <p className="eyebrow">Ready to generate</p>
            <h3>Pick a stack and difficulty to build a reusable DevOps starter.</h3>
            <p>
              Each bundle includes a project idea, architecture guidance, required tools,
              implementation steps, starter code, README content, and a ZIP download.
            </p>
          </section>
        )}
      </main>
    </div>
  )
}

export default App
