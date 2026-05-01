import { Link } from "react-router-dom";
import { InfinityLogo } from "../components/InfinityLogo";

export default function About() {
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
            <Link to="/how-it-works" className="text-nav">
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
        <section className="manifesto-card">
          <h2>
            About <span>us</span>
          </h2>
          <p>
            We help you go from an idea to an executable project plan. Describe
            what you want to build, pick a suggested project option, and get a
            detailed implementation blueprint.
          </p>
          <p>
            This app focuses on practical outputs: architecture, repo structure,
            stack guidance, and step-by-step setup so you can start fast.
          </p>

          <div className="about-grid">
            <article className="info-card">
              <p className="section-kicker">What we build</p>
              <p>
                ProjectForge turns rough project goals into structured starter
                blueprints for web apps, APIs, mobile apps, AI tools, games,
                dashboards, automation, DevOps, and more.
              </p>
            </article>

            <article className="info-card">
              <p className="section-kicker">Who it helps</p>
              <p>
                It is built for students, junior engineers, founders, and
                builders who want realistic project ideas with enough technical
                direction to begin implementation quickly.
              </p>
            </article>

            <article className="info-card">
              <p className="section-kicker">What you get</p>
              <ul className="compact-list">
                <li>Multiple project ideas across difficulty levels</li>
                <li>Architecture and component guidance</li>
                <li>Recommended tools and implementation steps</li>
                <li>Deliverables, risks, and operational notes</li>
              </ul>
            </article>

            <article className="info-card">
              <p className="section-kicker">Our approach</p>
              <p>
                We keep the output practical and engineering-focused. The goal
                is not to generate vague inspiration, but to give you a clear
                project direction you can refine, build, and show.
              </p>
            </article>
          </div>
        </section>
      </main>
    </div>
  );
}
