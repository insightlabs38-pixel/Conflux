# Local API explorer

Open **API explorer** in the operator web application's navigation, or visit
`/?api=explorer` on the web app's origin. The page ships in the existing web
build as a separate lazy-loaded bundle. It uses local assets and the live
`/api/v1/schema/?format=json` contract; no CDN or hosted documentation service
is required. Run the normal self-hosted web/API setup (`make dev` for local
work). This page belongs to the operator web build, not the server-rendered
public event site.

Choose a built-in example or search operations by method/path/summary. Examples
cover health, your identity/workspace IDs, event listing, event detail and event
creation. Selection does not send anything. Read your identity first and copy
real workspace/event public IDs into the required path fields; example bodies
never fabricate identities. The event creation example creates a private draft
and needs an organizer/admin session. Change its slug before creating another.

Edit path/query values and JSON bodies, then send explicitly. Each write requires
an intent checkbox; editing its parameters/body resets that intent. The existing
API enforces roles, scopes, deadlines and validation. HTTP failures remain
visible with their status and response body. Schema/response details are rendered
as text, including HTML content, without executing it.

Session mode sends the current cookie. Bearer mode omits cookies and sends only
the entered scoped token; some operations require a human session and reject
bearer-only calls. The explorer stores neither tokens nor responses in browser
storage. Clear a token by switching authentication or leaving the page. Do not
share screenshots of private API responses or issued credentials.

Supported sending formats are JSON request bodies, path parameters, scalar
form-style queries and scalar JSON-array queries. Multipart/file uploads,
structured query objects, custom header parameters and alternative body formats
require the generated SDK or another client. Their contracts remain browsable.
Only local API v1 routes are sent; redirects are rejected. Requests time out
after 30 seconds and displayed responses are capped at 1 MiB. A timeout/closed
page does not undo a write that the server already accepted; check server state
before retrying a non-idempotent operation.
