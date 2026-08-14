import Link from "next/link";

export const metadata = { title: "Participant privacy" };

export default function PrivacyPage() {
  return (
    <main className="document-shell">
      <Link className="back-link" href="/">← MightShape Research</Link>
      <p className="kicker">PARTICIPANT PRIVACY</p>
      <h1>Research without unnecessary identity.</h1>
      <p className="document-lede">
        Each study shows its own purpose, duration, data-use terms, reviewers,
        quotation policy, and configured retention plan before you consent.
      </p>
      <section>
        <h2>What the app does</h2>
        <ul>
          <li>Uses an anonymous participant code such as P-001 by default.</li>
          <li>Does not ask for a name or email to join an interview.</li>
          <li>Removes likely email addresses and phone numbers before storage.</li>
          <li>Labels participant responses as human interview evidence and AI messages separately.</li>
          <li>Lets a participant stop without explanation and delete their transcript from the interview page.</li>
        </ul>
      </section>
      <section>
        <h2>What participants should do</h2>
        <p>
          Avoid sharing names, contact information, exact addresses, confidential
          records, or other details that identify you or someone else. Automated
          redaction is limited and cannot guarantee complete anonymization.
        </p>
      </section>
      <section>
        <h2>Who controls the study</h2>
        <p>
          The research team named on the consent screen controls the study and can
          review its transcript. MightShape is an interviewing tool, not the
          study sponsor. Questions about a specific study should go to that team.
        </p>
      </section>
    </main>
  );
}
