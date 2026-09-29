# Reusable identity

`accounts.UserProfile` attaches display name, optional image URL, biography,
location, safe structured links, skills/interests/preferred roles and visibility
to the existing user. Sign-in names, sessions and external identities are unchanged.
New profiles default to private. Members visibility requires a shared workspace;
public visibility is an explicit opt-in. Public person pages expose identity only.

`GET/PATCH /api/v1/accounts/profile/` reads/edits the authenticated user's profile.
Updates are atomic and audited without copying private biography/link values into
workspace logs. `GET /api/v1/accounts/people/<user>/` enforces visibility and returns
404 for unavailable profiles. Submitted markup remains plain text. URL schemes,
credentials, length, structured link keys and duplicate tags are validated.

Existing event matching signals, availability and team-seeking status remain in
MarketplaceProfile. The marketplace can copy account tags into its editable draft;
only the existing Save profile action persists those event preferences. Judge
expertise and mentor information are read from their existing models for the owner,
scoped to current memberships. They are never automatically published as identity.
Portfolio/submission/award history retains its existing workspace-authorized API.

All six authenticated roles have an account/profile destination. Optional profile
content loads on first visit and retains drafts afterwards. Shared Avatar, PersonRow,
IdentityCard, ProfileHeader and tags are used in profiles, roster and judge directory/
marketplace views. Image failures retain deterministic initials. Public profile links
use the same privacy checks and reveal no assignments, ballots or private history.

User profiles are global account data and stay with existing identities during
final-archive imports; event archives do not clone accounts or their privacy choices.
Normal database backups include profiles. Demo enrichment affects only marked
synthetic accounts and uses explicit public participant/member staff identities.
