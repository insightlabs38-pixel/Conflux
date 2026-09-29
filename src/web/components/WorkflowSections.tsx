import { useId, useRef, useState, type ReactNode } from "react";

type Section = {
  id: string;
  label: string;
  description?: string;
  content: ReactNode;
};

/** Manual-activation tabs retain drafts and buffers in every mounted section. */
export function WorkflowSections({
  label,
  sections,
}: {
  label: string;
  sections: Section[];
}) {
  const prefix = useId();
  const [selected, setSelected] = useState(sections[0]?.id ?? "");
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
            onClick={() => setSelected(section.id)}
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
