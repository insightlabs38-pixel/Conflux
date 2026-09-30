/** A real `Response` for fetch mocks that feed the typed client (which reads `text()`/`json()`). */
export function jsonResponse(status: number, body?: unknown): Response {
  return status === 204
    ? new Response(null, { status })
    : new Response(body === undefined ? "{}" : JSON.stringify(body), {
        status,
        headers: { "Content-Type": "application/json" },
      });
}
