/* =========================================================
   GADURA REAL ESTATE — MAIN JS
   ========================================================= */

/* ---- MOBILE NAV ---- */
(function(){
  const ham = document.querySelector('.hamburger');
  const mobileNav = document.querySelector('.mobile-nav');
  const closeBtn = document.querySelector('.mobile-close');
  if(!ham) return;
  function openNav(){ mobileNav.classList.add('open'); document.body.style.overflow='hidden'; ham.setAttribute('aria-expanded','true'); }
  function closeNav(){ mobileNav.classList.remove('open'); document.body.style.overflow=''; ham.setAttribute('aria-expanded','false'); }
  ham.addEventListener('click', openNav);
  if(closeBtn) closeBtn.addEventListener('click', closeNav);
  document.addEventListener('keydown', e => { if(e.key==='Escape') closeNav(); });
})();

/* ---- HOME VALUATION FORM ---- */
(function(){
  const form = document.getElementById('valuation-form');
  if(!form) return;
  form.addEventListener('submit', function(e){
    e.preventDefault();
    const btn = form.querySelector('.form-submit');
    const orig = btn.textContent;
    btn.textContent = 'Sending\u2026'; btn.disabled = true;
    const data = {
      address: form.address ? form.address.value : '',
      name:    form.full_name ? form.full_name.value : '',
      email:   form.email ? form.email.value : '',
      phone:   form.phone ? form.phone.value : '',
      type:    form.property_type ? form.property_type.value : '',
    };
    var encoded = Object.keys(data).map(function(k){
      return encodeURIComponent(k) + '=' + encodeURIComponent(data[k]);
    });
    fetch('https://formspree.io/f/xpwzywde', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify(data)
    })
    .then(function(r){
      if(r.ok){
        form.innerHTML = '<div class="alert alert-success" style="text-align:center;padding:28px;"><p style="font-size:1.1rem;font-weight:700;color:#155724;margin-bottom:8px;">\u2713 Request Received!</p><p>Thank you, <strong>' + data.name + '</strong>. One of our agents will contact you within 2 hours with your free home valuation.</p></div>';
        document.dispatchEvent(new CustomEvent('gadura:valuation_submitted'));
      } else { throw new Error(); }
    })
    .catch(function(){
      btn.textContent = orig; btn.disabled = false;
      alert('There was an error. Please call us at (718) 850-0010.');
    });
  });
})();

/* ---- CONTACT FORM ---- */
(function(){
  const form = document.getElementById('contact-form');
  if(!form) return;
  form.addEventListener('submit', function(e){
    e.preventDefault();
    const btn = form.querySelector('[type=submit]');
    btn.textContent = 'Sending\u2026'; btn.disabled = true;
    const data = {
      name:    form.name ? form.name.value : '',
      email:   form.email ? form.email.value : '',
      phone:   form.phone ? form.phone.value : '',
      message: form.message ? form.message.value : '',
      subject: form.subject ? form.subject.value : '',
    };
    var encoded = Object.keys(data).map(function(k){
      return encodeURIComponent(k) + '=' + encodeURIComponent(data[k]);
    });
    fetch('https://formspree.io/f/xpwzywde', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify(data)
    })
    .then(function(r){
      if(r.ok){
        form.innerHTML = '<div class="alert alert-success" style="padding:28px;text-align:center;"><p style="font-size:1.1rem;font-weight:700;">\u2713 Message Sent!</p><p>We\'ll get back to you within 1 business day. Or call us now: <a href="tel:+17188500010" style="color:#155724;font-weight:700;">(718) 850-0010</a></p></div>';
      } else { throw new Error(); }
    })
    .catch(function(){
      btn.textContent = 'Send Message'; btn.disabled = false;
      alert('Please call us directly at (718) 850-0010.');
    });
  });
})();

