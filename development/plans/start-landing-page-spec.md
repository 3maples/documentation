# 3Maples `/start` Landing Page: Build Spec

**For:** Verdeck (and whichever coding agent builds this)
**From:** Ron St.Pierre, Fractional CMO
**Date:** September 2, 2026
**Status:** Design and copy are final. Build to this spec exactly.

---

## 1. What this is

A single, fast, mobile-first landing page at `https://3maples.com/start`. It is the destination for
paid search and paid social traffic. Its only job is to capture an email address and hand the visitor
to signup with that address already filled in.

Every design value in this document was read directly off the live 3Maples site
(`maples-website.web.app`, the Firebase origin behind `3maples.com`) on September 1 2026 using computed
styles and `cssRules`. Nothing here is invented. The page must be visually indistinguishable from the
rest of the site.

---

## 2. Non-negotiables

These are not preferences. Each one exists because of a measured failure.

| # | Requirement | Why |
|---|---|---|
| 1 | Serve at `3maples.com/start`, **same origin as the marketing site** | The Meta pixel already works on that domain. A separate subdomain or a Vercel host reintroduces the cross-domain hop that is currently losing the funnel |
| 2 | The email form lives **on this page** | The current path sends cold visitors to a different domain to fill four fields and a five-rule password. That path has produced 4 registrations in the pixel's entire history |
| 3 | **No images above the fold.** Hero is type and colour only | 100% of paid traffic arrives on a phone |
| 4 | The redirect to signup must **fail open** | If `/api/lead` errors or is slow, the visitor still reaches signup. Never trade a signup for a lead record |
| 5 | Fire the conversion events listed in section 8 | Two campaigns have already been made unreadable by missing conversion events |
| 6 | Do not add anything from the "banned" list in section 10 | Standing brand rules, one of them tied to an open bug |

---

## 3. Design tokens

Lift these verbatim. **If you are building inside the existing site template, these already exist in the
site stylesheet. Do not redeclare them.**

```css
:root{
  --bg:#ffffff; --bg-2:#f0eef7;
  --surface:#ffffff; --surface-2:#f5f4fa; --surface-3:#e7e8ef;
  --ink:#2a2546; --ink-2:#4a4570; --ink-soft:#7a7696; --muted:#a7a5bd;
  --line:#e8e7ef; --line-2:#d6d8e3;
  --accent:#2f9e6b; --danger:#dc4b4b;
}
```

**Note for Ron, not for the build:** the live site's accent is `#2f9e6b`, while brand guide v1.1 and all
composed ad creative use `#159652`. This spec uses the live site value so the page matches its
surroundings. That discrepancy needs resolving separately; do not resolve it in this build.

### Type

Plus Jakarta Sans, weights 400 / 500 / 600 / 700 / 800.
Fallback stack, exactly as the site uses it:

```css
font-family:"Plus Jakarta Sans",ui-sans-serif,system-ui,-apple-system,Helvetica,Arial,sans-serif;
```

| Element | Size | Line height | Letter spacing | Weight |
|---|---|---|---|---|
| `body` | 16px | 1.55 | normal | 400 |
| `h1` | `clamp(42px,6vw,82px)` | 1.02 | -.035em | 700 |
| `h2` | `clamp(32px,4vw,56px)` | 1.05 | -.025em | 700 |
| `h3` | 22px | 1.2 | -.02em | 700 |
| `.lead` | `clamp(17px,1.3vw,20px)` | 1.55 | normal | 400, colour `--ink-2` |
| `.eyebrow` | 12px | normal | .16em, uppercase | 600, colour `--accent` |
| `.btn` | 14.5px | 1 | normal | 600 |

### Layout

`.wrap` is `max-width:1240px; margin:0 auto; padding:0 28px`, and at `max-width:720px` the padding
drops to `0 20px`. Site breakpoints in use: 560, 720, 820, 900, 1100px.

`.btn` is `background:var(--accent); color:#fff; border-radius:10px; padding:12px 20px; border:0`.

---

## 4. Which build to do

**Option A, preferred: integrate into the existing site template.**
Use the markup in section 6 minus its nav, add only the supplemental CSS in section 7, and let the page
inherit the site's existing tokens, `.wrap`, headings, `.lead`, `.eyebrow` and `.btn`. The site is
hand-written CSS with semantic classes, not Tailwind, so this works cleanly.

**Option B: standalone page.** Use the complete file in section 9 as-is. It repeats the tokens inline so
it renders correctly with no dependency on the site stylesheet. 5.7KB gzipped.

Do one or the other. Do not mix them.

---

## 5. Copy

