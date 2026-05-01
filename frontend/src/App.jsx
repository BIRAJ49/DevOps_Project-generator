import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Archive,
  ArrowRight,
  Download,
  LayoutDashboard,
  LogOut,
  Monitor,
  Moon,
  Palette,
  Sun,
  X,
} from "lucide-react";
import { InfinityLogo } from "./components/InfinityLogo";
import "./App.css";
import { request } from "./api";

const AUTH_STORAGE_KEY = "devops-project-generator-auth";
const THEME_STORAGE_KEY = "devops-project-generator-theme";
const THEME_OPTIONS = [
  { value: "system", label: "System", icon: Monitor },
  { value: "dark", label: "Dark", icon: Moon },
  { value: "light", label: "Light", icon: Sun },
];

const TECH_TAGS = [
  "React + Node.js",
  "Mobile app",
  "AI chatbot",
  "E-commerce",
  "Game project",
  "Automation tool",
];

const GUEST_LIMIT_MESSAGE = "Login required to continue";

function getProfileIdentity(user) {
  const email = user?.email || "";
  const localPart = email.split("@")[0] || "user";
  const nameParts = localPart
    .replace(/([a-zA-Z])([0-9])/g, "$1 $2")
    .split(/[\s._-]+/)
    .filter(Boolean);
  const displayName = nameParts.length
    ? nameParts.join(" ")
    : localPart;
  const alphabeticParts = nameParts
    .map((part) => part.replace(/[^a-zA-Z]/g, ""))
    .filter(Boolean);
  const initialsSource = alphabeticParts.length ? alphabeticParts : nameParts;
  const initials =
    initialsSource.length > 1
      ? `${initialsSource[0][0]}${initialsSource[1][0]}`
      : (initialsSource[0] || localPart).slice(0, 2);

  return {
    displayName,
    initials: initials.toUpperCase() || "U",
  };
}