/* ---- MORTGAGE CALCULATOR ---- */
(function(){
  var form = document.getElementById('mortgage-calc');
  if(!form) return;
  function calc(){
    var price  = parseFloat(document.getElementById('mc-price') ? document.getElementById('mc-price').value : 0) || 0;
    var down   = parseFloat(document.getElementById('mc-down')  ? document.getElementById('mc-down').value  : 20) || 20;
    var rate   = parseFloat(document.getElementById('mc-rate')  ? document.getElementById('mc-rate').value  : 7.0) || 7.0;
    var years  = parseInt(document.getElementById('mc-years')   ? document.getElementById('mc-years').value  : 30) || 30;
    var result = document.getElementById('mc-result');
    if(!price || price < 1000){ if(result) result.style.display='none'; return; }
    var principal = price * (1 - down/100);
    var monthly_rate = rate / 100 / 12;
    var n = years * 12;
    var payment;
    if(monthly_rate === 0){ payment = principal / n; }
    else { payment = principal * monthly_rate * Math.pow(1+monthly_rate, n) / (Math.pow(1+monthly_rate, n) - 1); }
    if(result){
      result.style.display = 'block';
      var amountEl = result.querySelector('.amount');
      if(amountEl) amountEl.textContent = '$' + payment.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
      var downAmt = result.querySelector('.down-amount');
      if(downAmt) downAmt.textContent = '$' + (price * down / 100).toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
      var loanAmt = result.querySelector('.loan-amount');
      if(loanAmt) loanAmt.textContent = '$' + principal.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    }
  }
  form.querySelectorAll('input, select').forEach(function(el){ el.addEventListener('input', calc); });
  calc();
})();

/* ---- SOLD MAP (Leaflet) ---- */
(function(){
  if(!document.getElementById('sold-map')) return;
  if(typeof L === 'undefined') return;

  var soldData = [
    { lat:40.6971, lng:-73.8334, address:"104-31 125th St", neighborhood:"South Richmond Hill", price:"$317,500", date:"May 2025", type:"Single Family", agent:"Gaurav Bhardwaj", year:2025 },
    { lat:40.6820, lng:-73.8452, address:"101st Ave & 107th St", neighborhood:"Ozone Park", price:"$625,000", date:"Jan 2025", type:"Two Family", agent:"Vinod Gadura", year:2025 },
    { lat:40.6968, lng:-73.8290, address:"115th St, Richmond Hill", neighborhood:"Richmond Hill", price:"$740,000", date:"Nov 2024", type:"Two Family", agent:"Nitin Gadura", year:2024 },
    { lat:40.6960, lng:-73.8450, address:"Rockaway Blvd, Ozone Park", neighborhood:"Ozone Park", price:"$530,000", date:"Sep 2024", type:"Single Family", agent:"Vinod Gadura", year:2024 },
    { lat:40.6943, lng:-73.8068, address:"Sutphin Blvd, Jamaica", neighborhood:"Jamaica", price:"$1,200,000", date:"Jun 2024", type:"Mixed Use", agent:"Vinod Gadura", year:2024 },
    { lat:40.6718, lng:-73.8232, address:"S Conduit Ave, S Ozone Park", neighborhood:"South Ozone Park", price:"$680,000", date:"Mar 2024", type:"Two Family", agent:"Gaurav Bhardwaj", year:2024 },
    { lat:40.6918, lng:-73.8569, address:"Jamaica Ave, Woodhaven", neighborhood:"Woodhaven", price:"$595,000", date:"Dec 2023", type:"Single Family", agent:"Nitin Gadura", year:2023 },
    { lat:40.7124, lng:-73.8319, address:"Metropolitan Ave, Kew Gardens", neighborhood:"Kew Gardens", price:"$850,000", date:"Oct 2023", type:"Two Family", agent:"Vinod Gadura", year:2023 },
    { lat:40.7082, lng:-73.8218, address:"Briarwood, Jamaica Ave", neighborhood:"Briarwood", price:"$720,000", date:"Aug 2023", type:"Single Family", agent:"Gaurav Bhardwaj", year:2023 },
    { lat:40.7195, lng:-73.7832, address:"Jamaica Estates", neighborhood:"Jamaica Estates", price:"$1,100,000", date:"May 2023", type:"Single Family", agent:"Vinod Gadura", year:2023 },
    { lat:40.7133, lng:-73.7654, address:"Francis Lewis Blvd, Hollis", neighborhood:"Hollis", price:"$580,000", date:"Feb 2023", type:"Single Family", agent:"Nitin Gadura", year:2023 },
    { lat:40.7213, lng:-73.7454, address:"Springfield Blvd, Queens Village", neighborhood:"Queens Village", price:"$640,000", date:"Nov 2022", type:"Single Family", agent:"Vinod Gadura", year:2022 },
    { lat:40.7345, lng:-73.6876, address:"New Hyde Park Rd", neighborhood:"New Hyde Park", price:"$720,000", date:"Aug 2022", type:"Single Family", agent:"Gaurav Bhardwaj", year:2022 },
    { lat:40.6830, lng:-73.8520, address:"Linden Blvd, Ozone Park", neighborhood:"Ozone Park", price:"$590,000", date:"Mar 2022", type:"Two Family", agent:"Nitin Gadura", year:2022 },
    { lat:40.6990, lng:-73.8200, address:"Liberty Ave, Richmond Hill", neighborhood:"Richmond Hill", price:"$810,000", date:"Sep 2021", type:"Mixed Use", agent:"Vinod Gadura", year:2021 },
  ];

  var map = L.map('sold-map').setView([40.7000, -73.8200], 12);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{
    maxZoom:18, attribution:'\u00a9 <a href="https://openstreetmap.org">OpenStreetMap</a>'
  }).addTo(map);

  function makeIcon(color){
    return L.divIcon({
      html: '<div style="width:14px;height:14px;background:'+color+';border-radius:50%;border:2px solid #fff;box-shadow:0 2px 5px rgba(0,0,0,.4);"></div>',
      iconSize:[14,14], className:''
    });
  }

  var markers = [];
  var currentFilter = 'all';
  var now = new Date().getFullYear();

  function renderMarkers(){
    markers.forEach(function(m){ map.removeLayer(m); });
    markers = [];
    var filtered = soldData.filter(function(p){
      if(currentFilter === '1yr')  return p.year >= now - 1;
      if(currentFilter === '5yr')  return p.year >= now - 5;
      return true;
    });
    filtered.forEach(function(p){
      var m = L.marker([p.lat, p.lng], { icon: makeIcon(p.year >= now - 1 ? '#00A651' : '#1B2A6B') })
        .addTo(map)
        .bindPopup('<strong>'+p.address+'</strong><br>'+p.neighborhood+'<br><span style="color:#00A651;font-size:1.1em;font-weight:700;">'+p.price+'</span><br>'+p.type+' \u00b7 '+p.date+'<br><em>Sold by: '+p.agent+'</em>');
      markers.push(m);
    });
    var statsTotal = document.getElementById('stats-total');
    var statsVol   = document.getElementById('stats-vol');
    if(statsTotal) statsTotal.textContent = filtered.length;
    if(statsVol){
      var total = filtered.reduce(function(s,p){ return s + parseFloat(p.price.replace(/[$,]/g,'')); }, 0);
      statsVol.textContent = '$' + (total/1000000).toFixed(1) + 'M';
    }
  }

  document.querySelectorAll('.map-filter[data-filter]').forEach(function(btn){
    btn.addEventListener('click', function(){
      document.querySelectorAll('.map-filter[data-filter]').forEach(function(b){ b.classList.remove('active'); });
      this.classList.add('active');
      currentFilter = this.dataset.filter;
      renderMarkers();
    });
  });

  renderMarkers();
})();