All copy below is final and has been checked against the brand rules. Do not rewrite it, do not "improve"
it, and do not let a model regenerate it.

The `h1` swaps based on the `utm_content` query parameter so the headline matches the ad or keyword that
was clicked. Nine variants, listed in the script. Unknown or missing values fall through to the default,
"Stop building estimates at midnight." The swap runs inline immediately after the `h1` so there is no
flash and no layout shift.

---

## 6. Markup fragment (Option A)

Drop this inside the existing template, below the site nav.

```html
<!-- =============================================================
     3Maples /start  -  MARKUP FRAGMENT
     Drop inside the existing site template, below the site nav.
     Uses the site's own classes: .wrap .btn .eyebrow .lead h1 h2 h3
     Needs start-embed.css appended to the site stylesheet.
     Needs the form script from start.html (the block that fires
     Lead / generate_lead and redirects to app.3maples.ai/signup).
     ============================================================= -->

<!-- ============ HERO ============ -->
<section class="hero"><div class="wrap"><div class="hero-grid">
  <div>
    <p class="eyebrow">Free to start</p>
    <h1 id="hl">Stop building estimates at <span class="hl">midnight</span>.</h1>
    <script>
    /* Message match. Swaps the headline to the ad or keyword that was clicked.
       Runs before the rest of the page paints, so no flash and no layout shift.
       Unknown values fall through to the default above. */
    (function(){
      var v=(new URLSearchParams(location.search).get('utm_content')||'').toLowerCase();
      var m={
        'task-id':'Your tasks have <span class="hl">names</span> now.',
        'second-shift':'Your night shift <span class="hl">ends tonight</span>.',
        'you-talk':'You talk. <span class="hl">Maple works</span>.',
        'note-400':'That note on your dash is worth <span class="hl">$400</span>.',
        'anti-software':'No demo. No salesperson. <span class="hl">No contract</span>.',
        'fastest-estimate':'The <span class="hl">fastest estimate</span> wins.',
        'search-estimating':'Landscaping estimating that <span class="hl">builds itself</span>.',
        'search-free':'Free landscaping estimates. <span class="hl">No card</span>.',
        'search-app':'Build the estimate <span class="hl">from the truck</span>.'
      };
      if(m[v]){document.getElementById('hl').innerHTML=m[v];}
    })();
    </script>
    <p class="lead">Talk through the job the way you'd explain it to the customer. Maple builds the estimate before you're out of the driveway.</p>

    <form class="signup" id="f" novalidate>
      <label class="sr" for="e">Your email</label>
      <input type="email" id="e" name="email" placeholder="you@yourcompany.com" autocomplete="email" inputmode="email" required>
      <button type="submit" class="btn">Start free</button>
    </form>
    <p class="err" id="er">Enter a valid email address.</p>
    <p class="terms">3 users. 20 estimates a month. 50 tasks. No credit card, no contract.</p>
  </div>

  <div class="card">
    <p class="eyebrow">What you get, free</p>
    <div class="row"><span class="tick">&#10003;</span><p><strong>3 users.</strong> You and two crew leads.</p></div>
    <div class="row"><span class="tick">&#10003;</span><p><strong>20 estimates a month.</strong> Most solo operators never hit it.</p></div>
    <div class="row"><span class="tick">&#10003;</span><p><strong>50 tasks.</strong> Every one gets an ID so nothing gets lost.</p></div>
    <div class="row"><span class="tick">&#10003;</span><p><strong>No credit card.</strong> No trial clock. No contract.</p></div>
  </div>
</div></div></section>

<!-- ============ HOW IT WORKS ============ -->
<section class="section"><div class="wrap">
  <div class="section-head">
    <p class="eyebrow">How it works</p>
    <h2>Three steps, and you're <span class="hl">done</span>.</h2>
  </div>
  <div class="steps">
    <div class="step"><div class="num">1</div><h3>You talk it out</h3>
      <p>Walk the property and say what the job needs. Out loud, in plain words, the way you already describe it to a customer.</p></div>
    <div class="step"><div class="num">2</div><h3>Maple builds the estimate</h3>
      <p>Line items, quantities, your rates. Structured, not a wall of notes you retype at the kitchen table.</p></div>
    <div class="step"><div class="num">3</div><h3>You review and adjust</h3>
      <p>Change anything by telling it what to change. Every task gets an ID, so nothing gets lost between the truck and the office.</p></div>
  </div>
</div></section>

<!-- ============ FREE MEANS FREE ============ -->
<section class="section section-alt"><div class="wrap">
  <div class="section-head">
    <p class="eyebrow">No catch</p>
    <h2>Free means <span class="hl">free</span>.</h2>
    <p class="lead">Not a trial. Not a countdown. There is a paid plan if you outgrow this one, and until then nobody will call you about it.</p>
  </div>
  <div class="free-list">
    <div><span class="tick">&#10003;</span><span>3 users, 20 estimates a month, 50 tasks</span></div>
    <div><span class="tick">&#10003;</span><span>No credit card at signup</span></div>
    <div><span class="tick">&#10003;</span><span>No contract and no minimum term</span></div>
    <div><span class="tick">&#10003;</span><span>No demo required to get in</span></div>
  </div>
</div></section>

<!-- ============ OBJECTION ============ -->
<section class="section"><div class="wrap">
  <div class="section-head">
    <h2>No demo. No salesperson. <span class="hl">No contract</span>.</h2>
    <p class="lead">Make an account and build a real estimate in the same sitting. If it isn't faster than how you do it now, close the tab and you're out nothing.</p>
  </div>
</div></section>

<!-- ============ FAQ ============ -->
<section class="section section-alt"><div class="wrap">
  <div class="section-head">
    <p class="eyebrow">Straight answers</p>
    <h2>Questions people actually ask.</h2>
  </div>
  <div class="faq">
    <details open><summary>Is it really free?</summary>
      <p>Yes. Three users, twenty estimates a month, fifty tasks, no credit card and no contract. There is no trial clock counting down.</p></details>
    <details><summary>Do I need to be good with computers?</summary>
      <p>No. You talk, it types. If you can explain a job to a customer, you can build an estimate.</p></details>
    <details><summary>Is this built for landscaping or is it construction software?</summary>
      <p>Landscaping. Most estimating tools in this category are construction takeoff software with a landscaping page bolted on. This was built for crews.</p></details>
    <details><summary>How long does it take to get started?</summary>
      <p>About a minute to make an account. Your first estimate takes a few minutes after that.</p></details>
  </div>
</div></section>

<!-- ============ CLOSE ============ -->
<section class="section" id="start"><div class="wrap">
  <div class="section-head">
    <h2>Quote the next job <span class="hl">from the truck</span>.</h2>
    <p class="lead">Free to start. Takes about a minute.</p>
  </div>
  <form class="signup" id="f2" novalidate>
    <label class="sr" for="e2">Your email</label>
    <input type="email" id="e2" name="email" placeholder="you@yourcompany.com" autocomplete="email" inputmode="email" required>
    <button type="submit" class="btn">Start free</button>
  </form>
  <p class="terms">3 users. 20 estimates a month. 50 tasks. No credit card, no contract.</p>
</div></section>


```

