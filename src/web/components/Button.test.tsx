// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { expect, it } from "vitest";
import { Button, buttonClass } from "./Button";
(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

async function render(node: React.ReactNode) {
  const host = document.createElement("div");
  const root = createRoot(host);
  await act(async () => root.render(node));
  return host.querySelector("button")!;
}

it("is secondary unless a caller opts into primary, so a context never gains a second filled button by default", async () => {
  const button = await render(<Button>Cancel</Button>);
  expect(button.className).toBe("cx-button cx-button--secondary");
  expect(button.type).toBe("button");
});

it("renders each variant and size as a class the stylesheet defines", async () => {
  expect(
    (await render(<Button variant="primary">Save</Button>)).className,
  ).toBe("cx-button cx-button--primary");
  expect(
    (
      await render(
        <Button variant="ghost" size="sm">
          Notes
        </Button>,
      )
    ).className,
  ).toBe("cx-button cx-button--ghost cx-button--sm");
  expect(
    (
      await render(
        <Button variant="danger" size="lg" className="x">
          Delete
        </Button>,
      )
    ).className,
  ).toBe("cx-button cx-button--danger cx-button--lg x");
  expect(buttonClass()).toBe("cx-button cx-button--secondary");
});

it("passes native attributes through and stays disabled", async () => {
  const button = await render(
    <Button disabled aria-describedby="why">
      Apply
    </Button>,
  );
  expect(button.disabled).toBe(true);
  expect(button.getAttribute("aria-describedby")).toBe("why");
});
