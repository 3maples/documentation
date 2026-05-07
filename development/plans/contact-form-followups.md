# Contact Form & reCAPTCHA — Follow-ups

Source: `/code-review` of the contact-form expansion + reCAPTCHA v3 integration on the marketing site (May 2026).

The two security-flavored fixes (emulator gate, structured email addresses) and a vitest unit suite for `verifyRecaptcha` shipped with the original change. The items below are deferred housekeeping. Pick them up in order of severity.

---

## HIGH — Refactor the `contact` request handler

**Where:** `website/functions/index.js` — the `onRequest` callback, ~160 lines.

**Why:** The handler does payload parsing, four separate validation guards, revenue allowlist, captcha verification, transporter setup, email composition, and error handling all inline. Past the 50-line guideline; testing each branch in isolation requires the whole HTTP shell.

**Suggested shape:**
- `validateContactPayload(body)` → returns `{ ok: true, payload }` or `{ ok: false, status, error }`. Pure function, easy to unit-test.
- `runRecaptchaCheck(req, secret, isEmulator)` → already partly extracted via `lib/recaptcha.js`; pull the request-shaped wrapper (token reading, response decision) into a helper that returns the same `{ ok, status, error }` shape.
- `buildEmail({ details, message, fullName, supportEmail })` → returns the nodemailer `sendMail` payload. No I/O.
- `sendContactEmail(payload, smtpAuth)` → wraps `nodemailer.createTransport` + `sendMail`. The only I/O helper.

The handler then becomes:
```js
const validated = validateContactPayload(req.body);
if (!validated.ok) return res.status(validated.status).json({ error: validated.error });

const captcha = await runRecaptchaCheck(req, RECAPTCHA_V3_SECRET.value(), !!process.env.FUNCTIONS_EMULATOR);
if (!captcha.ok) return res.status(captcha.status).json({ error: captcha.error });

try {
  await sendContactEmail(buildEmail(validated.payload), { user: BREVO_SMTP_USER.value(), pass: BREVO_SMTP_PASS.value() });
  res.status(200).json({ ok: true });
} catch (err) { ... }
```

Once these helpers exist, write integration-style tests for the handler with a fetch mock (or `supertest` against the exported function — Cloud Functions v2 onRequest is a plain Express handler).

---

## HIGH — Frontend test for `resolveRecaptchaSiteKey` blocked by current architecture

**Where:** `website/public/contact-modal.js`.

**Why blocked:** `contact-modal.js` lives in `public/` and is served verbatim by Vite/Hosting. It's wrapped in an IIFE (no exports), so its helpers can't be imported by vitest. To test `resolveRecaptchaSiteKey` (the Vite-substitution-detection logic), the file needs to become a proper Vite/Rollup entry — same pattern as `widget/index.tsx` / `maple-widget.js`.

**Suggested move:**
1. Create `website/contact-modal/index.ts` (or `.js`) with the modal logic, exporting helpers like `resolveRecaptchaSiteKey` for tests.
2. Add the entry to `vite.config.ts` `rollupOptions.input` and `entryFileNames` rules so the build emits `dist/contact-modal.js` at the same path.
3. Drop `website/public/contact-modal.js`.
4. Add `website/contact-modal/__tests__/resolveSiteKey.test.ts` covering: real key → returned, empty → empty string, raw `%VITE_RECAPTCHA_V3_SITE_KEY%` placeholder → empty string.

This refactor also unlocks unit-testing the submit handler, the captcha load promise, and the form validation helper.

---

## MEDIUM — Make `RECAPTCHA_MIN_SCORE` configurable

**Where:** `website/functions/index.js:13`.

**Why:** The 0.5 threshold is hardcoded. Fresh keys with no traffic history routinely score below it (we hit this in dev). Tuning currently requires a code change + redeploy.

**Suggested fix:** Use `defineString('RECAPTCHA_V3_MIN_SCORE', { default: '0.5' })` from `firebase-functions/params`, parse to float at handler start, fall back to 0.5 on `NaN`. Set per-environment via `firebase functions:config` or a runtime param.

---

## MEDIUM — Tighten CORS

**Where:** `website/functions/index.js:26` — currently `cors: true` (wildcard).

**Why:** The contact form is served via Hosting rewrite, so traffic to `/api/contact` is same-origin and doesn't need CORS at all. Wildcard CORS lets any origin POST to the endpoint; reCAPTCHA mitigates abuse but tightening costs nothing.

**Suggested fix:**
```js
cors: [
  'https://3maples.ai',
  'https://www.3maples.ai',
  'https://maples-website-dev.web.app',
  'https://maples-website-dev.firebaseapp.com',
  'http://localhost:5050', // hosting emulator
],
```
Or drop `cors` entirely and rely on same-origin Hosting rewrites for prod traffic; only add CORS when explicit cross-origin support is needed.

---

## MEDIUM — `install()` in `contact-modal.js` is ~120 lines

**Where:** `website/public/contact-modal.js:240-360`.

**Why:** Mixes DOM creation, ref binding, captcha setup, open/close handlers, and submit logic. Hard to follow at a glance.

**Suggested fix:** Split into `renderModal()`, `bindOpenClose(refs)`, `bindSubmit(refs, captcha)`. Cleanest after the file is moved out of `public/` (see HIGH frontend-test follow-up above), since the helpers can then be unit-tested with injected refs.

---

## LOW — Hoist `optionalString` to module scope

**Where:** `website/functions/index.js:77`.

**Why:** Pure helper recreated on every request. Negligible perf cost but belongs at module scope alongside `escapeHtml`.

---

## LOW — Replace placeholder heuristic with explicit equality

**Where:** `website/public/contact-modal.js:5-11` — `resolveRecaptchaSiteKey`.

**Why:** Current check rejects values containing `%` or starting with `VITE_`. Functional but heuristic. An explicit check on the literal placeholder is clearer:
```js
if (!trimmed || trimmed === '%VITE_RECAPTCHA_V3_SITE_KEY%') return '';
return trimmed;
```

---

## LOW — Drop `escapeHtml(label)` on hardcoded labels

**Where:** `website/functions/index.js:183`.

**Why:** `htmlDetails` escapes label values that are all string literals defined two lines above. Defensive but unnecessary; misleads a reader into thinking labels could be untrusted.

**Suggested fix:** Drop the `escapeHtml(label)` call (keep `escapeHtml(value)`). Or move labels to a top-level constant to make their hardcoded nature explicit.
