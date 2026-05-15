# Brevo Contact Sync for Get-in-Touch Form

## Goal

When the website "Get in Touch" form is submitted, push the submitter into
Brevo as a contact (and add them to one or more lists) **in addition to**
sending the existing SMTP notification email. Brevo becomes the CRM/lead
store; the SMTP email stays as the immediate notification to support.

## Current state

- Form UI: `website/public/contact-modal.js` collects `firstName`,
  `lastName`, `email`, `message`, `company`, `website`, `mobile`,
  `revenue`, `joinWaitlist`, plus a reCAPTCHA token.
- Endpoint: `/api/contact` → `contact` Firebase Function in
  `website/functions/index.js`.
- Today: validates input, verifies reCAPTCHA, then `nodemailer` sends an
  email to `support@3maples.ai` via `smtp-relay.brevo.com`.
- Secrets in use: `BREVO_SMTP_USER`, `BREVO_SMTP_PASS`,
  `RECAPTCHA_V3_SECRET`.

## What you need to do in Brevo (before deploy)

1. **Create a Brevo API v3 key.**
   Brevo dashboard → *SMTP & API* → *API Keys* → **Generate a new API
   key**. Name it something like `website-contact-sync`. This is a
   *different* credential from the SMTP key already in use — keep both.
   Copy the key once; you won't see it again.

2. **Create the lists you want submissions routed to.**
   Brevo → *Contacts* → *Lists* → *Add a new list*. Recommended:
   - `Website – Contact Form` (everyone who submits the form)
   - `Website – Pre-launch Waitlist` (only when `joinWaitlist === true`)
   Note each list's numeric **ID** (visible in the URL, e.g.
   `/contact/index/list/12` → `12`). We'll need them as config.

3. **Create custom contact attributes** to capture the non-standard
   fields. Brevo → *Contacts* → *Settings* → *Contact attributes* → *Add
   an attribute*. Standard `FIRSTNAME` / `LASTNAME` / `SMS` already
   exist. Add:
   | Name | Type | Source field |
   |---|---|---|
   | `COMPANY` | Text | `company` |
   | `WEBSITE` | Text | `website` |
   | `REVENUE` | Text (or Category, with the same allowed values as in `index.js`) | `revenue` |
   | `MESSAGE` | Text | `message` |
   | `SOURCE` | Text | hardcoded `"website-contact-form"` |
   | `SUBMITTED_AT` | Date | timestamp at request time |

   *Note:* For phone, Brevo's built-in `SMS` attribute expects E.164
   format (`+15551234567`). The form's `mobile` field is free-text, so
   either (a) leave it out of Brevo and keep it in the notification
   email only, or (b) add a `MOBILE` text attribute and store the raw
   string. Recommend (b) to avoid silently dropping invalid numbers.

4. **(Optional) GDPR / consent.**
   If you intend to email these contacts marketing content later, the
   form should carry a consent checkbox. Today it doesn't — the
   `joinWaitlist` checkbox is closest. For now we'll treat submission
   as transactional/CRM intake, not marketing opt-in, and only add to
   the waitlist list when `joinWaitlist` is true.

## What changes in code

### `website/functions/index.js`

1. Define a new secret `BREVO_API_KEY` via `defineSecret(...)` and add
   it to the `secrets` array on `onRequest`.
2. Add two non-secret config constants for the list IDs — keep them
   inline for now (a single source location, easy to grep):
   ```js
   const BREVO_CONTACT_LIST_ID = 0;   // TODO: replace with real id
   const BREVO_WAITLIST_LIST_ID = 0;  // TODO: replace with real id
   ```
   These can graduate to env / `defineString` later if they need to
   differ per environment.
