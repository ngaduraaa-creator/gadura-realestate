# 30-Day Quick-Win Checklist: Dialpad for Gadura Real Estate

**Goal:** 30 highest-ROI actions in the first 30 days
**Time Commitment:** 1-2 hours per day
**Outcome:** Professional phone system capturing leads 24/7 with AI assistance

---

## Week 1: Foundation (Days 1-7)

_Theme: Stop losing leads immediately._

### Day 1: Get Connected

- [ ] **1. Download Dialpad app on iPhone**
  - App Store > Dialpad > Download > Sign in
  - Enable all notifications (calls, texts, voicemail)
  - Set as default business phone app

- [ ] **2. Download Dialpad on laptop/desktop**
  - Mac: dialpad.com/download
  - Sign in with same account
  - Enable desktop notifications

- [ ] **3. Verify your Dialpad number (917) 694-3993 is working**
  - Call from your cell (917) 705-0132
  - Call from the office line (917) 352-0773
  - Confirm calls ring on both phone and desktop

### Day 2: Business Hours and Routing

- [ ] **4. Set business hours**
  - Settings > Business Hours
  - Monday-Saturday: 9:00 AM - 7:00 PM Eastern
  - Sunday: Closed
  - Holiday schedule: Add major holidays (see note below)

- [ ] **5. Configure call routing**
  - During business hours: Ring Dialpad app (all devices) for 15 seconds, then forward to cell (917) 705-0132 for 15 seconds, then voicemail
  - After hours: Route to voicemail (upgrade to AI agent in Week 2)

### Day 3: Voicemail

- [ ] **6. Record business hours voicemail**
  - Use the script from VOICEMAIL-SCRIPTS.md "Business Hours Voicemail"
  - Record in a quiet room, speak clearly and warmly
  - Upload via Settings > Voicemail > Greeting

- [ ] **7. Record after-hours voicemail**
  - Use the script from VOICEMAIL-SCRIPTS.md "After-Hours Voicemail"
  - Upload and set as after-hours greeting

- [ ] **8. Enable voicemail-to-email**
  - Settings > Notifications > Voicemail
  - Send to: nitin@gadurarealestate.com
  - Enable voicemail transcription

### Day 4: Caller ID and Outbound Settings

- [ ] **9. Set outbound caller ID**
  - Settings > Caller ID
  - Display: "Gadura Real Estate" with (917) 694-3993
  - Verify by calling a friend and confirming display

- [ ] **10. Set up SMS on your Dialpad number**
  - Verify SMS is enabled on (917) 694-3993
  - Send a test text to your cell
  - Text from the app, not your personal number, for all business communication

### Day 5: Text-Back Auto-Reply

- [ ] **11. Configure missed call text-back**
  - Settings > Auto-Reply or use automation rule
  - Message:

```
Hi, this is Nitin Gadura from Gadura Real Estate. I missed your call and I'm sorry about that -- I'll get back to you within the hour. Need something right away? Reply to this text! Looking to buy or sell in Queens or Long Island? Browse homes at gadurarealestate.com - Nitin
```

- [ ] **12. Configure after-hours text-back**
  - Message:

```
Hi, this is Nitin from Gadura Real Estate. Our office is currently closed (Mon-Sat, 9 AM-7 PM). I'll return your call first thing tomorrow morning. If it's urgent, reply to this text and I'll respond ASAP. In the meantime, browse homes at gadurarealestate.com - Nitin
```

### Day 6: Contacts Import

- [ ] **13. Import existing contacts into Dialpad**
  - Sync Google Contacts (Settings > Integrations > Google Workspace)
  - Import phone contacts via mobile app
  - Verify key contacts synced: attorneys, mortgage brokers, inspectors, title companies

- [ ] **14. Create contact labels/groups**
  - Buyer Lead
  - Seller Lead
  - Past Client
  - Referral Partner
  - Mortgage Broker
  - Attorney
  - Inspector
  - Title Company

### Day 7: Test Everything

- [ ] **15. Full system test**
  - Call (917) 694-3993 during business hours -- does it ring everywhere?
  - Call after hours -- does voicemail play and text-back send?
  - Send an SMS from Dialpad -- does it deliver?
  - Check voicemail email notification -- does transcription arrive?
  - Call from an unknown number -- does caller ID show correctly on outbound callback?

