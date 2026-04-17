# Gadura Real Estate — v2

Volume 2 of the site, running in parallel to v1. Live v1 at `gadurarealestate.com/` is untouched.

## Deployment

Drop the `v2/` folder into the root of your existing hosting. The result:

```
gadurarealestate.com/            ← v1 (untouched, still live)
gadurarealestate.com/v2/          ← v2 (new)
gadurarealestate.com/v2/contact.html
gadurarealestate.com/v2/neighborhoods/ozone-park.html
```

All internal v2 links use absolute paths starting with `/v2/`, so they work regardless of where the folder is served from as long as it lives at `/v2/`.

External links (to `/blog/`, `/reviews.html`, `/privacy-policy.html`, etc.) point back to the existing v1 pages at `gadurarealestate.com/...` — those pages are reused as-is.

## File map

```
v2/
├── index.html                          ← new homepage
├── contact.html                        ← new contact page (bug fixed)
├── neighborhoods/
│   └── ozone-park.html                 ← template for all 8 neighborhoods
├── assets/
│   ├── css/site.css                    ← all styling, one file
│   └── js/site.js                      ← sticky call bar, forms, menu, reveals
└── README.md                           ← this file
```

## Bugs from v1 that are fixed in v2

| Bug | v1 location | v2 fix |
|---|---|---|
| Garbled `'">` rendering above Nitin's name | `contact.html`, `neighborhoods/ozone-park.html` | Rewrote agent cards from scratch |
| Wire-fraud link broken | `neighborhoods/ozone-park.html` points to `/neighborhoods/terms.html#wire-fraud` | Now correctly points to root `/terms.html#wire-fraud` equivalent |
| "Video coming soon" placeholders | Homepage | Removed entirely |
| Empty "Book a Consultation" widget | Homepage | Removed; replaced with direct call/text CTAs |
| Two phone numbers with no hierarchy | Every page | Office `(718) 850-0010` is primary on general/buyer pages; Nitin's direct `(917) 705-0132` is primary on seller/neighborhood pages |

## What's new (the call-generation features)

### 1. Sticky mobile call bar
Every page has a fixed bottom bar on mobile with two big thumb-sized buttons: **Call** and **Text**. Appears after 400px of scroll. Hidden on desktop. This alone typically lifts call volume 15–30% on real estate sites. See `.sticky-call` in CSS and the scroll handler in JS.

### 2. Text-us everywhere
Every `tel:` link has a matching `sms:` link beside it. Younger Queens buyers (and many South Asian clients especially) prefer texting before calling.

### 3. JSON-LD schema
Three schema blocks on the homepage:
- `RealEstateAgent` + `LocalBusiness` graph for the brokerage (with `aggregateRating` pulling in the 4.9★ / 57 reviews)
- Three `Person` schemas for Vinod, Nitin, Gaurav — each with their license number, languages, and direct phone
- The Ozone Park page adds `FAQPage` and `BreadcrumbList` schemas

The FAQ schema in particular can earn rich snippets in Google SERPs (the collapsible question/answer panels directly in search results) — this dramatically raises click-through rate without any extra content.