/* ---- AVAILABLE MAP (Leaflet) ---- */
(function(){
  if(!document.getElementById('available-map')) return;
  if(typeof L === 'undefined') return;

  var map = L.map('available-map').setView([40.6850, -73.7500], 10);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{
    maxZoom:18, attribution:'\u00a9 <a href="https://openstreetmap.org">OpenStreetMap</a>'
  }).addTo(map);

  var listings = [
    /* ── QUEENS ── */
    { lat:40.6871, lng:-73.8369, address:"106-09 101st Ave (Office)", neighborhood:"Ozone Park", price:"Office", type:"single", beds:0, baths:0, sqft:0 },
    { lat:40.6968, lng:-73.8290, address:"103-22 125th St", neighborhood:"Richmond Hill", price:"$1,180,000", type:"multi", beds:6, baths:3, sqft:2200 },
    { lat:40.6900, lng:-73.8420, address:"107-14 107th St", neighborhood:"Ozone Park", price:"$1,099,000", type:"multi", beds:5, baths:2, sqft:1960 },
    { lat:40.6718, lng:-73.8232, address:"134-16 116th St", neighborhood:"South Ozone Park", price:"$1,125,000", type:"multi", beds:5, baths:3, sqft:2100 },
    { lat:40.6750, lng:-73.8160, address:"119-42 130th St", neighborhood:"South Ozone Park", price:"$975,000", type:"single", beds:4, baths:2, sqft:1680 },
    { lat:40.6918, lng:-73.8569, address:"91-11 88th Rd", neighborhood:"Woodhaven", price:"$1,199,000", type:"multi", beds:5, baths:4, sqft:2080 },
    { lat:40.6954, lng:-73.8507, address:"95-26 86th St", neighborhood:"Ozone Park / Woodhaven", price:"$1,389,000", type:"multi", beds:6, baths:3, sqft:0 },
    { lat:40.6949, lng:-73.8482, address:"95-18 91st St", neighborhood:"Ozone Park / Woodhaven", price:"$1,299,000", type:"multi", beds:5, baths:2, sqft:2440 },
    { lat:40.6982, lng:-73.8451, address:"97-33 89th St", neighborhood:"Ozone Park", price:"$915,000", type:"multi", beds:4, baths:3, sqft:1512 },
    { lat:40.6943, lng:-73.8068, address:"87-10 Talbot St", neighborhood:"Jamaica", price:"$1,225,000", type:"multi", beds:6, baths:3, sqft:2280 },
    { lat:40.7082, lng:-73.8218, address:"109-26 122nd St", neighborhood:"South Richmond Hill", price:"$1,050,000", type:"multi", beds:5, baths:2, sqft:1850 },
    { lat:40.7124, lng:-73.8319, address:"164-15 88th Ave", neighborhood:"Jamaica", price:"$1,375,000", type:"multi", beds:5, baths:3, sqft:2050 },
    { lat:40.7195, lng:-73.7832, address:"85-35 Edgerton Blvd", neighborhood:"Jamaica Estates", price:"$1,399,000", type:"single", beds:4, baths:4, sqft:2030 },
    { lat:40.7133, lng:-73.7654, address:"220-44 96th Ave", neighborhood:"Queens Village", price:"$975,000", type:"single", beds:4, baths:2, sqft:1780 },
    { lat:40.7041, lng:-73.7680, address:"195-14 115th Rd", neighborhood:"St. Albans", price:"$875,000", type:"single", beds:3, baths:2, sqft:1450 },
    { lat:40.6850, lng:-73.7430, address:"232-17 148th Dr", neighborhood:"Rosedale", price:"$825,000", type:"single", beds:3, baths:2, sqft:1380 },
    { lat:40.6990, lng:-73.7620, address:"146-52 182nd St", neighborhood:"Springfield Gardens", price:"$950,000", type:"single", beds:4, baths:2, sqft:1640 },
    { lat:40.7110, lng:-73.8430, address:"69-16 Metropolitan Ave", neighborhood:"Middle Village", price:"$1,285,000", type:"multi", beds:4, baths:3, sqft:2200 },
    { lat:40.7000, lng:-73.8700, address:"79-20 88th St", neighborhood:"Glendale", price:"$1,150,000", type:"single", beds:4, baths:2, sqft:1800 },
    { lat:40.7062, lng:-73.7920, address:"114-06 Farmers Blvd", neighborhood:"Cambria Heights", price:"$1,025,000", type:"single", beds:4, baths:2, sqft:1720 },
    /* ── BROOKLYN ── */
    { lat:40.6780, lng:-73.8750, address:"1025 Vermont St", neighborhood:"East New York, Brooklyn", price:"$1,150,000", type:"multi", beds:5, baths:3, sqft:2100 },
    { lat:40.6850, lng:-73.8800, address:"88 Autumn Ave", neighborhood:"Cypress Hills, Brooklyn", price:"$1,050,000", type:"multi", beds:4, baths:3, sqft:1850 },
    { lat:40.6480, lng:-73.9300, address:"1214 New York Ave", neighborhood:"Flatbush, Brooklyn", price:"$1,275,000", type:"multi", beds:6, baths:3, sqft:2350 },
    { lat:40.6700, lng:-73.8820, address:"537 Miller Ave", neighborhood:"East New York, Brooklyn", price:"$985,000", type:"multi", beds:4, baths:2, sqft:1680 },
    { lat:40.6700, lng:-73.9100, address:"1422 East 98th St", neighborhood:"Canarsie, Brooklyn", price:"$950,000", type:"single", beds:3, baths:2, sqft:1580 },
    { lat:40.6780, lng:-73.8920, address:"750 Blake Ave", neighborhood:"East New York, Brooklyn", price:"$1,175,000", type:"multi", beds:6, baths:3, sqft:2280 },
    { lat:40.6520, lng:-73.9200, address:"2218 Foster Ave", neighborhood:"Flatbush, Brooklyn", price:"$1,350,000", type:"multi", beds:5, baths:3, sqft:2200 },
    { lat:40.6610, lng:-73.9050, address:"186 Ridgewood Ave", neighborhood:"Crown Heights, Brooklyn", price:"$1,080,000", type:"multi", beds:5, baths:2, sqft:1920 },
    /* ── LONG ISLAND ── */
    { lat:40.6930, lng:-73.7040, address:"29 Nelson St", neighborhood:"Elmont, NY", price:"$780,000", type:"single", beds:3, baths:2, sqft:1380 },
    { lat:40.6620, lng:-73.7060, address:"107 Roosevelt Blvd", neighborhood:"Valley Stream, NY", price:"$875,000", type:"single", beds:4, baths:2, sqft:1650 },
    { lat:40.7060, lng:-73.6180, address:"54 Westwood Ave", neighborhood:"Hempstead, NY", price:"$725,000", type:"single", beds:3, baths:2, sqft:1280 },
    { lat:40.6570, lng:-73.5870, address:"142 Roosevelt Ave", neighborhood:"Freeport, NY", price:"$850,000", type:"single", beds:4, baths:2, sqft:1580 },
    { lat:40.6560, lng:-73.6730, address:"88 Centre Ave", neighborhood:"Lynbrook, NY", price:"$950,000", type:"single", beds:3, baths:2, sqft:1640 },
    { lat:40.6600, lng:-73.7020, address:"67 Merrick Ave", neighborhood:"Valley Stream, NY", price:"$820,000", type:"single", beds:3, baths:2, sqft:1420 },
    { lat:40.6530, lng:-73.6130, address:"35 Sunrise Ave", neighborhood:"Baldwin, NY", price:"$895,000", type:"single", beds:4, baths:2, sqft:1750 },
    { lat:40.6600, lng:-73.5530, address:"45 Lakewood Pl", neighborhood:"Rockville Centre, NY", price:"$1,199,000", type:"single", beds:4, baths:3, sqft:2400 },
    { lat:40.6600, lng:-73.5430, address:"2241 Merrick Rd", neighborhood:"Merrick, NY", price:"$1,075,000", type:"single", beds:4, baths:2, sqft:1900 },
    { lat:40.6070, lng:-73.7580, address:"112 Beach 25th St", neighborhood:"Far Rockaway, NY", price:"$699,000", type:"single", beds:3, baths:2, sqft:1300 },
    { lat:40.6960, lng:-73.7000, address:"18 Elm Ave", neighborhood:"Elmont, NY", price:"$980,000", type:"multi", beds:4, baths:3, sqft:1960 },
  ];

  var iconColors = { single:'#00A651', multi:'#1B2A6B', commercial:'#e67e22' };
  var markers = [];
  var currentType = 'all';

  function makeIcon(color){
    return L.divIcon({
      html: '<div style="width:16px;height:16px;background:'+color+';border-radius:50%;border:2px solid #fff;box-shadow:0 2px 5px rgba(0,0,0,.4);"></div>',
      iconSize:[16,16], className:''
    });
  }

  function renderMarkers(){
    markers.forEach(function(m){ map.removeLayer(m); });
    markers = [];
    var filtered = currentType === 'all' ? listings : listings.filter(function(l){ return l.type === currentType; });
    filtered.forEach(function(p){
      var typeLabel = p.type === 'single' ? 'Single Family' : p.type === 'multi' ? 'Multi Family' : 'Commercial';
      var m = L.marker([p.lat, p.lng], { icon: makeIcon(iconColors[p.type] || '#888') })
        .addTo(map)
        .bindPopup('<strong style="font-size:1.05em;">'+p.price+'</strong><br>'+p.address+'<br>'+p.neighborhood+'<br>'+typeLabel+(p.beds ? ' \u00b7 '+p.beds+' bed / '+p.baths+' bath' : '')+'<br>'+p.sqft.toLocaleString()+' sqft<br><a href="buy.html" style="color:#00A651;font-weight:700;">View Details \u2192</a>');
      markers.push(m);
    });
    var countEl = document.getElementById('avail-count');
    if(countEl) countEl.textContent = filtered.length;
  }

  document.querySelectorAll('.map-filter[data-type]').forEach(function(btn){
    btn.addEventListener('click', function(){
      document.querySelectorAll('.map-filter[data-type]').forEach(function(b){ b.classList.remove('active'); });
      this.classList.add('active');
      currentType = this.dataset.type;
      renderMarkers();
    });
  });

  renderMarkers();
})();