---

## Week 2: Lead Capture (Days 8-14)

_Theme: Make AI capture and qualify every lead._

### Day 8: AI Transcription and Recaps

- [ ] **16. Enable AI transcription on all calls**
  - Settings > AI > Transcription > Enable
  - Verify transcription quality by reviewing 2-3 call transcripts

- [ ] **17. Enable AI Recaps**
  - Settings > AI > Recaps > Enable
  - Set recap delivery: Email to nitin@gadurarealestate.com after every call
  - Review first 5 recaps for quality and accuracy

### Day 9-10: After-Hours AI Agent

- [ ] **18. Create the after-hours AI agent**
  - Admin > AI Agent > Create New
  - Name: "Gadura Real Estate After-Hours Assistant"
  - Load the full script from AI-AGENT-AFTER-HOURS.md
  - Configure buyer path and seller path

- [ ] **19. Configure AI agent routing**
  - Route all after-hours calls to the AI agent instead of voicemail
  - Set routing: Mon-Sat after 7 PM and all day Sunday > AI Agent
  - Also route when status is "In a Showing" or "DND"

- [ ] **20. Test the AI agent**
  - Call (917) 694-3993 after 7 PM
  - Test buyer path: say "I'm looking to buy a home in Howard Beach"
  - Test seller path: say "I want to sell my house in Ozone Park"
  - Test urgent path: say "I need to speak to someone urgently"
  - Verify lead summary email arrives
  - Verify lead summary SMS arrives

### Day 11-12: Webchat Setup

- [ ] **21. Set up the webchat AI agent**
  - Admin > Webchat > Create Widget
  - Load the script from AI-AGENT-WEBSITE-CHAT.md
  - Configure greeting, proactive messages, and all conversation flows

- [ ] **22. Deploy webchat on gadurarealestate.com**
  - Get the embed code from Dialpad
  - Add to your GitHub Pages site (before closing body tag on all pages)
  - Test on desktop and mobile
  - Verify lead notifications arrive

### Day 13: DND and Status Setup

- [ ] **23. Create "In a Showing" status**
  - Set up Do Not Disturb profiles:
  - "In a Showing" (2 hours) -- routes to AI agent
  - "In a Closing" (4 hours) -- routes to AI agent
  - "Day Off" (full day) -- routes to AI agent
  - Test: activate "In a Showing" and call to verify AI agent answers

### Day 14: Week 2 Review

- [ ] **24. Review first week of AI data**
  - Count: How many calls did AI transcribe?
  - Count: How many after-hours leads did AI agent capture?
  - Count: How many webchat conversations happened?
  - Review: Are AI recaps accurate and useful?
  - Fix: Any issues with routing, scripts, or notifications?

---

## Week 3: Optimization (Days 15-21)

_Theme: Get smarter with every call._

### Day 15-16: AI Playbooks

- [ ] **25. Create the Buyer Lead playbook**
  - Admin > AI > Playbooks > Create
  - Load from AI-PLAYBOOK-BUYER-LEAD.md
  - Set trigger words: "buy," "looking for," "house," "apartment," "home," "condo," "property"
  - Test by making a practice call and verifying prompts appear

- [ ] **26. Create the Seller Lead playbook**
  - Admin > AI > Playbooks > Create
  - Load from AI-PLAYBOOK-SELLER-LEAD.md
  - Set trigger words: "sell," "list," "listing," "moving," "value," "worth"
  - Test by making a practice call and verifying prompts appear

### Day 17: Custom Moments

- [ ] **27. Set up Custom Moments**
  - Create these tracked moments:
  - "Pre-Approved" -- triggers on "pre-approved," "pre-approval," "approved for"
  - "First-Time Buyer" -- triggers on "first time," "never bought," "first home"
  - "Timeline Urgent" -- triggers on "ASAP," "this month," "lease ending," "need to move"
  - "Commission Question" -- triggers on "commission," "your fee," "how much do you charge"
  - "Zillow Mention" -- triggers on "Zillow," "Zestimate," "online value"
  - "Referral Source" -- triggers on "referred by," "friend told me," "found you on"
  - "Investment Interest" -- triggers on "investment," "rental income," "cash flow"
  - "Two-Family Interest" -- triggers on "two-family," "two family," "duplex"

