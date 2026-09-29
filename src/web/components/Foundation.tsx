import {
  useId,
  type AnchorHTMLAttributes,
  type HTMLAttributes,
  type InputHTMLAttributes,
  type ReactNode,
  type SelectHTMLAttributes,
  type TextareaHTMLAttributes,
} from "react";

export function ButtonLink({
  variant = "primary",
  className = "",
  ...props
}: AnchorHTMLAttributes<HTMLAnchorElement> & {
  variant?: "primary" | "secondary";
}) {
  return (
    <a className={`cx-button cx-button--${variant} ${className}`} {...props} />
  );
}

export function PageHeader({
  title,
  description,
  eyebrow,
  actions,
  as: Heading = "h2",
}: {
  title: string;
  description?: string;
  eyebrow?: string;
  actions?: ReactNode;
  as?: "h1" | "h2";
}) {
  return (
    <header className="cx-page-header">
      <div>
        {eyebrow && <p className="cx-eyebrow">{eyebrow}</p>}
        <Heading>{title}</Heading>
        {description && (
          <p className="cx-page-header__description">{description}</p>
        )}
      </div>
      {actions && <div className="cx-actions">{actions}</div>}
    </header>
  );
}

export function SectionHeader({
  title,
  children,
}: {
  title: string;
  children?: ReactNode;
}) {
  return (
    <header className="cx-section-header">
      <h3>{title}</h3>
      {children}
    </header>
  );
}

/** Owns the label/description association; child must spread these props onto its control. */
export function Field({
  label,
  hint,
  error,
  children,
}: {
  label: string;
  hint?: string;
  error?: string;
  children: (props: {
    id: string;
    "aria-describedby"?: string;
    "aria-invalid"?: true;
  }) => ReactNode;
}) {
  const id = useId();
  const description =
    [hint && `${id}-hint`, error && `${id}-error`].filter(Boolean).join(" ") ||
    undefined;
  return (
    <div className="cx-field">
      <label htmlFor={id}>{label}</label>
      {children({
        id,
        "aria-describedby": description,
        "aria-invalid": error ? true : undefined,
      })}
      {hint && (
        <p id={`${id}-hint`} className="cx-field__hint">
          {hint}
        </p>
      )}
      {error && (
        <p id={`${id}-error`} className="cx-field__error" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
export function TextInput({
  className = "",
  ...props
}: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={`cx-input ${className}`} {...props} />;
}
export function TextArea({
  className = "",
  ...props
}: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea className={`cx-input ${className}`} {...props} />;
}
export function Select({
  className = "",
  ...props
}: SelectHTMLAttributes<HTMLSelectElement>) {
  return <select className={`cx-input ${className}`} {...props} />;
}
export function SearchInput(props: InputHTMLAttributes<HTMLInputElement>) {
  return <TextInput type="search" {...props} />;
}
export function Checkbox(props: InputHTMLAttributes<HTMLInputElement>) {
  return <TextInput {...props} type="checkbox" />;
}
export function Radio(props: InputHTMLAttributes<HTMLInputElement>) {
  return <TextInput {...props} type="radio" />;
}

export function Avatar({
  name,
  src,
  size = "normal",
}: {
  name: string;
  src?: string;
  size?: "normal" | "large";
}) {
  const initials =
    name
      .trim()
      .split(/\s+/)
      .slice(0, 2)
      .map((part) => Array.from(part)[0] ?? "")
      .join("")
      .toLocaleUpperCase() || "?";
  return (
    <span className={`cx-avatar cx-avatar--${size}`} aria-hidden="true">
      {src ? <img src={src} alt="" loading="lazy" /> : initials}
    </span>
  );
}

export function PersonCard({
  name,
  role,
  description,
  avatar,
  children,
}: {
  name: string;
  role?: string;
  description?: string;
  avatar?: string;
  children?: ReactNode;
}) {
  return (
    <article className="cx-person">
      <Avatar name={name} src={avatar} />
      <div>
        <h3>{name}</h3>
        {role && <p className="cx-person__role">{role}</p>}
        {description && <p>{description}</p>}
        {children}
      </div>
    </article>
  );
}

export function ProjectCard({
  title,
  href,
  summary,
  category,
  attribution,
  cover,
  children,
}: {
  title: string;
  href: string;
  summary?: string;
  category?: string;
  attribution?: string;
  cover?: string;
  children?: ReactNode;
}) {
  return (
    <article className="cx-project-card">
      <div className="cx-project-card__cover" aria-hidden="true">
        {cover ? (
          <img src={cover} alt="" loading="lazy" />
        ) : (
          <span>{title.slice(0, 2).toLocaleUpperCase()}</span>
        )}
      </div>
      <div className="cx-project-card__body">
        {category && <p className="cx-eyebrow">{category}</p>}
        <h3>
          <a href={href}>{title}</a>
        </h3>
        {summary && <p>{summary}</p>}
        {attribution && <p className="cx-metadata">{attribution}</p>}
        {children}
      </div>
    </article>
  );
}

export function Alert({
  tone = "info",
  children,
}: {
  tone?: "info" | "danger" | "warning" | "success";
  children: ReactNode;
}) {
  return (
    <div
      className={`cx-alert cx-alert--${tone}`}
      role={tone === "danger" ? "alert" : "status"}
    >
      {children}
    </div>
  );
}
export function Stack({
  className = "",
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return <div className={`cx-stack ${className}`} {...props} />;
}
export function Grid({
  className = "",
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return <div className={`cx-grid ${className}`} {...props} />;
}
export function Breadcrumbs({
  items,
}: {
  items: { label: string; href?: string }[];
}) {
  return (
    <nav aria-label="Breadcrumb">
      <ol className="cx-breadcrumbs">
        {items.map((item, index) => (
          <li key={index}>
            {item.href ? (
              <a href={item.href}>{item.label}</a>
            ) : (
              <span aria-current="page">{item.label}</span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}
export function DataTable({
  children,
  label,
}: {
  children: ReactNode;
  label: string;
}) {
  return (
    <div
      className="cx-table-region"
      role="region"
      aria-label={label}
      tabIndex={0}
    >
      <table className="cx-table">{children}</table>
    </div>
  );
}
export function Pagination({
  current,
  total,
  previous,
  next,
}: {
  current: number;
  total: number;
  previous?: string;
  next?: string;
}) {
  return (
    <nav aria-label="Pagination" className="cx-pagination">
      {previous && (
        <ButtonLink variant="secondary" href={previous}>
          Previous
        </ButtonLink>
      )}
      <span aria-current="page">
        Page {current} of {total}
      </span>
      {next && (
        <ButtonLink variant="secondary" href={next}>
          Next
        </ButtonLink>
      )}
    </nav>
  );
}
export function Timeline({
  items,
}: {
  items: {
    title: string;
    detail?: string;
    status: "complete" | "current" | "pending";
  }[];
}) {
  return (
    <ol className="cx-timeline">
      {items.map((item, index) => (
        <li
          key={index}
          data-status={item.status}
          aria-current={item.status === "current" ? "step" : undefined}
        >
          <span className="cx-timeline__marker" aria-hidden="true">
            {item.status === "complete" ? "✓" : index + 1}
          </span>
          <div>
            <strong>{item.title}</strong>
            <p className="cx-metadata">
              {item.status}
              {item.detail && ` · ${item.detail}`}
            </p>
          </div>
        </li>
      ))}
    </ol>
  );
}
