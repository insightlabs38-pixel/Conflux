import type { ReactNode } from "react";
import { Avatar, PersonCard } from "./Foundation";
import { Badge } from "./Badge";

export type PersonIdentity = {
  profile_url?: string;
  skills?: string[];
  interests?: string[];
  preferred_roles?: string[];
  user_public_id: string;
  username: string;
  display_name: string;
  avatar_url: string;
  bio: string;
  location: string;
  links: { label: string; url: string }[];
};
export function SkillTags({ values }: { values: string[] }) {
  return (
    <ul className="cx-tags" aria-label="Skills and interests">
      {Array.from(new Set(values)).map((value) => (
        <li key={value}>
          <Badge>{value}</Badge>
        </li>
      ))}
    </ul>
  );
}
export function ProfileHeader({
  person,
  children,
  headingAs: Heading = "h3",
}: {
  headingAs?: "h2" | "h3";
  person: PersonIdentity;
  children?: ReactNode;
}) {
  return (
    <header className="cx-profile-header">
      <Avatar name={person.display_name} src={person.avatar_url} size="large" />
      <div>
        <Heading>{person.display_name}</Heading>
        <p className="cx-metadata">
          @{person.username}
          {person.location ? ` · ${person.location}` : ""}
        </p>
        {person.bio && <p>{person.bio}</p>}
        <ul className="cx-profile-links">
          {person.links.map((link) => (
            <li key={link.url}>
              <a href={link.url} rel="noopener noreferrer" target="_blank">
                {link.label}
              </a>
            </li>
          ))}
        </ul>
        {children}
      </div>
    </header>
  );
}
export function PersonRow({
  person,
  fallback,
  role,
  children,
}: {
  person?: PersonIdentity;
  fallback: string;
  role?: string;
  children?: ReactNode;
}) {
  const name = person?.display_name || fallback;
  return (
    <div className="cx-person-row">
      <Avatar name={name} src={person?.avatar_url} />
      <div>
        <strong>
          {person?.profile_url ? <a href={person.profile_url}>{name}</a> : name}
        </strong>
        {role && <p className="cx-metadata">{role}</p>}
      </div>
      {children}
    </div>
  );
}
export function IdentityCard({
  person,
  fallback,
  role,
  description,
  children,
}: {
  person?: PersonIdentity;
  fallback: string;
  role?: string;
  description?: string;
  children?: ReactNode;
}) {
  return (
    <PersonCard
      href={person?.profile_url}
      name={person?.display_name || fallback}
      avatar={person?.avatar_url}
      role={role}
      description={description || person?.bio}
    >
      {children}
    </PersonCard>
  );
}