---

## 7. Supplemental CSS (Option A)

Append to the existing site stylesheet. This defines only classes the site does not already have.

```css
/* =============================================================
   3Maples /start  -  SUPPLEMENTAL CSS ONLY
   Append to the existing site stylesheet. Everything else on the
   page (:root tokens, .wrap, h1/h2/h3, .lead, .eyebrow, .btn)
   already exists on the site and is deliberately NOT redefined here.
   ============================================================= */

.hl{color:var(--accent)}

/* ---------- form ---------- */
.signup{display:flex;flex-direction:column;gap:10px;max-width:460px}
label.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
.signup input{font-family:var(--font);font-size:16px;color:var(--ink);height:52px;padding:0 16px;
  border:1px solid var(--line-2);border-radius:10px;background:var(--surface);width:100%}
.signup input::placeholder{color:var(--muted)}
.signup input:focus{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px rgba(47,158,107,.15)}
.signup .btn{height:52px}
.terms{font-size:13.5px;color:var(--ink-soft);margin-top:12px}
.err{font-size:13.5px;color:var(--danger);display:none;margin-top:-2px}
@media(min-width:560px){
  .signup{flex-direction:row}
  .signup input{flex:1}
  .signup .btn{flex:0 0 auto;padding:0 26px}
}

/* ---------- proof card ---------- */
.card{background:var(--surface-2);border:1px solid var(--line);border-radius:16px;padding:26px}
.card .eyebrow{margin-bottom:12px}
.card p{color:var(--ink-2);font-size:16px}
.card .row{display:flex;gap:10px;align-items:flex-start;padding:10px 0;border-top:1px solid var(--line)}
.card .row:first-of-type{border-top:0}
.tick{flex:0 0 auto;color:var(--accent);font-weight:700}

/* ---------- sections ---------- */
.section{padding:64px 0}
.section-alt{background:var(--bg-2)}
.section-head{max-width:34ch;margin-bottom:36px}
.section-head h2{margin-bottom:12px}

.steps{display:grid;grid-template-columns:1fr;gap:26px}
@media(min-width:820px){.steps{grid-template-columns:repeat(3,1fr);gap:34px}}
.step .num{width:34px;height:34px;border-radius:50%;background:var(--surface-3);color:var(--ink);
  font-weight:700;font-size:15px;display:flex;align-items:center;justify-content:center;margin-bottom:14px}
.step h3{margin-bottom:6px}
.step p{color:var(--ink-2)}

.free-list{display:grid;grid-template-columns:1fr;gap:14px;margin-top:8px}
@media(min-width:720px){.free-list{grid-template-columns:1fr 1fr}}
.free-list div{display:flex;gap:10px;align-items:flex-start;color:var(--ink-2)}

.faq{border-top:1px solid var(--line)}
.faq details{border-bottom:1px solid var(--line);padding:18px 0}
.faq summary{font-weight:700;font-size:18px;letter-spacing:-.01em;cursor:pointer;list-style:none}
.faq summary::-webkit-details-marker{display:none}
.faq summary::after{content:"+";float:right;color:var(--accent);font-weight:700}
.faq details[open] summary::after{content:"\2013"}
.faq p{color:var(--ink-2);margin-top:10px;max-width:62ch}

footer{border-top:1px solid var(--line);padding:26px 0 36px;font-size:13.5px;color:var(--ink-soft)}

```

