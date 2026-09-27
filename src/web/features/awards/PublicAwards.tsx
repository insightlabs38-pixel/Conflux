import { useEffect, useState } from "react";
import { Card } from "../../components/Card";
import { ErrorState } from "../../components/ErrorState";

type Award = {
  public_id: string;
  name: string;
  description: string;
  winners: { project: string; project_name: string }[];
};

export function PublicAwards({ eventId }: { eventId: string }) {
  const [awards, setAwards] = useState<Award[]>([]);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
    fetch(`/api/v1/events/${eventId}/awards/`)
      .then((response) => {
        if (!response.ok)
          throw new Error(`Could not load awards (${response.status}).`);
        return response.json() as Promise<Award[]>;
      })
      .then((items) => {
        if (active && Array.isArray(items)) {
          setAwards(items);
          setError("");
        }
      })
      .catch((cause: unknown) => {
        if (active)
          setError(
            cause instanceof Error ? cause.message : "Could not load awards.",
          );
      });
    return () => {
      active = false;
    };
  }, [eventId, retry]);
  if (error)
    return (
      <ErrorState
        message={error}
        onRetry={() => setRetry((count) => count + 1)}
      />
    );
  if (awards.length === 0) return null;
  return (
    <section aria-label="Awards">
      <h2>Awards</h2>
      <ul>
        {awards.map((award) => (
          <li key={award.public_id}>
            <Card title={award.name}>
              {award.description && <p>{award.description}</p>}
              <ul>
                {award.winners.map((winner) => (
                  <li key={winner.project}>{winner.project_name}</li>
                ))}
              </ul>
            </Card>
          </li>
        ))}
      </ul>
    </section>
  );
}
