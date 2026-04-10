
# Security -- Broad .gitignore Pattern
💡 SUGGESTION The addition of *-key.json to 
.gitignore
 is a good security measure, but it might be overly broad.

Recommendation: Ensure no non-sensitive JSON files match this pattern, or narrow it down to service-account-key*.json specifically if that's the only type of key being used. However, given the context, a broad exclusion is safer than a narrow one.

# WARNING — Silent no-op when update_intent is missing
python
update_intent = resolve_intent("update", domain)
if update_intent:
    intent = update_intent
If 
domain
 exists but has no corresponding update_* intent (e.g. a future read-only domain), the override silently falls through, leaving the incorrect create_* intent. Add a logger.warning(...) here so failures are observable:

python
if update_intent:
    intent = update_intent
else:
    logger.warning("add/set override: no update intent for domain=%s", domain)

# SUGGESTION
Accessibility: 
In FeedbackPanel.tsx, the error message div currently reads error && <div className="text-xs text-red-600">{error}</div>. You should add role="alert" or aria-live="polite" so screen readers instantly announce network errors to visually impaired users instead of requiring them to explore the DOM to find out why the submission failed.

# TEST GAPS (Edge Cases): 
In your backend test_feedback_api.py, all requests inject an X-Test-Email header. However, feedback.py specifically features a defensive branch for missing emails (binding email = "unknown"). You should patch in a test verifying that an authenticated yet anonymous Firebase token (token_email = "") correctly flows into Trello as Unknown User <unknown>.

# AbortController for panel fetches: 
ChangeLogPanel currently uses the isMountedRef + fetchTokenRef race-guard pattern copied from FeedbackPanel. A cleaner AbortController-based approach would require (a) teaching apiRequest in portal/src/api/client.ts to accept a signal, and (b) migrating both ChangeLogPanel and FeedbackPanel together for consistency. Tracking as a standalone refactor.

# Unauthenticated-request test: 
The test suite runs with FIREBASE_AUTH_DISABLED=true, so a GET /change-logs without X-Test-Email wouldn't actually exercise the Firebase verification path. Worth addressing as a shared testing-infra improvement (e.g., a fixture that temporarily re-enables auth, or an explicit test that omits the bypass) rather than a one-off test in this PR.