import { useEffect, useState } from "react";
import { Card } from "../../components/Card";

type Award = {
  public_id: string;
  name: string;
  description: string;
  winners: { project: string; project_name: string }[];
};

export function PublicAwards({ eventId }: { eventId: string }) {
  const [awards, setAwards] = useState<Award[]>([]);
  useEffect(() => {
    let active = true;
    fetch(`/api/v1/events/${eventId}/awards/`)
      .then((response) =>
        response.ok ? (response.json() as Promise<Award[]>) : [],
      )
      .then((items) => {
        if (active && Array.isArray(items)) setAwards(items);
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, [eventId]);
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