### 4. Phone-number hierarchy by page intent
- **General, buyer, and info pages** → `(718) 850-0010` (office) is the primary CTA
- **Seller pages, neighborhood pages, valuation pages** → `(917) 705-0132` (Nitin's direct) is primary

The sticky bar adjusts accordingly — on the Ozone Park neighborhood page, the "Call" button goes direct to Nitin.

### 5. Form improvements
- **Email is optional**, not required. Phone is what converts to calls.
- **Honeypot field** (`_gotcha`) blocks bot submissions — unused hidden field; if it's filled, the submission is silently discarded. This is one of the cleanest anti-spam techniques that doesn't hurt UX.
- **Thank-you state** after successful submission shows the phone number prominently: *"Can't wait? Call Nitin now at (917) 705-0132"* — recovers a meaningful % of leads as immediate calls.
- **"We'll call you within 2 hours"** specificity beats vague "We'll be in touch." Every form promises a specific response window.

## Configuring form submissions

All forms POST to Formspree by default. You need to:

1. Sign up at https://formspree.io (free tier gives 50 submissions/month, $10/mo for more)
2. Create a form, copy the form ID (looks like `abcd1234`)
3. Find-and-replace `REPLACE_WITH_YOUR_ID` across all HTML files with your actual ID
4. Also update the `FORM_ENDPOINT` constant in `assets/js/site.js`

Alternative: point forms at **Basin**, **Web3Forms**, **GetForm**, or your own backend. The form markup doesn't care which service — just swap the `action` URL.

### Getting form submissions straight to your phone as a text
- Formspree can forward submissions to an email
- Use **Zapier** or **Make** to connect that email to Twilio, which sends you an SMS
- Or use **CallRail Form Tracking** — it attributes form fills to the page/source and can SMS your agents instantly

This means a seller filling out the Ozone Park valuation form hits your phone as a text within seconds.

## Replicating the neighborhood template

`ozone-park.html` is the master template. To create the other 7:

1. Copy `neighborhoods/ozone-park.html` to e.g. `richmond-hill.html`
2. Update the following (use find-and-replace carefully):
   - Title, meta description, canonical URL
   - Every mention of "Ozone Park" → "Richmond Hill"
   - The four hero stats (median price, days on market, sale/list ratio, dominant stock)
   - The narrative prose — **write it fresh.** Don't just swap names. Google's SpamBrain detects templated content across similar pages (see audit doc).
   - The market data table rows
   - The 6 value factors (location sub-areas, transit lines, schools will differ)
   - The testimonials (use real reviews specific to that neighborhood)
   - The FAQ answers (median price, DOM numbers, etc.)
   - Both JSON-LD schema blocks (FAQ answers + breadcrumb URL)
   - The "Nearby" footer links

**Critical for avoiding spam penalty:** each neighborhood page should feel like it was written by a human who knows that specific neighborhood. Vary subheadings, pull in different local landmarks, use different photo placements if you add images later. Same structure across all 8 is fine; identical prose-structure-with-names-swapped is not.

## What still needs to be built (honest scope note)

v2 covers the three pages that drive calls: homepage, contact, and the flagship neighborhood page. To complete the full site, you (or I) still need:

- `buy.html` — listings search page
- `sell.html` — dedicated seller landing page
- `about.html` — team story, company history
- The other 7 neighborhood pages (replicate the template)
- `blog/` — can stay on v1 for now, or be rebuilt later
- Spanish / Hindi / Bengali language variants (`/es/`, `/hi/`, `/bn/`)
- Map search pages (these pull from MLS, complex)

The current 3 pages are enough to A/B test v2 vs v1 call volume. Drive traffic to `/v2/` via one Google Ads campaign for a week, compare call counts against equivalent traffic to v1.

## Call tracking (do this before launch)

You cannot improve what you cannot measure. Before pointing any traffic at v2, set up dynamic number insertion via **CallRail** or **Nimbata**:

1. Create two tracking numbers — one for each "primary" number role
2. Install their JS snippet in the `<head>` of all v2 pages
3. It will dynamically replace the visible phone numbers with tracked ones based on the source (organic, direct, paid, etc.)
4. **Important:** configure CallRail to NOT touch the phone number inside the JSON-LD schema — those need to stay as the real numbers for Google's understanding. CallRail has a class-based targeting option for this.

Now you can answer: "How many calls did v2 drive this week vs v1? From which pages? From which sources?"

## Spam-safety notes

v2 follows Google's 2024–2026 spam policy guidance closely:
- Zero scraped or syndicated third-party content (no parasite SEO risk)
- All prose is original and locally specific
- No keyword stuffing — the footer has natural neighborhood links, not 50+ zip codes
- Structured data (schema) is accurate and matches visible content (no schema spam)
- No doorway pages — every page serves genuine user intent
- No cloaking — crawlers and users see identical content

The one thing to watch: when you build the other 7 neighborhood pages, **do not** just swap the neighborhood name and numbers. Google's SpamBrain specifically flags templated near-duplicate pages across a site. Each neighborhood deserves its own voice.

## Questions / next steps

Ping Claude for:
- The remaining 7 neighborhood pages (one at a time, written fresh each)
- `buy.html`, `sell.html`, `about.html`
- Translation versions of the homepage
- A/B test setup between v1 and v2