---

## 8. Form behaviour and tracking

Include this script on the page. It is the same in both options.

```html
<script>
/* ------------------------------------------------------------------Lead capture.
   1. Capture the email on 3maples.com, where the pixel demonstrably works.
   2. Fire the Meta Lead event, GA4 generate_lead, and the Google Ads
      conversion. This is the event the campaigns optimize against.
   3. Hand off to app.3maples.ai/signup with email + UTMs preserved.
   The redirect ALWAYS happens, even if the capture endpoint errors.
   We never trade a signup for a lead record.
------------------------------------------------------------------- */
(function(){
  var SIGNUP='https://app.3maples.ai/signup';
  var ENDPOINT='/api/lead';               // Simon: Brevo, list "Leads - Not Signed Up"
  var qs=location.search.slice(1);
  function valid(v){return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v);}
  function go(email){var p=new URLSearchParams(qs);p.set('email',email);location.href=SIGNUP+'?'+p.toString();}
  function handle(form,input,errEl){
    if(!form) return;
    form.addEventListener('submit',function(ev){
      ev.preventDefault();
      var email=input.value.trim();
      if(!valid(email)){ if(errEl) errEl.style.display='block'; input.focus(); return; }
      if(errEl) errEl.style.display='none';
      var btn=form.querySelector('button'); btn.disabled=true; btn.textContent='One second';
      try{ if(window.fbq) fbq('track','Lead'); }catch(e){}
      try{ if(window.gtag) gtag('event','generate_lead',{method:'landing_page'}); }catch(e){}
      var done=false, finish=function(){ if(!done){done=true;go(email);} };
      setTimeout(finish,1200);
      try{
        fetch(ENDPOINT,{method:'POST',headers:{'Content-Type':'application/json'},
          body:JSON.stringify({email:email,query:qs,page:location.pathname})}).then(finish).catch(finish);
      }catch(e){ finish(); }
    });
  }
  handle(document.getElementById('f'),document.getElementById('e'),document.getElementById('er'));
  handle(document.getElementById('f2'),document.getElementById('e2'),null);
})();
</script>
```

### Events that must fire

| Event | Where | Notes |
|---|---|---|
| `PageView` | Meta pixel `1027059673405942` | On load |
| `Lead` | Meta pixel | On valid form submit |
| `generate_lead` | GA4 | On valid form submit |
| Google Ads conversion | Google Ads tag | On valid form submit. Add the tag when the Ads account exists |

GA4: replace `G-XXXXXXX` with the real `maples-ai-prod` measurement ID in both places.

### Backend: `POST /api/lead`

Request body:

```json
{ "email": "string", "query": "raw querystring, no leading ?", "page": "/start" }
```

Behaviour:

- Create or update the contact in Brevo on list **`Leads - Not Signed Up`**.
- Keep the Brevo API key server side. It must never appear in the page.
- Return any 2xx. The client does not read the body.
- **Do not add validation that blocks the response.** The client redirects after 1200ms regardless, by design.

### Redirect contract

On submit, the visitor goes to:

```
https://app.3maples.ai/signup?<original query string>&email=<their email>
```

`app.3maples.ai/signup` must accept `?email=` and prefill the email field. That is a small change on the
app side and it is part of this work.

---

