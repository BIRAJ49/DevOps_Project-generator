import { Link } from "react-router-dom";
import { Mail, Send } from "lucide-react";
import { useState } from "react";
import { InfinityLogo } from "../components/InfinityLogo";
import { request } from "../api";

const INITIAL_FORM = {
  name: "",
  email: "",
  subject: "",
  message: "",
};

export default function Contact() {
  const [form, setForm] = useState(INITIAL_FORM);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  function updateField(field, value) {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));
    setSubmitted(false);
    setError("");
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setBusy(true);
    setSubmitted(false);
    setError("");

    try {
      await request("/api/contact", {
        method: "POST",
        body: JSON.stringify(form),
      });
      setSubmitted(true);
      setForm(INITIAL_FORM);
    } catch (requestError) {
      setError(requestError.message || "Failed to send your message.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar-inner">
          <Link to="/" className="brand-lockup" aria-label="Back to app">
            <span className="brand-orb" aria-hidden="true">
              <InfinityLogo size={66} />
            </span>
            <span className="brand-text">
              Project<span>Ops</span>
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
        <section className="contact-panel">
          <div className="contact-header">
            <div>
              <p className="section-kicker">Contact</p>
              <h2>Get in touch</h2>
              <p>
                Send feedback, support questions, or project workflow requests.
              </p>
            </div>
          </div>

          <div className="contact-layout">
            <form className="contact-form" onSubmit={handleSubmit}>
              <div className="contact-field-row">
                <label>
                  <span>Name</span>
                  <input
                    type="text"
                    value={form.name}
                    onChange={(event) => updateField("name", event.target.value)}
                    placeholder="Your name"
                    required
                  />
                </label>

                <label>
                  <span>Email</span>
                  <input
                    type="email"
                    value={form.email}
                    onChange={(event) => updateField("email", event.target.value)}
                    placeholder="you@example.com"
                    required
                  />
                </label>
              </div>

              <label>
                <span>Subject</span>
                <input
                  type="text"
                  value={form.subject}
                  onChange={(event) => updateField("subject", event.target.value)}
                  placeholder="How can we help?"
                  required
                />
              </label>

              <label>
                <span>Message</span>
                <textarea
                  value={form.message}
                  onChange={(event) => updateField("message", event.target.value)}
                  placeholder="Share the details..."
                  rows={7}
                  required
                />
              </label>

              <button type="submit" className="contact-submit" disabled={busy}>
                <span>{busy ? "Sending..." : "Send message"}</span>
                <Send size={20} />
              </button>

              {submitted ? (
                <div className="feedback success" role="status">
                  Thank you for your message. We’ll get back to you soon.
                </div>
              ) : null}
              {error ? (
                <div className="feedback error" role="alert">
                  {error}
                </div>
              ) : null}
            </form>

            <aside className="contact-aside" aria-label="Contact details">
              <article className="contact-card">
                <Mail size={20} />
                <div>
                  <p className="section-kicker">Email</p>
                  <a href="mailto:terms301@gmail.com">terms301@gmail.com</a>
                </div>
              </article>

            </aside>
          </div>
        </section>
      </main>
    </div>
  );
}
