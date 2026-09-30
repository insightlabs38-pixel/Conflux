import { useId, useRef, useState, type ReactNode } from "react";
import { useInRouterContext } from "react-router";
import { useUrlParam } from "../lib/urlState";

type Section = {
  id: string;
  label: string;
  description?: string;
  content: ReactNode;
};

type Props = {
  label: string;
  sections: Section[];
  /**
   * Mirror the open section to the `section` search param (panel state: replace, dropped when
   * leaving the view), so another screen can link straight to it, e.g. a readiness item's fix.
   * Only the top-level sections of a destination opt in; nested ones stay local.
   */
  linkable?: boolean;
};

/** Manual-activation tabs retain drafts and buffers in every mounted section. */
export function WorkflowSections({ linkable = false, ...props }: Props) {
  const routed = useInRouterContext();
  return linkable && routed ? (
    <RoutedSections {...props} />
  ) : (
    <LocalSections {...props} />
  );
}

function LocalSections({ label, sections }: Props) {
  const [selected, setSelected] = useState(sections[0]?.id ?? "");
  return (
    <Tabs
      label={label}
      sections={sections}
      selected={selected}
      onSelect={setSelected}
    />
  );
}

function RoutedSections({ label, sections }: Props) {
  const [param, setParam] = useUrlParam("section");
  const [local, setLocal] = useState(sections[0]?.id ?? "");
  // The URL is a request: only one of this list's own sections is honoured.
  const selected = sections.some((section) => section.id === param)
    ? param
    : local;
  return (
    <Tabs
      label={label}
      sections={sections}
      selected={selected}
      onSelect={(id) => {
        setLocal(id);
        setParam(id, { replace: true });
      }}
    />
  );
}

function Tabs({
  label,
  sections,
  selected,
  onSelect,
}: {
  label: string;
  sections: Section[];
  selected: string;
  onSelect: (id: string) => void;
}) {
  const prefix = useId();
  const controls = useRef<(HTMLButtonElement | null)[]>([]);
  return (
    <div className="cx-workflow">
      <div
        className="cx-workflow__navigation"
        role="tablist"
        aria-orientation="vertical"
        aria-label={label}
      >
        {sections.map((section, index) => (
          <button
            key={section.id}
            type="button"
            role="tab"
            id={`${prefix}-${section.id}-tab`}
            aria-controls={`${prefix}-${section.id}-panel`}
            aria-selected={selected === section.id}
            tabIndex={selected === section.id ? 0 : -1}
            ref={(node) => {
              controls.current[index] = node;
            }}
            onClick={() => onSelect(section.id)}
            onKeyDown={(event) => {
              let next = index;
              if (event.key === "ArrowRight" || event.key === "ArrowDown")
                next = (index + 1) % sections.length;
              else if (event.key === "ArrowLeft" || event.key === "ArrowUp")
                next = (index - 1 + sections.length) % sections.length;
              else if (event.key === "Home") next = 0;
              else if (event.key === "End") next = sections.length - 1;
              else return;
              event.preventDefault();
              controls.current[next]?.focus();
            }}
          >
            <span>{section.label}</span>
            {section.description && <small>{section.description}</small>}
          </button>
        ))}
      </div>
      <div className="cx-workflow__content">
        {sections.map((section) => (
          <div
            key={section.id}
            role="tabpanel"
            tabIndex={0}
            id={`${prefix}-${section.id}-panel`}
            aria-labelledby={`${prefix}-${section.id}-tab`}
            hidden={selected !== section.id}
          >
            {section.content}
          </div>
        ))}
      </div>
    </div>
  );
}