## 9. Complete standalone file (Option B)

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Landscaping estimates, built while you talk | 3Maples</title>
<meta name="description" content="Talk through the job. Maple builds the estimate. Free to start: 3 users, 20 estimates a month, 50 tasks. No credit card, no contract.">
<meta name="robots" content="noindex">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" media="print" onload="this.media='all'">
<noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap"></noscript>
<style>
/* ============================================================
   Tokens lifted verbatim from the live site (maples-website.web.app,
   read Sep 1 2026). Same names, same values, so this page and the
   site cannot drift apart. See start-embed.html for the version that
   inherits the real stylesheet instead of repeating it.
   ============================================================ */
:root{
  --bg:#ffffff; --bg-2:#f0eef7;
  --surface:#ffffff; --surface-2:#f5f4fa; --surface-3:#e7e8ef;
  --ink:#2a2546; --ink-2:#4a4570; --ink-soft:#7a7696; --muted:#a7a5bd;
  --line:#e8e7ef; --line-2:#d6d8e3;
  --accent:#2f9e6b; --danger:#dc4b4b;
  --font:"Plus Jakarta Sans",ui-sans-serif,system-ui,-apple-system,Helvetica,Arial,sans-serif;
}
*{box-sizing:border-box;margin:0;padding:0}
html{-webkit-text-size-adjust:100%}
body{font-family:var(--font);font-size:16px;line-height:1.55;color:var(--ink);background:var(--bg);-webkit-font-smoothing:antialiased}
img{max-width:100%;display:block}

/* site container */
.wrap{max-width:1240px;margin:0 auto;padding:0 28px}
@media(max-width:720px){.wrap{padding:0 20px}}

/* site type scale */
h1{font-size:clamp(42px,6vw,82px);line-height:1.02;letter-spacing:-.035em;font-weight:700}
h2{font-size:clamp(32px,4vw,56px);line-height:1.05;letter-spacing:-.025em;font-weight:700}
h3{font-size:22px;line-height:1.2;letter-spacing:-.02em;font-weight:700}
.lead{font-size:clamp(17px,1.3vw,20px);line-height:1.55;color:var(--ink-2)}
.eyebrow{font-size:12px;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:var(--accent)}
.hl{color:var(--accent)}

/* site button */
.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;
  font-family:var(--font);font-size:14.5px;font-weight:600;line-height:1;
  padding:12px 20px;border-radius:10px;border:0;cursor:pointer;text-decoration:none;
  background:var(--accent);color:#fff}