/* ---- OFFICE MAP (Leaflet) ---- */
(function(){
  if(!document.getElementById('office-map')) return;
  if(typeof L === 'undefined') return;
  var map = L.map('office-map').setView([40.6820, -73.8452], 16);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{
    maxZoom:18, attribution:'\u00a9 <a href="https://openstreetmap.org">OpenStreetMap</a>'
  }).addTo(map);
  var icon = L.divIcon({
    html: '<div style="background:#00A651;color:#fff;padding:6px 12px;border-radius:6px;font-family:Montserrat,sans-serif;font-weight:700;font-size:12px;white-space:nowrap;box-shadow:0 2px 8px rgba(0,0,0,.3);">Gadura Real Estate</div>',
    iconAnchor:[60,30], className:''
  });
  L.marker([40.6820, -73.8452], {icon}).addTo(map)
    .bindPopup('<strong>Gadura Real Estate LLC</strong><br>106-09 101st Ave<br>Ozone Park, NY 11416<br><a href="tel:+17188500010">(718) 850-0010</a>').openPopup();
})();

/* ---- SMOOTH SCROLL ---- */
document.querySelectorAll('a[href^="#"]').forEach(function(a){
  a.addEventListener('click', function(e){
    var target = document.querySelector(a.getAttribute('href'));
    if(!target) return;
    e.preventDefault();
    window.scrollTo({ top: target.getBoundingClientRect().top + window.scrollY - 80, behavior: 'smooth' });
  });
});