3. After reCAPTCHA passes and before/around the existing `sendMail`
   block, fire a new helper `syncContactToBrevo(...)`:
   - `POST https://api.brevo.com/v3/contacts`
   - Headers: `api-key: <key>`, `accept: application/json`,
     `content-type: application/json`
   - Body:
     ```json
     {
       "email": "<trimmedEmail>",
       "attributes": {
         "FIRSTNAME": "...",
         "LASTNAME": "...",
         "COMPANY": "...",
         "WEBSITE": "...",
         "MOBILE": "...",
         "REVENUE": "...",
         "MESSAGE": "...",
         "SOURCE": "website-contact-form",
         "SUBMITTED_AT": "2026-05-14T12:34:56.000Z"
       },
       "listIds": [<contact-list-id>, <waitlist-list-id-if-opted-in>],
       "updateEnabled": true
     }
     ```
   - `updateEnabled: true` so re-submissions update the existing
     contact instead of 400-ing on duplicate email.
4. **Error policy:** Brevo sync failure must NOT block the email — the
   email is the inbound signal we care about most. Wrap the Brevo call
   in its own try/catch, log on failure with enough context to triage
   (status code + Brevo error body, but **never** log the API key or
   full request headers), and continue. The 200 response to the
   browser is gated on the email send succeeding, same as today.
5. **Concurrency:** Run the Brevo POST and the `transporter.sendMail`
   in parallel with `Promise.allSettled` so we don't serialize two
   network round-trips. Inspect both results, decide the response based
   on email status, log Brevo status separately.
6. Use `fetch` (native in Node 20 Cloud Functions runtime) — no new
   dependency.

### `website/public/contact-modal.js`

No changes required. The function consumes the same payload it does
today.

### Tests

- Add `website/functions/__tests__/brevoContactSync.test.js` (or extend
  an existing test file in `__tests__/`) covering:
  - Happy path: valid form → Brevo `POST /v3/contacts` called once with
    the expected body (attributes, list IDs, `updateEnabled: true`).
  - `joinWaitlist: false` → only the contact list ID is included.
  - `joinWaitlist: true` → both list IDs included.
  - Brevo returns 400/500 → the function still returns `200 { ok: true }`
    to the client (email succeeded) and logs the Brevo failure.
  - Brevo returns 200 but email throws → function returns 500 (same as
    today's behavior).
- Mock `fetch` for Brevo and `nodemailer.createTransport` for email.
- Update any snapshot of the email-only flow that asserts "no other
  network calls were made."

### Documentation

- Update `website/README.md` (or wherever the existing function setup
  notes live) with the new `BREVO_API_KEY` secret and the two list-ID
  constants. Mention that custom attributes must exist in Brevo before
  the first deploy, otherwise they'll be silently dropped.

## Deploy steps (in order)

1. In Brevo: create API key, lists, and custom attributes (above).
2. Wire the secret into Firebase:
   ```bash
   firebase functions:secrets:set BREVO_API_KEY
   # paste the key when prompted
   ```
3. Replace the two `LIST_ID` placeholders in `index.js`.
4. Deploy: `cd website && firebase deploy --only functions:contact`.
5. Smoke test from production form with a throwaway email; verify the
   contact appears in both lists (with `joinWaitlist` ticked) and the
   notification email lands at `support@3maples.ai`.

## Risks / open questions

- **Mobile format mismatch.** Brevo's `SMS` attribute is E.164; the
  form accepts free text. Plan above stores raw in `MOBILE` text attr
  instead of `SMS`, so SMS sends from Brevo won't work until format is
  enforced or normalized. Flag if SMS marketing is on your roadmap.
- **GDPR/CASL consent.** Treating form submission as CRM-only intake
  is fine for transactional follow-up; sending marketing later needs
  an explicit opt-in checkbox. Worth deciding before list grows.
- **No retry on Brevo failure.** A transient Brevo 5xx silently drops
  the contact (we still have the email). If that's not acceptable
  later, options are: (a) Firestore queue + retry, (b) Cloud Tasks. Out
  of scope for this change.
- **No deduplication beyond email.** Brevo keys contacts by email, so
  multiple submissions from the same address will overwrite earlier
  attribute values (notably `MESSAGE` and `SUBMITTED_AT`). The
  notification email preserves the full history.