.btn:hover{background:#2a8f60}
.btn:disabled{opacity:.6;cursor:default}
.btn-lg{font-size:16px;padding:16px 24px}

/* ---------- nav ---------- */
.nav{border-bottom:1px solid var(--line)}
.nav .wrap{display:flex;align-items:center;justify-content:space-between;height:72px}
.brand{display:flex;align-items:center;gap:10px;font-weight:800;font-size:20px;letter-spacing:-.02em;color:var(--ink);text-decoration:none}
.brand img{height:26px;width:auto}

/* ---------- hero ---------- */
.hero{padding:56px 0 64px}
.hero .eyebrow{margin-bottom:14px}
.hero h1{margin-bottom:16px;max-width:17ch}
.hero .lead{margin-bottom:26px;max-width:44ch}
.hero-grid{display:grid;grid-template-columns:1fr;gap:0}
@media(min-width:960px){
  .hero{padding:76px 0 88px}
  .hero-grid{grid-template-columns:1.05fr .95fr;gap:56px;align-items:center}
}

/* ---------- form ---------- */
.signup{display:flex;flex-direction:column;gap:10px;max-width:460px}
label.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
.signup input{font-family:var(--font);font-size:16px;color:var(--ink);height:52px;padding:0 16px;
  border:1px solid var(--line-2);border-radius:10px;background:var(--surface);width:100%}
.signup input::placeholder{color:var(--muted)}
.signup input:focus{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px rgba(47,158,107,.15)}
.signup .btn{height:52px}
.terms{font-size:13.5px;color:var(--ink-soft);margin-top:12px}
.err{font-size:13.5px;color:var(--danger);display:none;margin-top:-2px}
@media(min-width:560px){
  .signup{flex-direction:row}
  .signup input{flex:1}
  .signup .btn{flex:0 0 auto;padding:0 26px}
}

/* ---------- proof card ---------- */
.card{background:var(--surface-2);border:1px solid var(--line);border-radius:16px;padding:26px}
.card .eyebrow{margin-bottom:12px}
.card p{color:var(--ink-2);font-size:16px}
.card .row{display:flex;gap:10px;align-items:flex-start;padding:10px 0;border-top:1px solid var(--line)}
.card .row:first-of-type{border-top:0}
.tick{flex:0 0 auto;color:var(--accent);font-weight:700}

/* ---------- sections ---------- */
.section{padding:64px 0}
.section-alt{background:var(--bg-2)}
.section-head{max-width:34ch;margin-bottom:36px}
.section-head h2{margin-bottom:12px}

.steps{display:grid;grid-template-columns:1fr;gap:26px}
@media(min-width:820px){.steps{grid-template-columns:repeat(3,1fr);gap:34px}}
.step .num{width:34px;height:34px;border-radius:50%;background:var(--surface-3);color:var(--ink);
  font-weight:700;font-size:15px;display:flex;align-items:center;justify-content:center;margin-bottom:14px}
.step h3{margin-bottom:6px}
.step p{color:var(--ink-2)}

.free-list{display:grid;grid-template-columns:1fr;gap:14px;margin-top:8px}
@media(min-width:720px){.free-list{grid-template-columns:1fr 1fr}}
.free-list div{display:flex;gap:10px;align-items:flex-start;color:var(--ink-2)}

.faq{border-top:1px solid var(--line)}
.faq details{border-bottom:1px solid var(--line);padding:18px 0}
.faq summary{font-weight:700;font-size:18px;letter-spacing:-.01em;cursor:pointer;list-style:none}
.faq summary::-webkit-details-marker{display:none}
.faq summary::after{content:"+";float:right;color:var(--accent);font-weight:700}
.faq details[open] summary::after{content:"\2013"}
.faq p{color:var(--ink-2);margin-top:10px;max-width:62ch}

footer{border-top:1px solid var(--line);padding:26px 0 36px;font-size:13.5px;color:var(--ink-soft)}
</style>
</head>
<body>

<!-- ============ NAV ============ -->
<div class="nav"><div class="wrap">
  <a class="brand" href="/"><img src="/assets/3maples-logo-horizontal.png" alt="" width="26" height="26">3Maples</a>
  <a class="btn" href="#start">Start free</a>
</div></div>

<!-- ============ HERO ============ -->
<section class="hero"><div class="wrap"><div class="hero-grid">
  <div>
    <p class="eyebrow">Free to start</p>
    <h1 id="hl">Stop building estimates at <span class="hl">midnight</span>.</h1>
    <script>
    /* Message match. Swaps the headline to the ad or keyword that was clicked.
       Runs before the rest of the page paints, so no flash and no layout shift.
       Unknown values fall through to the default above. */
    (function(){
      var v=(new URLSearchParams(location.search).get('utm_content')||'').toLowerCase();
      var m={
        'task-id':'Your tasks have <span class="hl">names</span> now.',
        'second-shift':'Your night shift <span class="hl">ends tonight</span>.',
        'you-talk':'You talk. <span class="hl">Maple works</span>.',
        'note-400':'That note on your dash is worth <span class="hl">$400</span>.',
        'anti-software':'No demo. No salesperson. <span class="hl">No contract</span>.',
        'fastest-estimate':'The <span class="hl">fastest estimate</span> wins.',
        'search-estimating':'Landscaping estimating that <span class="hl">builds itself</span>.',
        'search-free':'Free landscaping estimates. <span class="hl">No card</span>.',
        'search-app':'Build the estimate <span class="hl">from the truck</span>.'
      };
      if(m[v]){document.getElementById('hl').innerHTML=m[v];}
    })();
    </script>
    <p class="lead">Talk through the job the way you'd explain it to the customer. Maple builds the estimate before you're out of the driveway.</p>

    <form class="signup" id="f" novalidate>
      <label class="sr" for="e">Your email</label>
      <input type="email" id="e" name="email" placeholder="you@yourcompany.com" autocomplete="email" inputmode="email" required>
      <button type="submit" class="btn">Start free</button>
    </form>
    <p class="err" id="er">Enter a valid email address.</p>
    <p class="terms">3 users. 20 estimates a month. 50 tasks. No credit card, no contract.</p>
  </div>

  <div class="card">
    <p class="eyebrow">What you get, free</p>
    <div class="row"><span class="tick">&#10003;</span><p><strong>3 users.</strong> You and two crew leads.</p></div>
    <div class="row"><span class="tick">&#10003;</span><p><strong>20 estimates a month.</strong> Most solo operators never hit it.</p></div>
    <div class="row"><span class="tick">&#10003;</span><p><strong>50 tasks.</strong> Every one gets an ID so nothing gets lost.</p></div>
    <div class="row"><span class="tick">&#10003;</span><p><strong>No credit card.</strong> No trial clock. No contract.</p></div>
  </div>
</div></div></section>

<!-- ============ HOW IT WORKS ============ -->
<section class="section"><div class="wrap">
  <div class="section-head">
    <p class="eyebrow">How it works</p>
    <h2>Three steps, and you're <span class="hl">done</span>.</h2>
  </div>
  <div class="steps">
    <div class="step"><div class="num">1</div><h3>You talk it out</h3>
      <p>Walk the property and say what the job needs. Out loud, in plain words, the way you already describe it to a customer.</p></div>
    <div class="step"><div class="num">2</div><h3>Maple builds the estimate</h3>
      <p>Line items, quantities, your rates. Structured, not a wall of notes you retype at the kitchen table.</p></div>
    <div class="step"><div class="num">3</div><h3>You review and adjust</h3>
      <p>Change anything by telling it what to change. Every task gets an ID, so nothing gets lost between the truck and the office.</p></div>
  </div>
</div></section>

<!-- ============ FREE MEANS FREE ============ -->
<section class="section section-alt"><div class="wrap">
  <div class="section-head">
    <p class="eyebrow">No catch</p>
    <h2>Free means <span class="hl">free</span>.</h2>
    <p class="lead">Not a trial. Not a countdown. There is a paid plan if you outgrow this one, and until then nobody will call you about it.</p>
  </div>
  <div class="free-list">
    <div><span class="tick">&#10003;</span><span>3 users, 20 estimates a month, 50 tasks</span></div>
    <div><span class="tick">&#10003;</span><span>No credit card at signup</span></div>
    <div><span class="tick">&#10003;</span><span>No contract and no minimum term</span></div>
    <div><span class="tick">&#10003;</span><span>No demo required to get in</span></div>
  </div>
</div></section>

<!-- ============ OBJECTION ============ -->
<section class="section"><div class="wrap">
  <div class="section-head">
    <h2>No demo. No salesperson. <span class="hl">No contract</span>.</h2>
    <p class="lead">Make an account and build a real estimate in the same sitting. If it isn't faster than how you do it now, close the tab and you're out nothing.</p>
  </div>
</div></section>

<!-- ============ FAQ ============ -->
<section class="section section-alt"><div class="wrap">
  <div class="section-head">
    <p class="eyebrow">Straight answers</p>
    <h2>Questions people actually ask.</h2>
  </div>
  <div class="faq">
    <details open><summary>Is it really free?</summary>
      <p>Yes. Three users, twenty estimates a month, fifty tasks, no credit card and no contract. There is no trial clock counting down.</p></details>
    <details><summary>Do I need to be good with computers?</summary>
      <p>No. You talk, it types. If you can explain a job to a customer, you can build an estimate.</p></details>
    <details><summary>Is this built for landscaping or is it construction software?</summary>
      <p>Landscaping. Most estimating tools in this category are construction takeoff software with a landscaping page bolted on. This was built for crews.</p></details>
    <details><summary>How long does it take to get started?</summary>
      <p>About a minute to make an account. Your first estimate takes a few minutes after that.</p></details>
  </div>
</div></section>

<!-- ============ CLOSE ============ -->
<section class="section" id="start"><div class="wrap">
  <div class="section-head">
    <h2>Quote the next job <span class="hl">from the truck</span>.</h2>
    <p class="lead">Free to start. Takes about a minute.</p>
  </div>
  <form class="signup" id="f2" novalidate>
    <label class="sr" for="e2">Your email</label>
    <input type="email" id="e2" name="email" placeholder="you@yourcompany.com" autocomplete="email" inputmode="email" required>
    <button type="submit" class="btn">Start free</button>
  </form>
  <p class="terms">3 users. 20 estimates a month. 50 tasks. No credit card, no contract.</p>
</div></section>

<footer><div class="wrap">&copy; 2026 3Maples</div></footer>

<script>
/* ------------------------------------------------------------------
   Lead capture.
   1. Capture the email on 3maples.com, where the pixel demonstrably works.
   2. Fire the Meta Lead event, GA4 generate_lead, and the Google Ads
      conversion. This is the event the campaigns optimize against.
   3. Hand off to app.3maples.ai/signup with email + UTMs preserved.
   The redirect ALWAYS happens, even if the capture endpoint errors.
   We never trade a signup for a lead record.
------------------------------------------------------------------- */
(function(){
  var SIGNUP='https://app.3maples.ai/signup';
  var ENDPOINT='/api/lead';               // Simon: Brevo, list "Leads - Not Signed Up"
  var qs=location.search.slice(1);
  function valid(v){return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v);}
  function go(email){var p=new URLSearchParams(qs);p.set('email',email);location.href=SIGNUP+'?'+p.toString();}
  function handle(form,input,errEl){
    if(!form) return;
    form.addEventListener('submit',function(ev){
      ev.preventDefault();
      var email=input.value.trim();
      if(!valid(email)){ if(errEl) errEl.style.display='block'; input.focus(); return; }
      if(errEl) errEl.style.display='none';
      var btn=form.querySelector('button'); btn.disabled=true; btn.textContent='One second';
      try{ if(window.fbq) fbq('track','Lead'); }catch(e){}
      try{ if(window.gtag) gtag('event','generate_lead',{method:'landing_page'}); }catch(e){}
      var done=false, finish=function(){ if(!done){done=true;go(email);} };
      setTimeout(finish,1200);
      try{
        fetch(ENDPOINT,{method:'POST',headers:{'Content-Type':'application/json'},
          body:JSON.stringify({email:email,query:qs,page:location.pathname})}).then(finish).catch(finish);
      }catch(e){ finish(); }
    });
  }
  handle(document.getElementById('f'),document.getElementById('e'),document.getElementById('er'));
  handle(document.getElementById('f2'),document.getElementById('e2'),null);
})();
</script>

