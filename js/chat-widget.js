/* ============================================================
   GADURA REAL ESTATE — Chat Widget
   Floating WhatsApp + Text chat button
   Agent: Nitin Gadura · (917) 705-0132
   ============================================================ */
(function () {
  'use strict';

  /* ── Config ──────────────────────────────────────────────── */
  var PHONE      = '+19177050132';
  var PHONE_DISP = '(917) 705-0132';
  var WA_MSG     = encodeURIComponent("Hello, I have a question about buying or selling my house.");
  var SMS_MSG    = encodeURIComponent("Hello, I have a question about buying or selling my house.");
  var WA_URL     = 'https://wa.me/' + PHONE.replace('+','') + '?text=' + WA_MSG;
  var SMS_URL    = 'sms:' + PHONE + '?body=' + SMS_MSG;
  var AUTO_OPEN_DELAY = 9000;   // ms — show popup after 9 s
  var SESSION_KEY     = 'gre_chat_dismissed';

  /* ── Inject CSS ──────────────────────────────────────────── */
  var css = [
    /* ── Floating launcher button ── */
    '.gre-chat-launcher{',
    '  position:fixed;bottom:28px;right:24px;z-index:9998;',
    '  width:62px;height:62px;border-radius:50%;border:none;cursor:pointer;',
    '  background:#00A651;box-shadow:0 4px 20px rgba(0,0,0,.28);',
    '  display:flex;align-items:center;justify-content:center;',
    '  transition:transform .2s ease,box-shadow .2s ease;',
    '  outline:none;',
    '}',
    '.gre-chat-launcher:hover{transform:scale(1.08);box-shadow:0 6px 28px rgba(0,166,81,.45);}',
    '.gre-chat-launcher:focus-visible{outline:3px solid #00A651;outline-offset:3px;}',

    /* pulse ring */
    '.gre-chat-launcher::before{',
    '  content:"";position:absolute;inset:-6px;border-radius:50%;',
    '  border:3px solid #00A651;opacity:0;',
    '  animation:gre-pulse 2.4s ease-out infinite;',
    '}',
    '@keyframes gre-pulse{0%{transform:scale(.9);opacity:.7}70%{transform:scale(1.25);opacity:0}100%{opacity:0}}',

    /* notification dot */
    '.gre-chat-badge{',
    '  position:absolute;top:4px;right:4px;',
    '  width:18px;height:18px;border-radius:50%;',
    '  background:#e53e3e;border:2px solid #fff;',
    '  font-size:10px;font-weight:800;color:#fff;',
    '  display:flex;align-items:center;justify-content:center;',
    '  font-family:Arial,sans-serif;line-height:1;',
    '}',

    /* ── Popup card ── */
    '.gre-chat-popup{',
    '  position:fixed;bottom:104px;right:24px;z-index:9999;',
    '  width:320px;max-width:calc(100vw - 32px);',
    '  background:#fff;border-radius:18px;',
    '  box-shadow:0 12px 48px rgba(0,0,0,.22),0 2px 8px rgba(0,0,0,.1);',
    '  overflow:hidden;font-family:"Inter",Arial,sans-serif;',
    '  transform:translateY(16px) scale(.96);opacity:0;',
    '  transition:transform .28s cubic-bezier(.34,1.56,.64,1),opacity .22s ease;',
    '  pointer-events:none;',
    '}',
    '.gre-chat-popup.gre-open{transform:translateY(0) scale(1);opacity:1;pointer-events:auto;}',

    /* header strip */
    '.gre-chat-head{',
    '  background:linear-gradient(135deg,#1B2A6B 0%,#0d1f55 100%);',
    '  padding:16px 18px 14px;display:flex;align-items:center;gap:12px;position:relative;',
    '}',
    '.gre-chat-avatar{',
    '  width:44px;height:44px;border-radius:50%;border:2px solid rgba(255,255,255,.35);',
    '  background:#00A651;flex-shrink:0;display:flex;align-items:center;justify-content:center;',
    '  overflow:hidden;',
    '}',
    '.gre-chat-avatar img{width:100%;height:100%;object-fit:cover;}',
    '.gre-chat-head-info{flex:1;}',
    '.gre-chat-name{color:#fff;font-weight:700;font-size:.92rem;line-height:1.2;}',
    '.gre-chat-status{display:flex;align-items:center;gap:5px;margin-top:3px;}',
    '.gre-status-dot{',
    '  width:8px;height:8px;border-radius:50%;background:#00A651;',
    '  box-shadow:0 0 0 2px rgba(0,166,81,.3);',
    '  animation:gre-blink 1.6s ease-in-out infinite;',
    '}',
    '@keyframes gre-blink{0%,100%{opacity:1}50%{opacity:.4}}',
    '.gre-status-txt{color:rgba(255,255,255,.75);font-size:.75rem;}',
    '.gre-chat-close{',
    '  position:absolute;top:10px;right:12px;',
    '  background:rgba(255,255,255,.15);border:none;cursor:pointer;',
    '  width:26px;height:26px;border-radius:50%;',
    '  color:#fff;font-size:14px;line-height:1;',
    '  display:flex;align-items:center;justify-content:center;',
    '  transition:background .15s;',
    '}',
    '.gre-chat-close:hover{background:rgba(255,255,255,.28);}',

    /* body */
    '.gre-chat-body{padding:18px 18px 0;}',

    /* speech bubble */
    '.gre-chat-bubble{',
    '  background:#f0f4ff;border-radius:4px 16px 16px 16px;',
    '  padding:12px 14px;font-size:.88rem;color:#1a1a2e;line-height:1.55;',
    '  position:relative;margin-bottom:6px;',
    '}',
    '.gre-chat-bubble::before{',
    '  content:"";position:absolute;left:-6px;top:0;',
    '  border-width:0 8px 8px 0;border-style:solid;',
    '  border-color:transparent #f0f4ff transparent transparent;',
    '}',
    '.gre-chat-bubble strong{color:#1B2A6B;}',
    '.gre-chat-time{font-size:.72rem;color:#999;margin-bottom:14px;padding-left:2px;}',

    /* CTA buttons */
    '.gre-chat-actions{display:flex;flex-direction:column;gap:10px;padding:4px 0 16px;}',
    '.gre-cta-btn{',
    '  display:flex;align-items:center;justify-content:center;gap:9px;',
    '  padding:13px 18px;border-radius:10px;border:none;cursor:pointer;',
    '  font-family:inherit;font-weight:700;font-size:.9rem;',
    '  text-decoration:none;transition:filter .15s,transform .1s;',
    '  -webkit-tap-highlight-color:transparent;',
    '}',
    '.gre-cta-btn:hover{filter:brightness(1.08);}',
    '.gre-cta-btn:active{transform:scale(.97);}',
    '.gre-btn-wa{background:#25D366;color:#fff;}',
    '.gre-btn-sms{background:#1B2A6B;color:#fff;}',

    /* footer disclaimer */
    '.gre-chat-disclaimer{',
    '  background:#f8f9fa;border-top:1px solid #eee;',
    '  padding:9px 16px;font-size:.7rem;color:#888;',
    '  text-align:center;line-height:1.5;',
    '}',
    '.gre-chat-disclaimer a{color:#1B2A6B;text-decoration:none;}',

    /* ── Mobile overrides ── */
    '@media(max-width:420px){',
    '  .gre-chat-launcher{bottom:20px;right:16px;width:56px;height:56px;}',
    '  .gre-chat-popup{bottom:90px;right:16px;}',
    '}',
  ].join('\n');

  var styleEl = document.createElement('style');
  styleEl.textContent = css;
  document.head.appendChild(styleEl);

  /* ── Build HTML ──────────────────────────────────────────── */
  var wrapper = document.createElement('div');
  wrapper.innerHTML = [
    /* Popup */
    '<div class="gre-chat-popup" id="greChatPopup" role="dialog" aria-modal="true" aria-label="Chat with a Gadura Real Estate agent">',
    '  <div class="gre-chat-head">',
    '    <div class="gre-chat-avatar">',
    '      <img src="/images/nitin-gadura.jpg" alt="Nitin Gadura" ',
    '           onerror="this.style.display=\'none\';this.parentElement.innerHTML=\'<svg width=24 height=24 viewBox=\\\'0 0 24 24\\\' fill=none stroke=white stroke-width=2><path d=\\\'M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2\\\'/><circle cx=12 cy=7 r=4/></svg>\';">',
    '    </div>',
    '    <div class="gre-chat-head-info">',
    '      <div class="gre-chat-name">Gadura Real Estate</div>',
    '      <div class="gre-chat-status">',
    '        <div class="gre-status-dot" aria-hidden="true"></div>',
    '        <span class="gre-status-txt">Agent available now</span>',
    '      </div>',
    '    </div>',
    '    <button class="gre-chat-close" id="greChatClose" aria-label="Close chat widget">&#10005;</button>',
    '  </div>',
    '  <div class="gre-chat-body">',
    '    <div class="gre-chat-bubble">',
    '      <strong>Thinking of selling your home?</strong><br>',
    '      Chat with a local licensed agent right now — we know your neighborhood and can give you a free home valuation today. 🏡',
    '    </div>',
    '    <div class="gre-chat-time">Typically responds within minutes</div>',
    '    <div class="gre-chat-actions">',
    '      <a href="' + WA_URL + '" target="_blank" rel="noopener noreferrer"',
    '         class="gre-cta-btn gre-btn-wa"',
    '         aria-label="Chat on WhatsApp with Gadura Real Estate agent"',
    '         onclick="greChatTrack(\'whatsapp\')">',
    '        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">',
    '          <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/>',
    '          <path d="M12.004 2C6.477 2 2.004 6.474 2.004 12.001c0 1.777.467 3.448 1.28 4.898L2 22l5.229-1.265A9.946 9.946 0 0012.004 22c5.527 0 10-4.474 10-10.001C22.004 6.474 17.531 2 12.004 2zm0 18.004a8.013 8.013 0 01-4.097-1.129l-.293-.174-3.105.751.781-2.997-.191-.307A7.946 7.946 0 014.003 12c0-4.411 3.592-8.002 8.001-8.002 4.41 0 8.001 3.591 8.001 8.002 0 4.41-3.591 8.004-8.001 8.004z"/>',
    '        </svg>',
    '        Chat on WhatsApp',
    '      </a>',
    '      <a href="' + SMS_URL + '"',
    '         class="gre-cta-btn gre-btn-sms"',
    '         aria-label="Send a text message to Gadura Real Estate agent"',
    '         onclick="greChatTrack(\'sms\')">',
    '        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true">',
    '          <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>',
    '        </svg>',
    '        Send a Text Message',
    '      </a>',
    '    </div>',
    '  </div>',
    '  <div class="gre-chat-disclaimer">',
    '    By messaging us you agree to our <a href="/terms.html#tcpa" target="_blank">Terms</a>.',
    '    Message &amp; data rates may apply. Reply STOP to opt out.',
    '    <br>Agent: Nitin Gadura · ' + PHONE_DISP,
    '  </div>',
    '</div>',

    /* Launcher button */
    '<button class="gre-chat-launcher" id="greChatBtn"',
    '        aria-label="Chat with a Gadura Real Estate agent" aria-expanded="false"',
    '        aria-controls="greChatPopup">',
    '  <span class="gre-chat-badge" aria-hidden="true">1</span>',
    '  <svg id="greChatIconOpen" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.2" aria-hidden="true">',
    '    <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>',
    '  </svg>',
    '  <svg id="greChatIconClose" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.5" style="display:none" aria-hidden="true">',
    '    <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>',
    '  </svg>',
    '</button>',
  ].join('\n');

  document.body.appendChild(wrapper);

  /* ── State & refs ─────────────────────────────────────────── */
  var popup    = document.getElementById('greChatPopup');
  var btn      = document.getElementById('greChatBtn');
  var closeBtn = document.getElementById('greChatClose');
  var iconOpen  = document.getElementById('greChatIconOpen');
  var iconClose = document.getElementById('greChatIconClose');
  var badge    = btn.querySelector('.gre-chat-badge');
  var isOpen   = false;

  /* ── Open / close ─────────────────────────────────────────── */
  function openChat() {
    isOpen = true;
    popup.classList.add('gre-open');
    btn.setAttribute('aria-expanded', 'true');
    iconOpen.style.display = 'none';
    iconClose.style.display = '';
    if (badge) badge.style.display = 'none';
    popup.querySelector('.gre-chat-close').focus();
  }

  function closeChat(savePref) {
    isOpen = false;
    popup.classList.remove('gre-open');
    btn.setAttribute('aria-expanded', 'false');
    iconOpen.style.display = '';
    iconClose.style.display = 'none';
    if (savePref) {
      try { sessionStorage.setItem(SESSION_KEY, '1'); } catch(e){}
    }
    btn.focus();
  }

  /* ── Events ───────────────────────────────────────────────── */
  btn.addEventListener('click', function () {
    isOpen ? closeChat(false) : openChat();
  });

  closeBtn.addEventListener('click', function () {
    closeChat(true);
  });

  /* Close on Escape */
  document.addEventListener('keydown', function (e) {
    if (isOpen && (e.key === 'Escape' || e.keyCode === 27)) closeChat(false);
  });

  /* Close if clicking outside popup + button */
  document.addEventListener('click', function (e) {
    if (isOpen && !popup.contains(e.target) && !btn.contains(e.target)) {
      closeChat(false);
    }
  });

  /* ── Auto-open after delay (once per session) ─────────────── */
  try {
    if (!sessionStorage.getItem(SESSION_KEY)) {
      setTimeout(function () {
        if (!isOpen) openChat();
      }, AUTO_OPEN_DELAY);
    }
  } catch(e) {}

  /* ── Analytics helper (GA4 event if available) ─────────────── */
  window.greChatTrack = function (channel) {
    try {
      if (typeof gtag === 'function') {
        gtag('event', 'chat_widget_click', {
          event_category: 'Lead',
          event_label: channel,
          value: 1
        });
      }
    } catch(e) {}
  };

})();