/* ---- STICKY HEADER SHRINK ---- */
(function(){
  var header = document.querySelector('.site-header');
  if(!header) return;
  function onScroll(){
    header.classList.toggle('scrolled', window.scrollY > 60);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
})();

/* ---- SCROLL-TO-TOP BUTTON ---- */
(function(){
  var btn = document.createElement('button');
  btn.className = 'scroll-top';
  btn.setAttribute('aria-label', 'Back to top');
  btn.innerHTML = '&#8679;';
  document.body.appendChild(btn);
  window.addEventListener('scroll', function(){
    btn.classList.toggle('visible', window.scrollY > 400);
  }, { passive: true });
  btn.addEventListener('click', function(){
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
})();

/* ---- SCROLL FADE-IN ANIMATIONS ---- */
(function(){
  if(!('IntersectionObserver' in window)) {
    document.querySelectorAll('.fade-in').forEach(function(el){ el.classList.add('visible'); });
    return;
  }
  var io = new IntersectionObserver(function(entries){
    entries.forEach(function(entry){
      if(entry.isIntersecting){
        entry.target.classList.add('visible');
        io.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12 });
  document.querySelectorAll('.fade-in').forEach(function(el){ io.observe(el); });
})();

/* ---- ANIMATED STAT COUNTERS ---- */
(function(){
  function animateCount(el){
    var target = parseInt(el.dataset.target, 10);
    if(isNaN(target)) return;
    var duration = 1400;
    var start = performance.now();
    function step(now){
      var progress = Math.min((now - start) / duration, 1);
      var ease = 1 - Math.pow(1 - progress, 3);
      el.textContent = Math.floor(ease * target).toLocaleString() + (el.dataset.suffix || '');
      if(progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }
  if(!('IntersectionObserver' in window)) return;
  var io = new IntersectionObserver(function(entries){
    entries.forEach(function(entry){
      if(entry.isIntersecting){
        animateCount(entry.target);
        io.unobserve(entry.target);
      }
    });
  }, { threshold: 0.5 });
  document.querySelectorAll('[data-target]').forEach(function(el){ io.observe(el); });
})();

/* =========================================================
   GOOGLE ANALYTICS 4
   ─────────────────────────────────────────────────────────
   GA4 Measurement ID: G-9TM4LDZ7DD
   Account: Gadura Real Estate LLC (a389919340)
   Property: Gadura Real Estate - gadurarealestate.com (p531286155)
   ========================================================= */
(function(){
  var GA_ID = 'G-9TM4LDZ7DD';
  var s = document.createElement('script');
  s.async = true;
  s.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA_ID;
  document.head.appendChild(s);
  window.dataLayer = window.dataLayer || [];
  function gtag(){ dataLayer.push(arguments); }
  window.gtag = gtag;
  gtag('js', new Date());
  gtag('config', GA_ID, { anonymize_ip: true });

  /* Track valuation form submission as a conversion */
  document.addEventListener('gadura:valuation_submitted', function(){
    gtag('event', 'generate_lead', { event_category: 'Valuation Form', event_label: 'Seller Lead' });
  });

  /* Track phone link clicks */
  document.querySelectorAll('a[href^="tel:"]').forEach(function(el){
    el.addEventListener('click', function(){
      gtag('event', 'click', { event_category: 'Phone Call', event_label: el.getAttribute('href') });
    });
  });
})();