<!-- Meta Pixel 1027059673405942 -->
<script>
!function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?
n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;
n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;
t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,
document,'script','https://connect.facebook.net/en_US/fbevents.js');
fbq('init','1027059673405942');fbq('track','PageView');
</script>
<noscript><img height="1" width="1" style="display:none" alt=""
src="https://www.facebook.com/tr?id=1027059673405942&ev=PageView&noscript=1"></noscript>

<!-- GA4. Simon: replace G-XXXXXXX with the maples-ai-prod measurement ID -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXX"></script>
<script>
window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments)}
gtag('js',new Date());gtag('config','G-XXXXXXX');
</script>

</body>
</html>

```

---

## 10. Do not

- **No margin or markup claims of any kind.** Bug `3M-EST-001` is open.
- **Do not claim estimates send from the app.** That is not built.
- No Spanish exclusivity claims.
- No ROI or "make more money" claim. There is no customer to substantiate one.
- No stock photography of landscapers.
- Real logo files only, never redrawn or AI generated. White lockup on dark grounds, black on light.
- Do not add a cookie banner, chat widget, video embed, carousel, or animation library. Every one of
  those costs load time on a page whose entire purpose is speed.

Free plan facts, to be used verbatim wherever they appear: **3 users, 20 estimates a month, 50 tasks,
no credit card, no contract.**

---

## 11. Assets

| Asset | Path on site | Source |
|---|---|---|
| Logo, horizontal | `/assets/3maples-logo-horizontal.png` | Dropbox `/3 Maples/Brand Assets/3Maples Logos/Logos/`. Use unmodified |
| Plus Jakarta Sans 400/500/600/700/800 | Self-host as woff2 | If the site already self-hosts, reuse it and delete the Google Fonts link and both preconnects from the standalone file |

---

## 12. Acceptance tests

Run every line. Report pass or fail. The page does not receive ad traffic until all of them pass.

| # | Test | Expected |
|---|---|---|
| 1 | PageSpeed Insights, mobile, against the deployed URL | LCP under 2.5s, Total Blocking Time under 200ms. **This is the gate** |
| 2 | Load on a real phone on cellular, not wifi | Headline and email field visible without scrolling |
| 3 | Logo renders | No broken image box |
| 4 | Load with each of the nine `utm_content` values | Headline swaps correctly. No flash, no layout shift |
| 5 | Load with JavaScript disabled | Default headline stands, page readable |
| 6 | Compare side by side with the homepage | Same green, same Ink, same Plus Jakarta Sans, same button radius, same container width |
| 7 | Submit the form, watch Events Manager Test Events | `Lead` received on pixel `1027059673405942` |
| 8 | Submit the form, check Brevo | Contact appears on `Leads - Not Signed Up` |
| 9 | Submit the form, inspect the redirect URL | Lands on `app.3maples.ai/signup` carrying `email` and every `utm_` parameter, and the email field is prefilled |
| 10 | Force `/api/lead` to return 500, submit again | Redirect still happens. The visitor is not lost |
| 11 | Tab through the page with a keyboard | Focus ring visible on both inputs and both buttons |

---

## 13. Questions to send back rather than guess

- Does the site already self-host Plus Jakarta Sans? If yes, use it and drop the Google Fonts link.
- Is there an existing `/api` route pattern to follow, or is `/api/lead` a new endpoint?
- Does `app.3maples.ai/signup` currently ignore unknown query parameters, or will unrecognised UTMs break it?

Do not invent answers to these. Send them back.
