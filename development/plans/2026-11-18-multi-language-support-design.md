# Multi-Language Support — Design

Approved by Simon on 2026-11-18. The drawn UI designs (1–7) are on the
published plan page: https://claude.ai/artifact/2fb9m3ZGVGkqffSfPheiQf
(private to Simon). This file is the text of that page, and the build plan
(`2026-11-18-multi-language-support-plan.md`) argues from it.

> **Since the 2026-11-18/19 review fixes,** the code and
> `.claude/rules/translation.md` are the authority on how translation works.
> This design records what was decided; where a detail below differs from the
> rule file, the rule file is right.

Each person can have the text their team writes shown in their own language.
The app itself stays in English, and what the team writes stays exactly as it
was typed. Translation is only what a reader sees on their own screen.

## Where things stand today

- **Maple already translates.** She reads any language and replies in the
  writer's language, using `platform/services/translation.py`. That translator
  keeps markdown, numbers, prices and quoted names intact. Team text uses the
  same provider and worker model, with its own prompt (`services/team_translation.py`).
- **Nothing stores a language.** A user has no language setting. An invitation
  carries an email and a role only.
- **Descriptions are editable fields.** An estimate's and a work item's
  description are always-editable boxes for anyone allowed to edit; there is no
  separate reading view. An estimate's title already shows as text until it is
  clicked.

## Decisions (all settled, 17–18 Nov 2026)

- Auto-translate is off by default. Off means text shows as written.
- When it is on, the person picks their preferred language.
- Auto-translate covers team-written text only. Menus, buttons and labels stay
  in English.
- Text is stored as typed, in whatever language the writer used.
- A translate button gives a one-off translation that is never saved on the
  record and is gone when the page is reloaded or left.
- An invitation carries a starting language, applied when the new member signs
  up.
- Catalog names are left alone.
- Clicking into an editable field shows the saved text.
- Translation counts against the company's credits.
- Auto-translate also translates estimate and task titles. Titles get no
  translate button. (A work item has no title, only a description.)
- The language chip is read-only. Its tooltip says where to change the setting.
- Translation happens on screen (approach C).
- All 22 languages the translator names today are offered.
- Auto-translate is each person's own setting, saved on their account.
- When the included credits are used up, auto-translate pauses. The translate
  button follows Maple's overage rule.
- There is no company-wide switch.
- The User's Guide stops promising a translated app and translated customer
  documents.

## Calls made in the design (Simon did not object)

- Task descriptions count as text content.
- Titles are translated wherever the portal shows them: on the estimate or task
  itself, and in lists, boards and pickers.
- A translated title carries a small icon instead of the full mark. Pointing at
  the icon shows the title as written; on a phone, tapping it on the estimate or
  task itself does.
- English is in the language list, so an English reader can auto-translate a
  teammate's Spanish notes.
- A translation already in the cache costs no credits, so it is still shown
  when the included credits are used up.
- Translated text carries a small mark and a way back to the original.
- The platform keeps each translation, without the original text, so the same
  text is not translated twice. The copy belongs to the company and expires
  after 30 days unused.
- On phones the translate button is always shown and the language list opens as
  a sheet from the bottom.
- The language chip sits at the foot of the sidebar on a computer (which has no
  top bar) and in the top bar on a phone.

## Behaviour

| Situation | What the person sees |
|---|---|
| Auto-translate off (the default) | Text exactly as it was typed. |
| Auto-translate on, Spanish chosen | Estimate and task titles, descriptions and notes written in any other language are translated on screen and marked. Text already in Spanish is left alone. Menus, buttons and labels are still English. |
| Clicking into a title or description to edit it | The translation is swapped for the saved text, with a line saying so ("You're editing the original text, written in English."). Saving never writes a translation over it. |
| Included credits used up | Auto-translate pauses. Translations already made still show; other text shows as written, and the chip's tooltip says translation is paused. The translate button keeps working as paid overage if the company has a card and the person has accepted overage charges; otherwise it says why it can't. |
| Translate button | Works on descriptions, notes and Maple's replies, into any language on the list, whether auto-translate is on or off. Gone on reload or leaving the page. Titles have no translate button. |
| Invited with a language | The new account starts with auto-translate on and that language chosen. An invitation left on English starts with auto-translate off, as today. |

**Translated:** estimate title (auto-translate only), task title (auto-translate
only), estimate description, work item description, notes, task description,
Maple's replies (translate button only).

