import { ButtonLink } from "../../components/Foundation";
import { ErrorState } from "../../components/ErrorState";
import { useLoad } from "../../hooks/useLoad";

type Award = {
  public_id: string;
  name: string;
  description: string;
  winners: { project: string; project_name: string }[];
};

export function PublicAwards({ eventId }: { eventId: string }) {
  const { data, error, reload } = useLoad<Award[]>(
    `/api/v1/events/${eventId}/awards/`,
    { describe: (status) => `Could not load awards (${status}).` },
  );
  const awards = Array.isArray(data) ? data : [];
  if (error)
    return <ErrorState kind="read" message={error.message} onRetry={reload} />;
  if (awards.length === 0) return null;
  return (
    <section aria-label="Awards">
      <h2>Awards</h2>
      <ul className="cx-results">
        {awards.map((award) => (
          <li key={award.public_id}>
            <article className="cx-award-section">
              <header>
                <p className="cx-event-kicker">Award</p>
                <h3>{award.name}</h3>
                {award.description && <p>{award.description}</p>}
              </header>
              <ul className="cx-grid">
                {award.winners.map((winner) => (
                  <li key={winner.project} className="cx-award-winner">
                    <h4>{winner.project_name}</h4>
                    <ButtonLink
                      href={`/e/${eventId}/results/projects/${winner.project}/`}
                      variant="secondary"
                    >
                      Project highlight
                    </ButtonLink>
                  </li>
                ))}
              </ul>
            </article>
          </li>
        ))}
      </ul>
    </section>
  );
}
