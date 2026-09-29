// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import {
  Avatar,
  ButtonLink,
  Checkbox,
  DataTable,
  Field,
  Pagination,
  Radio,
  TextInput,
  Timeline,
} from "./Foundation";
(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

describe("foundation accessibility contracts", () => {
  it("associates label, hint and validation error with the control", () => {
    const container = document.createElement("div");
    const root = createRoot(container);
    act(() =>
      root.render(
        <Field
          label="Project name"
          hint="Use a short name"
          error="Name is required"
        >
          {(props) => <TextInput {...props} required />}
        </Field>,
      ),
    );
    const input = container.querySelector("input")!;
    expect(container.querySelector("label")!.htmlFor).toBe(input.id);
    const described = input.getAttribute("aria-describedby")!.split(" ");
    expect(
      described.map(
        (id) => container.querySelector(`[id="${id}"]`)!.textContent,
      ),
    ).toEqual(["Use a short name", "Name is required"]);
    expect(input.getAttribute("aria-invalid")).toBe("true");
    expect(input.required).toBe(true);
    act(() => root.unmount());
  });
  it("keeps actions as links and choices native and disabled", () => {
    const html = renderToStaticMarkup(
      <>
        <ButtonLink href="/event">Join event</ButtonLink>
        <Checkbox disabled />
        <Radio name="role" value="judge" />
      </>,
    );
    expect(html).toContain('<a class="cx-button cx-button--primary ');
    expect(html).toContain('href="/event"');
    expect(html).toContain('type="checkbox"');
    expect(html).toContain('disabled=""');
    expect(html).toContain('type="radio"');
  });
  it("makes a dense table keyboard-scrollable without losing table semantics", () => {
    const html = renderToStaticMarkup(
      <DataTable label="Assignments">
        <caption>Assigned projects</caption>
        <thead>
          <tr>
            <th scope="col">Project</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Live Wire</td>
          </tr>
        </tbody>
      </DataTable>,
    );
    expect(html).toContain('role="region"');
    expect(html).toContain('tabindex="0"');
    expect(html).toContain("<table");
    expect(html).toContain('scope="col"');
  });
  it("expresses progress and page state without color and omits unavailable navigation", () => {
    const html = renderToStaticMarkup(
      <>
        <Timeline
          items={[
            { title: "Team", status: "complete" },
            { title: "Submit", status: "current" },
          ]}
        />
        <Pagination current={1} total={3} next="?page=2" />
      </>,
    );
    expect(html).toContain('aria-current="step"');
    expect(html).toContain("complete");
    expect(html).toContain('aria-current="page"');
    expect(html).not.toContain("Previous");
  });
  it("initials tolerate empty and non-Latin names without adding redundant accessible text", () => {
    expect(renderToStaticMarkup(<Avatar name="" />)).toContain("?");
    expect(renderToStaticMarkup(<Avatar name="李 明" />)).toContain("李明");
    expect(renderToStaticMarkup(<Avatar name="Sam Rivera" />)).toContain(
      'aria-hidden="true"',
    );
  });
});
