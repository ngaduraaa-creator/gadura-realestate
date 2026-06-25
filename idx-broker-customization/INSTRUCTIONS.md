# IDX Broker Page Customization — Setup Guide

This makes the listing pages on **homes.gadurarealestate.com** (the IDX Broker
subdomain) match the luxury design on the main site: Nitin's photo, a formatted
phone number, a "Call to Inquire" button, a WhatsApp chat button (web + mobile),
and a cleaner lead form.

> The main site's own property pages (`gadurarealestate.com/homes/...`) are
> already fully redesigned and deployed. This guide is **only** for the IDX
> Broker–hosted pages, which can only be changed from inside the IDX dashboard.

---

## What you'll paste (2 files in this folder)

| File | Goes in IDX Broker |
|------|--------------------|
| `idx-custom.css` | **Designs → Global CSS** (or "Custom CSS") |
| `idx-custom.js`  | **Designs → Custom Initial Output** (wrap in `<script>…</script>`) |

---

## Step 1 — Paste the CSS

1. Log in to **middleware.idxbroker.com**.
2. Go to **Designs** (left menu).
3. Find the **Global CSS** box (some plans call it "Custom CSS" or it lives
   under *Manage Custom Code*).
4. Paste the **entire contents of `idx-custom.css`** and **Save**.

## Step 2 — Paste the JavaScript

1. Still under **Designs**, open **Custom Initial Output**
   (or *Manage Wrappers → Dynamic Wrapper*).
2. Paste this, with the JS from `idx-custom.js` inside:

   ```html
   <script>
   /* …paste the full contents of idx-custom.js here… */
   </script>
   ```
3. **Save.**

## Step 3 — Upload Nitin's photo in IDX Broker (recommended)

The JS injects Nitin's headshot as a fallback, but it's cleaner to set it
natively so it also shows in search results and emails:

1. **Account → Users** (or *Agents*).
2. Open **Nitin Gadura**.
3. Upload `images/nitin-gadura-headshot.jpg` and **Save**.

> While you're there, confirm the phone shows as **(917) 705-0132** and the
> email is **nitin@gadurarealestate.com**.

---

## Verify

Open any listing, e.g.
`https://homes.gadurarealestate.com/idx/details/listing/c056/995909/...`
You should see:

- ✅ Nitin's headshot + name in the contact card
- ✅ Phone shown as **(917) 705-0132**
- ✅ Green **Call Nitin to Inquire** button
- ✅ Green **Chat on WhatsApp** button (opens with the property address pre-typed)
- ✅ Floating WhatsApp bubble, bottom-right
- ✅ Cleaner lead form + navy **Send Message** button

If any piece doesn't pick up the styling, send a screenshot — IDX Broker class
names occasionally differ by plan and the selectors can be tuned.

---

## Notes

- **wa.me links work on both web and mobile**: desktop opens WhatsApp Web,
  phones open the WhatsApp app — no separate links needed.
- The JS is **idempotent** (safe to run repeatedly) and re-applies itself when
  IDX swaps in new listing content.
- These files are version-controlled in the repo for reference; pasting them
  into the IDX dashboard is what makes them live (IDX pages aren't in our repo).