function formatProjectLabel(value) {
  return String(value || "")
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function ProfileMenuItem({ icon: Icon, label, onClick }) {
  return (
    <button type="button" className="profile-menu-item" onClick={onClick}>
      <span className="profile-menu-icon" aria-hidden="true">
        <Icon size={19} strokeWidth={2} />
      </span>
      <span className="profile-menu-label">{label}</span>
    </button>
  );
}

function readStoredSession() {
  try {
    const stored = localStorage.getItem(AUTH_STORAGE_KEY);
    if (!stored) {
      return { token: "", user: null };
    }

    const parsed = JSON.parse(stored);
    return {
      token: parsed?.token || "",
      user: parsed?.user || null,
    };
  } catch {
    return { token: "", user: null };
  }
}

function readStoredTheme() {
  try {
    const storedTheme = localStorage.getItem(THEME_STORAGE_KEY);
    return THEME_OPTIONS.some((option) => option.value === storedTheme)
      ? storedTheme
      : "system";
  } catch {
    return "system";
  }
}

function getSystemTheme() {
  if (window.matchMedia("(prefers-color-scheme: light)").matches) {
    return "light";
  }
  return "dark";
}

function App() {
  const [authMode, setAuthMode] = useState("login");
  const [credentials, setCredentials] = useState({ email: "", password: "" });
  const [authState, setAuthState] = useState(readStoredSession);
  const [authOpen, setAuthOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [themePreference, setThemePreference] = useState(readStoredTheme);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [authBusy, setAuthBusy] = useState(false);
  const [resendBusy, setResendBusy] = useState(false);
  const [verificationEmail, setVerificationEmail] = useState("");
  const [verificationCode, setVerificationCode] = useState("");
  const [resetEmail, setResetEmail] = useState("");
  const [resetPassword, setResetPassword] = useState("");
  const [prompt, setPrompt] = useState("");
  const [suggestBusy, setSuggestBusy] = useState(false);
  const [detailsBusy, setDetailsBusy] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [selectedSuggestion, setSelectedSuggestion] = useState(null);
  const [details, setDetails] = useState(null);

  useEffect(() => {
    if (!authState.token) {
      return;
    }

    let cancelled = false;

    async function verifySession() {
      try {
        const user = await request("/api/me", { token: authState.token });
        if (cancelled) {
          return;
        }

        const nextState = { token: authState.token, user };
        setAuthState(nextState);
        localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(nextState));
      } catch {
        if (cancelled) {
          return;
        }
        localStorage.removeItem(AUTH_STORAGE_KEY);
        setAuthState({ token: "", user: null });
      }
    }

    void verifySession();

    return () => {
      cancelled = true;
    };
  }, [authState.token]);

  useEffect(() => {
    if (!profileOpen) {
      return;
    }

    function handleKeyDown(event) {
      if (event.key === "Escape") {
        setProfileOpen(false);
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [profileOpen]);

  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-color-scheme: light)");

    function applyTheme() {
      const resolvedTheme =
        themePreference === "system" ? getSystemTheme() : themePreference;
      document.documentElement.dataset.theme = resolvedTheme;
      document.documentElement.dataset.themePreference = themePreference;
    }

    applyTheme();
    localStorage.setItem(THEME_STORAGE_KEY, themePreference);

    if (themePreference !== "system") {
      return undefined;
    }

    mediaQuery.addEventListener("change", applyTheme);
    return () => mediaQuery.removeEventListener("change", applyTheme);
  }, [themePreference]);

  const signedIn = Boolean(authState.token && authState.user);
  const profileIdentity = getProfileIdentity(authState.user);
  const currentThemeLabel =
    THEME_OPTIONS.find((option) => option.value === themePreference)?.label ||
    "System";
  const authHeader =
    {
      verify: {
        kicker: "Verify email",
        title: "Enter the code from your email.",
      },
      signup: {
        kicker: "Create account",
        title: "Create an account to continue.",
      },
      forgot: {
        kicker: "Reset password",
        title: "Send a reset code to your email.",
      },
      reset: {
        kicker: "Reset password",
        title: "Enter the code and choose a new password.",
      },
      login: {
        kicker: "Welcome back",
        title: "Log in to continue.",
      },
    }[authMode] || {
      kicker: "Welcome back",
      title: "Log in to continue.",
    };
  const showAuthSwitch = authMode === "login" || authMode === "signup";

  function updateCredentials(field, value) {
    setCredentials((current) => ({
      ...current,
      [field]: value,
    }));
  }

  function persistAuth(nextAuthState) {
    setAuthState(nextAuthState);
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(nextAuthState));
    localStorage.removeItem("generateClicks");
  }

  function openAuth(mode) {
    setAuthMode(mode);
    setAuthOpen(true);
    setError("");
    setMessage("");
    setVerificationCode("");
    setResetPassword("");
    if (mode === "forgot") {
      setResetEmail(credentials.email);
    }
  }

  function scrollToSection(sectionId) {
    document.getElementById(sectionId)?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  }

  function handleProfileScroll(sectionId) {
    setProfileOpen(false);
    scrollToSection(sectionId);
  }

  async function handleAuthSubmit(event) {
    event.preventDefault();
    setAuthBusy(true);
    setError("");
    setMessage("");

    try {
      const response = await request(`/api/${authMode}`, {
        method: "POST",
        body: JSON.stringify(credentials),
      });

      if (authMode === "signup") {
        setVerificationEmail(response.email || credentials.email);
        setVerificationCode("");
        setCredentials((current) => ({ ...current, password: "" }));
        setAuthMode("verify");
        setMessage(response.message || "Verification code sent. Check your email.");
        return;
      }

      persistAuth({
        token: response.access_token,
        user: response.user,
      });
      setCredentials({ email: "", password: "" });
      setAuthOpen(false);
      setMessage(
        authMode === "signup"
          ? "Account created successfully."
          : "Login successful.",
      );
    } catch (requestError) {
      if (requestError.message === "Email verification required") {
        setVerificationEmail(credentials.email);
        setVerificationCode("");
        setAuthMode("verify");
        setMessage("Enter the verification code sent to your email.");
      } else {
        setError(requestError.message);
      }
    } finally {
      setAuthBusy(false);
    }
  }

  async function handleVerifySubmit(event) {
    event.preventDefault();
    setAuthBusy(true);
    setError("");
    setMessage("");

    try {
      const response = await request("/api/verify-email", {
        method: "POST",
        body: JSON.stringify({
          email: verificationEmail || credentials.email,
          code: verificationCode,
        }),
      });

      persistAuth({
        token: response.access_token,
        user: response.user,
      });
      setCredentials({ email: "", password: "" });
      setVerificationEmail("");
      setVerificationCode("");
      setAuthOpen(false);
      setMessage("Email verified. You are logged in.");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setAuthBusy(false);
    }
  }

  async function handleResendVerification() {
    const email = verificationEmail || credentials.email;
    if (!email) {
      setError("Enter your email first.");
      return;
    }

    setResendBusy(true);
    setError("");
    setMessage("");

    try {
      const response = await request("/api/resend-verification", {
        method: "POST",
        body: JSON.stringify({ email }),
      });
      setVerificationEmail(response.email || email);
      setMessage(response.message || "Verification code sent.");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setResendBusy(false);
    }
  }

  async function handleForgotPasswordSubmit(event) {
    event.preventDefault();
    const email = (resetEmail || credentials.email).trim();
    if (!email) {
      setError("Enter your email first.");
      return;
    }

    setAuthBusy(true);
    setError("");
    setMessage("");

    try {
      const response = await request("/api/forgot-password", {
        method: "POST",
        body: JSON.stringify({ email }),
      });
      setResetEmail(response.email || email);
      setVerificationCode("");
      setResetPassword("");
      setAuthMode("reset");
      setMessage(response.message || "Password reset code sent. Check your email.");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setAuthBusy(false);
    }
  }

  async function handleResetPasswordSubmit(event) {
    event.preventDefault();
    const email = resetEmail.trim();
    if (!email) {
      setError("Enter your email first.");
      return;
    }

    setAuthBusy(true);
    setError("");
    setMessage("");

    try {
      const response = await request("/api/reset-password", {
        method: "POST",
        body: JSON.stringify({
          email,
          code: verificationCode,
          password: resetPassword,
        }),
      });
      setCredentials({ email, password: "" });
      setResetEmail("");
      setVerificationCode("");
      setResetPassword("");
      setAuthMode("login");
      setMessage(response.message || "Password reset. Log in with your new password.");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setAuthBusy(false);
    }
  }

  function handleLogout() {
    localStorage.removeItem(AUTH_STORAGE_KEY);
    setAuthState({ token: "", user: null });
    setProfileOpen(false);
    setMessage("Signed out.");
    setError("");
  }

  async function requestSuggestions(nextPrompt) {
    const normalizedPrompt = nextPrompt.trim();

    if (!normalizedPrompt) {
      setError("Describe what you want to build.");
      return;
    }

    setPrompt(normalizedPrompt);
    setSuggestBusy(true);
    setDetails(null);
    setSelectedSuggestion(null);
    setError("");
    setMessage("");

    try {
      const response = await request("/api/suggest", {
        method: "POST",
        token: authState.token || undefined,
        body: JSON.stringify({ prompt: normalizedPrompt }),
      });
      setSuggestions(
        Array.isArray(response?.suggestions) ? response.suggestions : [],
      );
      if (
        !authState.token &&
        typeof response?.guest_requests_remaining === "number"
      ) {
        const remaining = response.guest_requests_remaining;
        setMessage(
          remaining > 0
            ? `${remaining} free request${remaining === 1 ? "" : "s"} remaining.`
            : "You’ve used all 3 free requests. Log in to continue.",
        );
      }
      scrollToSection("suggestions");
    } catch (requestError) {
      setSuggestions([]);
      if (requestError.message === GUEST_LIMIT_MESSAGE) {
        openAuth("login");
      } else {
        setError(requestError.message);
      }
    } finally {
      setSuggestBusy(false);
    }
  }

  function handleSuggest(event) {
    event.preventDefault();
    void requestSuggestions(prompt);
  }

  function handleTagSuggest(tag) {
    scrollToSection("suggest");
    void requestSuggestions(tag);
  }

  async function handleSelectSuggestion(suggestion) {
    setSelectedSuggestion(suggestion);
    setDetails(null);
    setDetailsBusy(true);
    setError("");
    setMessage("");

    try {
      const response = await request("/api/details", {
        method: "POST",
        token: authState.token || undefined,
        body: JSON.stringify({
          prompt: prompt.trim(),
          suggestion,
        }),
      });
      setDetails(response);
      if (
        !authState.token &&
        typeof response?.guest_requests_remaining === "number"
      ) {
        const remaining = response.guest_requests_remaining;
        setMessage(
          remaining > 0
            ? `${remaining} free request${remaining === 1 ? "" : "s"} remaining.`
            : "You’ve used all 3 free requests. Log in to continue.",
        );
      }
      scrollToSection("details");
    } catch (requestError) {
      if (requestError.message === GUEST_LIMIT_MESSAGE) {
        openAuth("login");
      } else {
        setError(requestError.message);
      }
    } finally {
      setDetailsBusy(false);
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar-inner">
          <button
            type="button"
            className="brand-lockup"
            onClick={() => scrollToSection("hero")}
          >
            <span className="brand-orb" aria-hidden="true">
              <InfinityLogo size={66} />
            </span>
            <span className="brand-text">
              Project<span>Forge</span>
            </span>
          </button>

          <div className="topbar-actions">
            <nav className="topbar-nav" aria-label="Primary">
              <Link to="/how-it-works" className="text-nav">
                <span>How it works</span>
              </Link>
              <Link to="/about" className="text-nav">
                <span>About us</span>
              </Link>
              <Link to="/contact" className="text-nav">
                <span>Contact</span>
              </Link>
            </nav>

            <div className="account-actions">
              {signedIn ? (
                <div className="profile-menu-wrap">
                  <button
                    type="button"
                    className="profile-avatar-button"
                    aria-label="Open profile menu"
                    aria-expanded={profileOpen}
                    aria-haspopup="menu"
                    onClick={() => setProfileOpen((current) => !current)}
                  >
                    <span>{profileIdentity.initials}</span>
                  </button>

                  {profileOpen ? (
                    <>
                      <button
                        type="button"
                        className="profile-menu-backdrop"
                        aria-label="Close profile menu"
                        tabIndex={-1}
                        onClick={() => setProfileOpen(false)}
                      />
                      <div className="profile-menu" role="menu">
                        <div className="profile-menu-panel">
                          <div className="profile-menu-head">
                            <div className="profile-menu-avatar" aria-hidden="true">
                              {profileIdentity.initials}
                            </div>
                            <div className="profile-menu-identity">
                              <strong>{profileIdentity.displayName}</strong>
                            </div>
                          </div>

                          <div className="profile-menu-divider" />

                          <div className="profile-menu-list">
                            <ProfileMenuItem
                              icon={LayoutDashboard}
                              label="Dashboard"
                              onClick={() => handleProfileScroll("hero")}
                            />
                            <ProfileMenuItem
                              icon={Archive}
                              label="Generated projects"
                              onClick={() => handleProfileScroll("details")}
                            />
                            <ProfileMenuItem
                              icon={Download}
                              label="Downloads"
                              onClick={() => handleProfileScroll("details")}
                            />
                          </div>

                          <div className="profile-theme-panel">
                            <div className="profile-theme-heading">
                              <span className="profile-menu-icon" aria-hidden="true">
                                <Palette size={19} strokeWidth={2} />
                              </span>
                              <div>
                                <span>Themes</span>
                                <small>{currentThemeLabel}</small>
                              </div>
                            </div>
                            <div
                              className="profile-theme-options"
                              aria-label="Theme options"
                            >
                              {THEME_OPTIONS.map((option) => {
                                const ThemeIcon = option.icon;
                                return (
                                  <button
                                    type="button"
                                    key={option.value}
                                    className={
                                      themePreference === option.value
                                        ? "active"
                                        : ""
                                    }
                                    aria-pressed={themePreference === option.value}
                                    onClick={() => setThemePreference(option.value)}
                                  >
                                    <ThemeIcon size={14} />
                                    <span>{option.label}</span>
                                  </button>
                                );
                              })}
                            </div>
                          </div>

                          <div className="profile-menu-divider" />

                          <ProfileMenuItem
                            icon={LogOut}
                            label="Log out"
                            onClick={handleLogout}
                          />
                        </div>
                      </div>
                    </>
                  ) : null}
                </div>
              ) : (
                <>
                  <button
                    type="button"
                    className="text-nav"
                    onClick={() => openAuth("login")}
                  >
                    <span>Log in</span>
                  </button>
                  <button
                    type="button"
                    className="header-signup"
                    onClick={() => openAuth("signup")}
                  >
                    <span>Sign up</span>
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="page-shell">
        <section className="hero-section" id="hero">
          <div className="hero-grid">
            <div className="hero-content">
              <h1 className="hero-title">
                Design <span>any</span> project.
                <br />
                Build with a plan.
              </h1>

              <p className="hero-copy">
                Tell us what you want to build. We’ll propose multiple project
                options for any stack or topic, from React and Node.js to mobile
                apps, AI tools, games, dashboards, automation, and DevOps. Pick
                one and get a full execution plan.
              </p>

              <div className="hero-actions">
                <button
                  type="button"
                  className="hero-primary"
                  onClick={() => scrollToSection("suggest")}
                >
                  <span>Get project options</span>
                  <ArrowRight size={22} />
                </button>
              </div>
            </div>

            <Link
              to="/how-it-works"
              className="hero-card"
              aria-label="How it works"
            >
              <div className="hero-card-header">
                <span className="how-icon" aria-hidden="true">
                  <InfinityLogo size={62} />
                </span>
                <div>
                  <p className="section-kicker">How it works</p>
                  <h3>Plan → pick → ship</h3>
                </div>
              </div>
              <p>
                You describe the target system. We generate options, then expand
                the selected option into a full implementation blueprint.
              </p>
              <ul>
                <li>Architecture + feature scope</li>
                <li>Stack and tooling recommendations</li>
                <li>Step-by-step implementation</li>
                <li>Deliverables + risks</li>
              </ul>
              <div className="hero-card-cta">
                <span>Learn more</span>
                <ArrowRight size={18} />
              </div>
            </Link>
          </div>
        </section>

        <section className="suggest-panel" id="suggest">
          <div className="suggest-header">
            <div>
              <p className="section-kicker">AI Planner</p>
              <h3>Describe what you want to build</h3>
              <p>
                We’ll suggest multiple project options, then generate full
                details for your pick.
              </p>
            </div>
          </div>

          <div className="suggest-topics-wrapper">
            <p className="suggest-topics-label">Try a topic or stack:</p>
            <div className="tag-strip suggest-panel-tags">
              {TECH_TAGS.map((tag) => (
                <button
                  key={tag}
                  type="button"
                  onClick={() => handleTagSuggest(tag)}
                >
                  {tag}
                </button>
              ))}
            </div>
          </div>

          <form className="suggest-form" onSubmit={handleSuggest}>
            <textarea
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
              placeholder="Example: I want a React and Node.js project for a task management app with auth, dashboards, and real-time updates."
              rows={5}
            />
            <button type="submit" disabled={suggestBusy}>
              {suggestBusy ? "Thinking…" : "Get project options"}
            </button>
          </form>

          {suggestions.length ? (
            <div className="suggestions-grid" id="suggestions">
              {suggestions.map((sugg) => {
                const key = `${sugg.title}-${sugg.category}-${sugg.difficulty_level}`;
                const selected =
                  selectedSuggestion &&
                  selectedSuggestion.title === sugg.title &&
                  selectedSuggestion.category === sugg.category &&
                  selectedSuggestion.difficulty_level === sugg.difficulty_level;

                return (
                  <button
                    key={key}
                    type="button"
                    className="suggestion-card"
                    onClick={() => handleSelectSuggestion(sugg)}
                    disabled={detailsBusy}
                    aria-pressed={selected}
                  >
                    <div>
                      <div className="suggestion-meta">
                        <span>{formatProjectLabel(sugg.category)}</span>
                        <span>{formatProjectLabel(sugg.difficulty_level)}</span>
                      </div>
                      <strong>{sugg.title}</strong>
                      <p>{sugg.rationale}</p>
                    </div>
                    <ArrowRight size={18} />
                  </button>
                );
              })}
            </div>
          ) : null}
        </section>

        {(message || error) && (
          <section className="feedback-strip">
            {message ? <div className="feedback success">{message}</div> : null}
            {error ? <div className="feedback error">{error}</div> : null}
          </section>
        )}

        {details ? (
          <section className="results-panel" id="details">
            <div className="results-head">
              <div>
                <p className="section-kicker">Project details</p>
                <h2>{details.title}</h2>
                <p className="section-kicker">
                  {formatProjectLabel(details.category)} ·{" "}
                  {formatProjectLabel(details.difficulty_level)}
                </p>
              </div>
            </div>

            <div className="results-summary">
              <article>
                <p className="section-kicker">Rationale</p>
                <p>{details.rationale}</p>
              </article>
              <article>
                <p className="section-kicker">Overview</p>
                <p>{details.overview}</p>
              </article>
            </div>

            <div className="results-grid">
              <article className="info-card">
                <p className="section-kicker">Architecture</p>
                <ul className="compact-list">
                  {details.architecture.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </article>

              <article className="info-card">
                <p className="section-kicker">Recommended tools</p>
                <ul className="compact-list">
                  {details.recommended_tools.map((tool) => (
                    <li key={tool}>{tool}</li>
                  ))}
                </ul>
              </article>
            </div>

            <div className="results-grid">
              <article className="info-card">
                <p className="section-kicker">Implementation steps</p>
                <ol className="steps-list">
                  {details.implementation_steps.map((step) => (
                    <li key={step}>{step}</li>
                  ))}
                </ol>
              </article>

              <article className="info-card">
                <p className="section-kicker">Deliverables</p>
                <ul className="compact-list">
                  {details.deliverables.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>

                <p className="section-kicker" style={{ marginTop: 18 }}>
                  Risks
                </p>
                <ul className="compact-list">
                  {details.risks.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </article>
            </div>
          </section>
        ) : detailsBusy ? (
          <section className="feedback-strip" id="details">
            <div className="feedback">Generating details…</div>
          </section>
        ) : null}
      </main>

      <footer className="footer-bar">
        <div className="footer-left">
          <InfinityLogo size={32} />
          <span>© 2026 ProjectForge</span>
          <span>built for engineers who ship.</span>
        </div>
        <div className="footer-right">
          <span className="quota-dot" />
          <span>operational</span>
          <span>v1.0.0</span>
          {signedIn && (
            <button
              type="button"
              className="footer-link"
              onClick={handleLogout}
            >
              Sign Out
            </button>
          )}
        </div>
      </footer>

      {authOpen ? (
        <div className="auth-overlay" onClick={() => setAuthOpen(false)}>
          <div
            className="auth-modal"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="auth-header">
              <div>
                <p className="section-kicker">{authHeader.kicker}</p>
                <h3>{authHeader.title}</h3>
              </div>
              <button
                type="button"
                className="icon-button"
                onClick={() => setAuthOpen(false)}
              >
                <X size={18} />
              </button>
            </div>

            {showAuthSwitch ? (
              <div className="auth-switch">
                <button
                  type="button"
                  className={authMode === "login" ? "active" : ""}
                  onClick={() => setAuthMode("login")}
                >
                  Login
                </button>
                <button
                  type="button"
                  className={authMode === "signup" ? "active" : ""}
                  onClick={() => setAuthMode("signup")}
                >
                  Sign up
                </button>
              </div>
            ) : null}

            {(message || error) && (
              <div className="auth-feedback-stack">
                {message ? (
                  <div className="feedback success" role="status">
                    {message}
                  </div>
                ) : null}
                {error ? (
                  <div className="feedback error" role="alert">
                    {error}
                  </div>
                ) : null}
              </div>
            )}

            {authMode === "verify" ? (
              <form className="auth-form" onSubmit={handleVerifySubmit}>
                <label>
                  <span>Email</span>
                  <input
                    type="email"
                    value={verificationEmail || credentials.email}
                    onChange={(event) => setVerificationEmail(event.target.value)}
                    placeholder="you@example.com"
                    required
                  />
                </label>
                <label>
                  <span>Verification code</span>
                  <input
                    type="text"
                    inputMode="numeric"
                    autoComplete="one-time-code"
                    value={verificationCode}
                    onChange={(event) =>
                      setVerificationCode(event.target.value.replace(/\D/g, "").slice(0, 6))
                    }
                    placeholder="6-digit code"
                    minLength={6}
                    maxLength={6}
                    required
                  />
                </label>
                <button
                  type="submit"
                  className="generate-button auth-submit"
                  disabled={authBusy}
                >
                  <span>{authBusy ? "Verifying..." : "Verify email"}</span>
                  <ArrowRight size={24} />
                </button>
                <button
                  type="button"
                  className="auth-secondary"
                  onClick={handleResendVerification}
                  disabled={resendBusy}
                >
                  {resendBusy ? "Sending..." : "Resend code"}
                </button>
              </form>
            ) : authMode === "forgot" ? (
              <form className="auth-form" onSubmit={handleForgotPasswordSubmit}>
                <label>
                  <span>Email</span>
                  <input
                    type="email"
                    value={resetEmail}
                    onChange={(event) => setResetEmail(event.target.value)}
                    placeholder="you@example.com"
                    required
                  />
                </label>
                <button
                  type="submit"
                  className="generate-button auth-submit"
                  disabled={authBusy}
                >
                  <span>{authBusy ? "Sending..." : "Send reset code"}</span>
                  <ArrowRight size={24} />
                </button>
                <button
                  type="button"
                  className="auth-secondary"
                  onClick={() => openAuth("login")}
                >
                  Back to login
                </button>
              </form>
            ) : authMode === "reset" ? (
              <form className="auth-form" onSubmit={handleResetPasswordSubmit}>
                <label>
                  <span>Email</span>
                  <input
                    type="email"
                    value={resetEmail}
                    onChange={(event) => setResetEmail(event.target.value)}
                    placeholder="you@example.com"
                    required
                  />
                </label>
                <label>
                  <span>Reset code</span>
                  <input
                    type="text"
                    inputMode="numeric"
                    autoComplete="one-time-code"
                    value={verificationCode}
                    onChange={(event) =>
                      setVerificationCode(event.target.value.replace(/\D/g, "").slice(0, 6))
                    }
                    placeholder="6-digit code"
                    minLength={6}
                    maxLength={6}
                    required
                  />
                </label>
                <label>
                  <span>New password</span>
                  <input
                    type="password"
                    value={resetPassword}
                    onChange={(event) => setResetPassword(event.target.value)}
                    placeholder="Minimum 8 characters"
                    minLength={8}
                    required
                  />
                </label>
                <button
                  type="submit"
                  className="generate-button auth-submit"
                  disabled={authBusy}
                >
                  <span>{authBusy ? "Resetting..." : "Reset password"}</span>
                  <ArrowRight size={24} />
                </button>
                <button
                  type="button"
                  className="auth-secondary"
                  onClick={handleForgotPasswordSubmit}
                  disabled={authBusy}
                >
                  Resend reset code
                </button>
              </form>
            ) : (
              <form className="auth-form" onSubmit={handleAuthSubmit}>
                <label>
                  <span>Email</span>
                  <input
                    type="email"
                    value={credentials.email}
                    onChange={(event) =>
                      updateCredentials("email", event.target.value)
                    }
                    placeholder="you@example.com"
                    required
                  />
                </label>
                <label>
                  <span>Password</span>
                  <input
                    type="password"
                    value={credentials.password}
                    onChange={(event) =>
                      updateCredentials("password", event.target.value)
                    }
                    placeholder="Minimum 8 characters"
                    minLength={8}
                    required
                  />
                </label>
                {authMode === "login" ? (
                  <button
                    type="button"
                    className="auth-link-button"
                    onClick={() => openAuth("forgot")}
                  >
                    Forgot password?
                  </button>
                ) : null}
                <button
                  type="submit"
                  className="generate-button auth-submit"
                  disabled={authBusy}
                >
                  <span>
                    {authBusy
                      ? "Working..."
                      : authMode === "signup"
                        ? "Create account"
                        : "Log in"}
                  </span>
                  <ArrowRight size={24} />
                </button>
              </form>
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}

export default App;