**Left as it is:** menus, buttons, labels, statuses and app messages; catalog
names (materials, equipment, People roles, units, categories); people and
company names, addresses, emails, phone numbers; amounts, prices, quantities,
estimate and task codes; titles quoted inside other text (notifications, emails,
Maple's replies); documents sent to customers.

## UI (designs on the plan page)

1. **Settings → Account → Preferences.** A Language block joins the existing
   list and saves immediately, like the checkboxes beside it: an
   "Auto-translate" checkbox; when checked, a "Your language" picker. Helper
   copy: "Only changes what you see. What your team writes is saved as written.
   Translating uses your company's credits and sends the text to the AI service
   Maple uses." Off-state copy: "Off. Titles, descriptions and notes show as
   they were written."
2. **An estimate with auto-translate on.** Title, descriptions and notes in the
   reader's language; each translated description/note shows
   "Translated from English · Show original"; the title shows a small icon.
   Show original flips that one block back.
3. **The translate button.** On a computer it appears on hover in the block's
   corner; it opens a language list (search, "Yours", "Recent", "All"). The
   translation replaces the text in place, with a strip
   "Translated from Spanish to English · not saved" and "Show original".
4. **Inviting team members.** The Invite dialog gains a "Preferred language"
   picker (applies to every address in that invitation; default English). Copy:
   "Titles, descriptions and notes will be shown to them in Spanish. They can
   change this in Settings." The invitations list gains a Language column;
   resending keeps it. The invitation email and sign-up page stay English.
5. **Titles and descriptions you can edit.** Not focused: the translation with
   its mark. Focused: the saved text, with the banner above the field.
6. **Titles in lists.** Translated title + small icon; pointing at the icon
   shows "Written as: <original>". Text already in the reader's language has no
   icon.
7. **On a phone.** Nothing depends on hover; tap targets as large as the top
   bar's icon buttons; list rows open when tapped, so a title's icon there is a
   mark only; titles stay one line with the icon outside the ellipsis;
   descriptions and notes wrap with no fixed height; the translate list opens as
   a bottom sheet with search; pickers use the native select; the editing
   banner sits above the field; Maple's replies get a small translate button at
   the end of each reply. The chip shrinks to the globe and a two-letter code;
   tapping it shows the tooltip line.

Chip tooltip: "Auto-translate is on. Change it in Settings → Account →
Preferences."

## Approach

| Approach | Verdict |
|---|---|
| A. Translate the whole page in the browser | Rejected: translates menus, rewrites names and prices, fights the portal's redraws. |
| B. Translate in the API responses | Rejected: every route changes, an edit box would hold the translation and save it over the original, Maple and the customer MCP server read the same routes. |
| **C. Translate on screen (chosen)** | The portal asks one platform translate service for the text it is about to show; the service keeps a cache. The API keeps returning stored words, so nothing can save a translation by accident. One service and one portal component run both the translate button and auto-translate. |

The translator uses the same provider and worker model as Maple's translator
(no new vendor), with its own prompt for team text (`services/team_translation.py`).

## What gets built

### Platform

- `User` gains `auto_translate` (default False) and `preferred_language`
  (default `"en"`). `Invitation` gains `preferred_language`; the create request
  and the invitations list carry it, and a resend keeps it.
- `PUT /users/{id}` and the sign-in reply carry the two user fields. Only the
  person themself can change them; an Owner or Admin editing someone else leaves
  them untouched, and a request that omits them leaves them untouched.
- Accepting an invitation copies its language to a member who is new by state
  (never joined a company, auto-translate off, language English) and turns
  auto-translate on unless the language is English. It never overwrites a
  language an existing user already chose.
- One list of languages (the 22 in `services/languages.LANGUAGES`, two-letter codes), served to
  the portal. Every place a code comes in is checked against it.
- `services/team_translation.py` holds the entry point for team-written text: detects
  each text's language, skips text already in the target, reports the source
  language. One model call per text, a few at a time.
- New `POST /translate`: a batch of texts and a target language in,
  translations out. Fails open: on error the original comes back.
- New company-scoped translation cache collection: translation + SHA-256
  fingerprint of the original (never the original). Expires after 30 days
  unused; removed with the company; registered in `DOCUMENT_MODELS`.
- Credits: answer from the cache first, then check the quota before any model
  call, and record usage under its own feature name. Auto-translate requests
  stop at the included credits; translate-button requests follow Maple's
  overage rule.
- Maple: when auto-translate is on, a new chat or a message with no words to
  read a language from is answered in the preferred language. She still replies
  in whatever language you write in.

### Portal

- A wrapper for text content (mark, translate button, show original), used by
  notes and Maple's messages through the existing safe renderers.
- A wrapper for editable fields: translation drawn over the field while it is
  not focused; the field's value is always the saved text. On estimate, work
  item and task descriptions (with translate button) and estimate and task
  titles (without).
- A lighter wrapper for titles shown as plain text (translation, icon, original
  on hover). No translate button. Estimates table, task board and cards,
  dashboard, pickers, a property's activity.
- A paused state when included credits are used up.
- One batching hook: everything on screen that needs translating goes to
  `/translate` in one request; the original shows until the translation arrives.
- Language block in Preferences, Preferred language in the invite dialog,
  Language column in the invitations list, read-only language chip.
- Every new piece has a phone layout and is checked at phone width.
- No language files and no change to menus, buttons or messages.

### User's Guide (`platform/user_guides/users_guide.md`)

- New section under "Other features": the translate button, auto-translate,
  what is and isn't translated, the clicked-field rule, the language chip, what
  happens when the included credits are used up, and that translated text is
  sent to the AI service Maple uses.
- Section 10's "Multi-language support" entry and section 4's pointer to it are
  rewritten to say what ships and promise nothing further.
- Section 3 names translation among the things that use Maple Credits.
- Section 7 gains the Language block and the Preferred language field.
- Each phase updates the guide for what it ships.

A new `.claude/rules/translation.md` records how translation works once built.

## Security and privacy (requirements, not options)

- **Text is data, never an instruction.** Fence the text with
  `prompts/fencing.py`. Discard a translation (show the original) if its set
  of link URLs differs from the original's or it is far longer than the
  original. The discard is cached as a marker with no text, so auto-translate
  doesn't pay for it again; the Translate button asks again. Tests use notes written as instructions.
- **One text per model call**, so one person's text cannot steer another's
  cached translation.
- **Only the 22 codes are accepted** on the user update, the invitation and the
  translate route; the translator refuses any other value. The portal never
  tells the platform what language a text is written in.
- **The translate route is protected like Maple's routes:**
  `require_authenticated_user`, `assert_user_company_access`,
  `assert_token_quota`, `ensure_llm_context` (own feature name),
  `llm_rate_limiter` per person under a company ceiling. Takes text, not ids.
  Not a customer MCP tool.
- **Size caps:** up to 60 texts per request, 20,000 characters per text,
  60,000 characters per request. Translation runs a few texts at a time.
- **The cache holds no original text.** Key: SHA-256 of the translator
  version + target language + exact text. The company is not in the hash: it
  is a field on the row, and every lookup filters on it. Removed with the company; expiry index registered with the others.
  Neither `/ops` nor the staff analytics server reads it.
- **Deleted text lingers up to 30 days** in the cache (fetchable only by
  someone who already has the exact original).
- **Only you can change your language setting** (self-edit only; omitted fields
  untouched).
- **Translations render through the existing safe renderers** (no raw HTML).
- **More text reaches the AI service** (every title/description/note a reader
  with auto-translate opens). Same provider as Maple; usage records and error
  reports hold no text. Preferences copy and the guide say so. Simon to confirm
  privacy policy section 2 covers it.

## Phases

1. **Translate button (Medium)** — route, cache, credit check, translator entry
   point, every security requirement above that covers them; text wrapper on
   notes and Maple's messages, editable-field wrapper on the three descriptions,
   desktop and phone; guide section for the button. Releasable alone.
2. **Language setting and invitations (Small)** — user and invitation fields,
   validation, self-only edit, Preferences block, invite field, list column,
   accept sets language; guide.
3. **Auto-translate (Medium)** — batching hook, mark, chip; auto-translate
   through both wrappers; title fields; titles in lists; Maple's default reply
   language; guide ("coming next" corrected).

Phases 2 and 3 are released together so the setting never appears before it
does something.

## Limits and risks

- The app stays English (menus, invitation email, sign-up page).
- Credits: each text costs credits the first time per language; a long list
  translates every title on that page once.
- Search and sorting use the stored words.
- Maple uses the stored titles.
- Mixed languages in one record; exports carry the stored words.
- Trade terms: the translator needs a short glossary so cost, price, markup and
  margin each map to one fixed word per language.
- First view of new text takes a moment; the original shows meanwhile.
- Right-to-left languages: each translated block sets its own direction; the
  page does not mirror.
- Translation quality: the mark and one-click original let a reader check.

**Not in this design:** translating the app's own wording, translating what is
stored, customer documents, `/ops`, the customer MCP server's replies, the
public website.
