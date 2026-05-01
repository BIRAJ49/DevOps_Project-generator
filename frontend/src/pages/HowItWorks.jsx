import { Link } from "react-router-dom";
import { InfinityLogo } from "../components/InfinityLogo";

export default function HowItWorks() {
  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar-inner">
          <Link to="/" className="brand-lockup" aria-label="Back to app">
            <span className="brand-orb" aria-hidden="true">
              <InfinityLogo size={66} />
            </span>
            <span className="brand-text">
              Project<span>Forge</span>
            </span>
          </Link>

          <div className="topbar-actions">
            <Link to="/how-it-works" className="text-nav" aria-current="page">
              <span>How it works</span>
            </Link>
            <Link to="/about" className="text-nav">
              <span>About us</span>
            </Link>
            <Link to="/contact" className="text-nav">
              <span>Contact</span>
            </Link>
            <Link to="/" className="cta-pill">
              <span>Back to app</span>
            </Link>
          </div>
        </div>
      </header>

      <main className="page-shell">
        <section className="results-panel">
          <div className="results-head">
            <div>
              <p className="section-kicker">// how it works</p>
              <h2>
                Plan → pick → <span>ship</span>
              </h2>
              <p className="hero-copy" style={{ maxWidth: 720 }}>
                Describe the target system. We generate multiple project
                options, then expand the option you choose into a detailed
                implementation blueprint.
              </p>
            </div>
          </div>

          <div className="results-grid">
            <article className="info-card">
              <p className="section-kicker">Step 1</p>
              <h3>Describe your project</h3>
              <p>
                Share your goal, constraints, stack preferences, scale, and
                operational needs.
              </p>
            </article>

            <article className="info-card">
              <p className="section-kicker">Step 2</p>
              <h3>Pick an option</h3>
              <p>
                Choose from multiple suggested approaches across web, mobile,
                AI, data, automation, DevOps, and other software domains.
              </p>
            </article>

            <article className="info-card">
              <p className="section-kicker">Step 3</p>
              <h3>Get the full blueprint</h3>
              <p>
                Receive architecture, recommended tools, implementation steps,
                deliverables, and risks.
              </p>
            </article>

            <article className="info-card">
              <p className="section-kicker">What you get</p>
              <ul className="compact-list">
                <li>Architecture + feature scope</li>
                <li>Stack and tooling recommendations</li>
                <li>Step-by-step implementation</li>
                <li>Deliverables + risks</li>
              </ul>
            </article>
          </div>
        </section>
      </main>
    </div>
  );
}