### Day 18-19: Scorecards

- [ ] **28. Create the call quality scorecard**
  - Admin > AI > Scorecards > Create
  - Load all 10 items from SCORECARD-TEMPLATE.md
  - Set minimum passing score: 7/10
  - Apply to all inbound calls over 60 seconds
  - Run on 5 past calls to calibrate

### Day 20-21: Review and Adjust

- [ ] **29. Mid-month review**
  - Review 10 AI recaps -- are they capturing the right details?
  - Review 5 scorecard results -- are scores reflecting reality?
  - Review AI agent transcripts -- where are callers getting confused?
  - Adjust any scripts, playbook prompts, or moment triggers based on real data
  - Note: What questions are callers asking that you didn't anticipate?

---

## Week 4: Analytics and Refinement (Days 22-30)

_Theme: Measure results and build habits._

### Day 22-24: Analytics Dashboard

- [ ] **30. Set up your analytics dashboard and weekly routine**
  - Admin > Analytics > Dashboard
  - Configure these widgets:
    - Inbound calls per day (chart)
    - Calls answered vs. missed vs. AI agent handled (pie chart)
    - Average call duration (number)
    - After-hours AI agent leads captured (count)
    - Webchat conversations (count)
    - Average scorecard score (number)
    - Top Custom Moments (bar chart)
  - Schedule weekly email digest: Monday 8:00 AM to nitin@gadurarealestate.com
  - Block 30 minutes every Monday morning for analytics review

---

## Holiday Schedule Reference

Add these to your Dialpad business hours as "closed" days:

| Holiday | Date | Voicemail |
|---------|------|-----------|
| New Year's Day | January 1 | Holiday greeting |
| MLK Day | Third Monday, January | Holiday greeting |
| Presidents' Day | Third Monday, February | Holiday greeting |
| Memorial Day | Last Monday, May | Holiday greeting |
| Independence Day | July 4 | Holiday greeting |
| Labor Day | First Monday, September | Holiday greeting |
| Thanksgiving | Fourth Thursday, November | Holiday greeting |
| Day After Thanksgiving | Fourth Friday, November | Holiday greeting |
| Christmas Eve | December 24 | Holiday greeting |
| Christmas Day | December 25 | Holiday greeting |
| New Year's Eve | December 31 | Holiday greeting |

---

## 30-Day Success Metrics

By Day 30, you should have:

| Metric | Target |
|--------|--------|
| Dialpad app on phone and desktop | Done |
| Professional voicemail on all four slots | Done |
| After-hours AI agent live | Done |
| Webchat live on website | Done |
| AI recaps on every call | Done |
| Buyer playbook active | Done |
| Seller playbook active | Done |
| Scorecard grading calls | Done |
| Custom Moments tracking 8+ triggers | Done |
| Analytics dashboard configured | Done |
| Missed call text-back active | Done |
| Contacts organized with labels | Done |
| AI agent leads captured | 10+ |
| Webchat leads captured | 5+ |
| Average scorecard score | 7+/10 |
| Response time to missed calls | Under 30 min |

---

## Quick Reference: Key Settings Locations

| What | Where in Dialpad |
|------|-----------------|
| Business hours | Settings > Business Hours |
| Voicemail greetings | Settings > Voicemail > Greeting |
| Call routing | Settings > Call Routing |
| AI transcription | Settings > AI > Transcription |
| AI Recaps | Settings > AI > Recaps |
| AI Agent | Admin > AI Agent |
| Webchat | Admin > Webchat |
| Playbooks | Admin > AI > Playbooks |
| Scorecards | Admin > AI > Scorecards |
| Custom Moments | Admin > AI > Custom Moments |
| Analytics | Admin > Analytics |
| Caller ID | Settings > Caller ID |
| DND/Status | App > Status menu |
| Contacts | App > Contacts |
| SMS settings | Settings > Messaging |
