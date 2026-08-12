"use client";

import { CSSProperties, FormEvent, useEffect, useRef, useState } from "react";

type Study = {
  title: string;
  purpose: string;
  durationMinutes: number;
  interviewMode: "SOLUTION_BLACKOUT" | "CONCEPT_REVEAL";
  conceptDescription: string | null;
  dataCollected: string;
  reviewerDescription: string;
  deidentifiedQuotesAllowed: boolean;
  retentionDays: number;
  consentVersion: string;
};

type Message = {
  id?: string;
  role: "USER" | "ASSISTANT";
  content: string;
  provenance?: string;
  redacted?: boolean;
};

type Session = {
  participantCode: string;
  sessionToken: string;
  status: "ACTIVE" | "STOPPED" | "COMPLETED";
  messages: Message[];
};

export function InterviewClient({ token }: { token: string }) {
  const [study, setStudy] = useState<Study | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [consented, setConsented] = useState(false);
  const [draft, setDraft] = useState("");
  const [error, setError] = useState("");
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleted, setDeleted] = useState(false);
  const transcriptEnd = useRef<HTMLDivElement>(null);
  const storageKey = `dc-interview:${token}`;
  const apiRoot = `/api/studies/${encodeURIComponent(token)}`;

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const savedToken = window.sessionStorage.getItem(storageKey);
        const response = await fetch(apiRoot, {
          cache: "no-store",
          headers: savedToken ? { Authorization: `Bearer ${savedToken}` } : undefined,
        });
        const payload = (await response.json()) as {
          error?: string;
          study: Study;
        };
        if (!response.ok) {
          if (savedToken && (response.status === 401 || response.status === 404)) {
            window.sessionStorage.removeItem(storageKey);
          }
          throw new Error(payload.error ?? "This study is unavailable.");
        }
        if (cancelled) return;
        setStudy(payload.study);
        if (savedToken) {
          const resumed = await fetch(`${apiRoot}/session`, {
            cache: "no-store",
            headers: { Authorization: `Bearer ${savedToken}` },
          });
          if (resumed.ok) {
            const saved = (await resumed.json()) as Omit<Session, "sessionToken">;
            if (!cancelled) {
              setSession({ ...saved, sessionToken: savedToken });
            }
          } else {
            window.sessionStorage.removeItem(storageKey);
          }
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : "This study is unavailable.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [apiRoot, storageKey]);

  useEffect(() => {
    transcriptEnd.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [session?.messages.length, busy]);

  async function begin() {
    if (!study || !consented) return;
    setBusy(true);
    setError("");
    try {
      const response = await fetch(`${apiRoot}/participants`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ consent: true, consentVersion: study.consentVersion }),
      });
      const payload = (await response.json()) as Session & { error?: string };
      if (!response.ok) throw new Error(payload.error ?? "Unable to begin the interview.");
      window.sessionStorage.setItem(storageKey, payload.sessionToken);
      setSession(payload);
    } catch (beginError) {
      setError(beginError instanceof Error ? beginError.message : "Unable to begin the interview.");
    } finally {
      setBusy(false);
    }
  }

  async function send(event: FormEvent) {
    event.preventDefault();
    if (!session || !draft.trim() || busy || session.status !== "ACTIVE") return;
    const outgoing = draft.trim();
    setDraft("");
    await submitTurn({ message: outgoing }, outgoing);
  }

  async function skipQuestion() {
    if (!session || busy || session.status !== "ACTIVE") return;
    await submitTurn({ action: "SKIP" });
  }

  async function submitTurn(
    body: { message?: string; action?: "SKIP" },
    restoreDraft = "",
  ) {
    if (!session || busy || session.status !== "ACTIVE") return;
    setBusy(true);
    setError("");
    try {
      const response = await authorizedFetch(`${apiRoot}/messages`, session.sessionToken, {
        method: "POST",
        body: JSON.stringify(body),
      });
      const payload = (await response.json()) as {
        error?: string;
        participantMessage: Message;
        assistantMessage: Message;
        status: Session["status"];
        interviewMode: Study["interviewMode"];
        conceptDescription: string | null;
      };
      if (!response.ok) throw new Error(payload.error ?? "Your response could not be sent.");
      setSession((current) =>
        current
          ? {
              ...current,
              status: payload.status,
              messages: [
                ...current.messages,
                payload.participantMessage,
                payload.assistantMessage,
              ],
            }
          : current,
      );
      setStudy((current) =>
        current
          ? {
              ...current,
              interviewMode: payload.interviewMode,
              conceptDescription: payload.conceptDescription,
            }
          : current,
      );
    } catch (sendError) {
      if (restoreDraft) setDraft(restoreDraft);
      setError(sendError instanceof Error ? sendError.message : "Your response could not be sent.");
    } finally {
      setBusy(false);
    }
  }

  async function stop() {
    if (!session || busy) return;
    setBusy(true);
    setError("");
    try {
      const response = await authorizedFetch(`${apiRoot}/stop`, session.sessionToken, {
        method: "POST",
      });
      const payload = (await response.json()) as { error?: string; status: "STOPPED" };
      if (!response.ok) throw new Error(payload.error ?? "Unable to stop the interview.");
      setSession((current) => (current ? { ...current, status: "STOPPED" } : current));
    } catch (stopError) {
      setError(stopError instanceof Error ? stopError.message : "Unable to stop the interview.");
    } finally {
      setBusy(false);
    }
  }

  async function removeTranscript() {
    if (!session || busy) return;
    setBusy(true);
    setError("");
    try {
      const response = await authorizedFetch(`${apiRoot}/session`, session.sessionToken, {
        method: "DELETE",
      });
      const payload = (await response.json()) as { error?: string; deleted?: boolean };
      if (!response.ok) throw new Error(payload.error ?? "Unable to delete your responses.");
      window.sessionStorage.removeItem(storageKey);
      setSession(null);
      setDeleted(true);
      setConfirmDelete(false);
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "Unable to delete your responses.");
    } finally {
      setBusy(false);
    }
  }

  if (loading) {
    return (
      <main className="interview-shell centered" aria-busy="true">
        <div className="loading-mark" aria-hidden="true">◇</div>
        <p>Opening the research study…</p>
      </main>
    );
  }

  if (error && !study) {
    return (
      <main className="interview-shell centered">
        <p className="kicker">DESIGN COUNCIL RESEARCH</p>
        <h1>This study is unavailable.</h1>
        <p className="error-copy">{error}</p>
      </main>
    );
  }

  if (deleted) {
    return (
      <main className="interview-shell centered">
        <div className="success-mark" aria-hidden="true">✓</div>
        <h1>Your responses were deleted.</h1>
        <p>The transcript and participant session have been removed. Only a non-content deletion receipt remains.</p>
      </main>
    );
  }

  if (!study) return null;
  if (!session) {
    return (
      <main className="consent-shell">
        <CouncilOrbit className="consent-orbit" />
        <header className="study-brand">
          <span aria-hidden="true">◇</span>
          <span>Design Council Research</span>
        </header>
        <section className="consent-card" aria-labelledby="study-title">
          <div className="ai-disclosure">
            <span className="ai-orb" aria-hidden="true">AI</span>
            <div>
              <strong>Your interviewer is AI.</strong>
              <p>You’ll have a text conversation with an AI facilitator, not a human researcher.</p>
            </div>
          </div>
          <h1 id="study-title">Your experience, in your words.</h1>
          <p className="consent-study-title">{study.title}</p>
          <p className="consent-purpose">{study.purpose}</p>

          {study.interviewMode === "CONCEPT_REVEAL" && study.conceptDescription ? (
            <div className="concept-card">
              <span>CONCEPT REVEAL</span>
              <p>{study.conceptDescription}</p>
            </div>
          ) : (
            <div className="blackout-card">
              <span>◇ SOLUTION BLACKOUT</span>
              <p>The team’s proposed solution will stay hidden while we learn from your experience.</p>
            </div>
          )}

          <dl className="consent-details">
            <div><dt>Time</dt><dd>About {study.durationMinutes} minutes</dd></div>
            <div><dt>Collected</dt><dd>{study.dataCollected}</dd></div>
            <div><dt>Reviewers</dt><dd>{study.reviewerDescription}</dd></div>
            <div>
              <dt>Quotations</dt>
              <dd>{study.deidentifiedQuotesAllowed ? "De-identified quotations may be used." : "Your responses will not be quoted."}</dd>
            </div>
            <div>
              <dt>Retention plan</dt>
              <dd>
                {study.retentionDays} days. The research team is responsible for
                deleting the study when that period ends.
              </dd>
            </div>
            <div><dt>Your choice</dt><dd>Skip any question, stop anytime, or delete your responses from this page.</dd></div>
          </dl>

          <div className="privacy-nudge">
            Please do not share names, contact details, exact addresses, or confidential records.
            Likely email addresses and phone numbers are removed, but automated redaction is limited.
          </div>

          <label className="consent-check">
            <input
              type="checkbox"
              checked={consented}
              onChange={(event) => setConsented(event.target.checked)}
            />
            <span>I understand the information above and voluntarily agree to take part.</span>
          </label>
          <button className="primary-button" disabled={!consented || busy} onClick={begin}>
            {busy ? "Starting…" : "Begin anonymous interview"}
          </button>
          {error ? <p className="form-error" role="alert">{error}</p> : null}
          <p className="consent-footnote">No name or email is required. You’ll receive an anonymous P-### participant ID.</p>
        </section>
      </main>
    );
  }

  const ended = session.status !== "ACTIVE";
  return (
    <main className="conversation-shell">
      <CouncilOrbit className="active-orbit" />
      <header className="conversation-header">
        <div>
          <p className="kicker">{study.title}</p>
          <h1>Research conversation</h1>
        </div>
        <div className="session-meta">
          <span className="participant-chip">{session.participantCode}</span>
          <span className="ai-chip"><i aria-hidden="true" /> AI INTERVIEWER</span>
          {!ended ? (
            <button className="header-stop" disabled={busy} onClick={stop} type="button">
              Stop anytime
            </button>
          ) : null}
        </div>
      </header>

      <div className={`mode-banner ${study.interviewMode === "SOLUTION_BLACKOUT" ? "blackout" : "reveal"}`}>
        <strong>{study.interviewMode === "SOLUTION_BLACKOUT" ? "◇ SOLUTION BLACKOUT" : "CONCEPT REVEAL"}</strong>
        <span>
          {study.interviewMode === "SOLUTION_BLACKOUT"
            ? "Exploring your real experience before discussing solutions."
            : study.conceptDescription ?? "The study is now exploring a disclosed concept."}
        </span>
      </div>

      <section className="transcript" aria-label="Interview transcript" aria-live="polite">
        {session.messages.map((message, index) => (
          <article className={`message ${message.role === "USER" ? "participant" : "interviewer"}`} key={message.id ?? `${message.role}-${index}`}>
            <span className="message-author">
              {message.role === "USER" ? session.participantCode : "AI INTERVIEWER"}
            </span>
            <p>{message.content}</p>
            {message.redacted ? <small>Likely contact information was removed before storage.</small> : null}
          </article>
        ))}
        {busy ? <div className="thinking" role="status"><i /><i /><i /><span>AI interviewer is responding</span></div> : null}
        <div ref={transcriptEnd} />
      </section>

      {ended ? (
        <section className="ended-card" aria-live="polite">
          <strong>Interview {session.status === "STOPPED" ? "stopped" : "complete"}.</strong>
          <p>Your responses remain stored for the study unless you delete them below.</p>
        </section>
      ) : (
        <form className="reply-form" onSubmit={send}>
          <label htmlFor="participant-reply">Your response</label>
          <textarea
            id="participant-reply"
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            maxLength={4_000}
            rows={4}
            placeholder="Describe what actually happened…"
            disabled={busy}
          />
          <div className="reply-actions">
            <div>
              <button className="skip-button" disabled={busy} onClick={skipQuestion} type="button">
                Skip this question
              </button>
              <span>{draft.length.toLocaleString()} / 4,000</span>
            </div>
            <button className="primary-button compact" disabled={busy || !draft.trim()} type="submit">Send response</button>
          </div>
        </form>
      )}

      {error ? <p className="form-error" role="alert">{error}</p> : null}
      <footer className="participant-controls">
        <span className="participant-agency">You may skip a question, stop, or delete your responses.</span>
        {!confirmDelete ? (
          <button className="danger-link" disabled={busy} onClick={() => setConfirmDelete(true)}>Delete my responses</button>
        ) : (
          <div className="delete-confirm" role="group" aria-label="Confirm transcript deletion">
            <span>This permanently removes your transcript.</span>
            <button className="danger-button" disabled={busy} onClick={removeTranscript}>{busy ? "Deleting…" : "Delete permanently"}</button>
            <button className="text-button" disabled={busy} onClick={() => setConfirmDelete(false)}>Cancel</button>
          </div>
        )}
      </footer>
    </main>
  );
}

function CouncilOrbit({ className }: { className: string }) {
  return (
    <div className={`council-orbit ${className}`} aria-hidden="true">
      {Array.from({ length: 10 }, (_, index) => (
        <i key={index} style={{ "--orbit-node": index } as CSSProperties} />
      ))}
    </div>
  );
}

function authorizedFetch(url: string, sessionToken: string, init: RequestInit) {
  return fetch(url, {
    ...init,
    headers: {
      Authorization: `Bearer ${sessionToken}`,
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
    },
  });
}
