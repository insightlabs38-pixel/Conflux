import { Component, type ComponentType, type ReactNode } from "react";
import { ErrorState } from "../../components/ErrorState";

type State = { failed: boolean; attempt: number };

class Boundary extends Component<
  { label: string; children: (attempt: number) => ReactNode },
  State
> {
  state: State = { failed: false, attempt: 0 };
  static getDerivedStateFromError(): Partial<State> {
    return { failed: true };
  }
  render() {
    if (this.state.failed)
      return (
        <section aria-label={this.props.label}>
          <h3>{this.props.label}</h3>
          <ErrorState
            message="This section could not be displayed."
            onRetry={() =>
              this.setState((s) => ({ failed: false, attempt: s.attempt + 1 }))
            }
          />
        </section>
      );
    return this.props.children(this.state.attempt);
  }
}

/** A panel that fails to render (e.g. an unexpected server payload) degrades to a
 * retryable notice instead of taking the whole workspace down with it. */
export function guarded<P extends object>(
  Panel: ComponentType<P>,
  label: string,
): ComponentType<P> {
  return function Guarded(props: P) {
    return (
      <Boundary label={label}>
        {(attempt) => <Panel key={attempt} {...props} />}
      </Boundary>
    );
  };
}
