import Link from "next/link";

const principles = [
  ["Story first", "Questions reconstruct what actually happened, not what someone says they might do."],
  ["Blackout by default", "Exploratory studies keep the proposed solution out of the interview until a deliberate concept reveal."],
  ["Evidence intact", "Participant messages are HUMAN_INTERVIEW evidence; AI facilitation is labeled separately."],
];

export default function Home() {
  return (
    <main className="landing-shell">
      <header className="landing-nav">
        <BrandMark />
      </header>

      <section className="hero" aria-labelledby="hero-title">
        <div className="hero-copy">
          <h1 id="hero-title">A more human interview, facilitated by AI.</h1>
          <p className="hero-lede">
            A lightweight companion for shareable, conversational research studies.
            Participants always know the interviewer is AI, remain anonymous by default,
            and can stop or delete their responses.
          </p>
          <div className="hero-note">
            <span className="status-dot" aria-hidden="true" />
            Participant access happens through a private, high-entropy study link.
          </div>
        </div>

        <article className="sample-card" aria-label="Sample participant welcome">
          <div className="sample-topline">
            <span>MIGHTSHAPE RESEARCH</span>
            <span className="mode-pill">SOLUTION BLACKOUT</span>
          </div>
          <h2>Thanks for taking part.</h2>
          <p>
            I’m an AI interviewer helping a design team understand what actually
            happens in this situation. There are no right answers.
          </p>
          <div className="sample-question">
            <span>AI INTERVIEWER</span>
            Tell me about the last specific time this happened. What did you do first?
          </div>
          <div className="sample-meta">
            <span>~10 minutes</span>
            <span>Anonymous ID</span>
            <span>Stop anytime</span>
          </div>
        </article>
      </section>

      <section className="principle-grid" aria-label="Research safeguards">
        {principles.map(([title, description], index) => (
          <article className="principle" key={title}>
            <span className="principle-index">0{index + 1}</span>
            <h2>{title}</h2>
            <p>{description}</p>
          </article>
        ))}
      </section>

      <footer className="landing-footer">
        <p>Think wider. Frame better. Build what matters.</p>
        <Link href="/privacy">Participant privacy</Link>
      </footer>
    </main>
  );
}

function BrandMark() {
  return (
    <div className="brand-lockup" aria-label="MightShape">
      <span className="brand-glyph" aria-hidden="true">
        {Array.from({ length: 10 }, (_, index) => (
          <i key={index} style={{ "--node": index } as React.CSSProperties} />
        ))}
      </span>
      <span>MIGHTSHAPE</span>
    </div>
  );
}
