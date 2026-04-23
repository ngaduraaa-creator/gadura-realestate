/* Gadura Real Estate — past sales renderer.
   Reads /data/past-sales.json and renders into matching containers on the page.
   Usage on any page:
     <div id="gre-past-sales" data-limit="6" data-showdate="true"></div>
     <span id="gre-past-sales-count"></span>  (total count)
     <span id="gre-past-sales-volume"></span> (total $ volume)
     <script src="/js/past-sales.js" defer></script>
*/
(function(){
  function fmtMoney(n){ return '$' + n.toLocaleString('en-US'); }
  function fmtDate(s){
    try {
      var d = new Date(s + 'T00:00:00');
      return d.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
    } catch(e){ return s; }
  }
  function parseYear(s){ return (s || '').slice(0,4); }

  function card(sale){
    var emoji = sale.units >= 2 ? '🏘️' : (sale.propertyType && sale.propertyType.toLowerCase().indexOf('condo') > -1 ? '🏢' : '🏠');
    return [
      '<article class="sale-card" style="background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 2px 10px rgba(0,0,0,.08);transition:transform .2s;">',
        '<div style="position:relative;aspect-ratio:4/3;background:linear-gradient(135deg,#0b2545,#13315c);display:flex;align-items:center;justify-content:center;color:#fff;font-size:3rem;">', emoji,
          '<span style="position:absolute;top:12px;left:12px;background:#e8c547;color:#0b2545;padding:4px 10px;border-radius:4px;font-size:.75rem;font-weight:700;letter-spacing:.5px;">SOLD</span>',
          '<span style="position:absolute;top:12px;right:12px;background:rgba(0,0,0,.55);color:#fff;padding:4px 10px;border-radius:4px;font-size:.72rem;font-weight:600;">', fmtDate(sale.closedDate), '</span>',
        '</div>',
        '<div style="padding:1rem 1.25rem;">',
          '<div style="color:#0b2545;font-weight:700;font-size:1.05rem;">', sale.neighborhood, ', NY (', sale.zip, ')</div>',
          '<div style="color:#555;font-size:.88rem;margin:.25rem 0;">', sale.propertyType, ' · Represented ', sale.represented, '</div>',
          '<div style="color:#00813f;font-weight:700;font-size:1.1rem;margin-top:.5rem;">', fmtMoney(sale.price), '</div>',
          sale.highlight ? ('<div style="color:#7a5800;background:#fff8e1;padding:4px 8px;border-radius:4px;font-size:.78rem;font-weight:600;margin-top:.4rem;display:inline-block;">' + sale.highlight + '</div>') : '',
        '</div>',
      '</article>'
    ].join('');
  }

  fetch('/data/past-sales.json')
    .then(function(r){ return r.json(); })
    .then(function(data){
      var sales = (data && data.sales) || [];
      // sort newest first
      sales.sort(function(a,b){ return (b.closedDate || '').localeCompare(a.closedDate || ''); });

      var totalVol = sales.reduce(function(sum, s){ return sum + (Number(s.price) || 0); }, 0);
      var totalCount = sales.length;

      // Counters
      document.querySelectorAll('#gre-past-sales-count, .gre-past-sales-count').forEach(function(el){
        el.textContent = totalCount.toLocaleString('en-US');
      });
      document.querySelectorAll('#gre-past-sales-volume, .gre-past-sales-volume').forEach(function(el){
        // Show in millions with one decimal if $1M+, otherwise in thousands
        if (totalVol >= 1000000) {
          el.textContent = '$' + (totalVol / 1000000).toFixed(1) + 'M+';
        } else {
          el.textContent = '$' + Math.round(totalVol / 1000) + 'K';
        }
      });

      // Grids — one-time render per container
      document.querySelectorAll('#gre-past-sales, .gre-past-sales-grid').forEach(function(container){
        var limit = parseInt(container.getAttribute('data-limit') || '0', 10);
        var slice = limit > 0 ? sales.slice(0, limit) : sales;
        container.innerHTML = slice.map(card).join('');
      });

      // Year filter (on /past-sales/ page)
      var yearFilter = document.getElementById('gre-year-filter');
      if (yearFilter) {
        var years = Array.from(new Set(sales.map(function(s){ return parseYear(s.closedDate); }))).filter(Boolean).sort().reverse();
        yearFilter.innerHTML = '<option value="">All years</option>' + years.map(function(y){ return '<option value="'+y+'">'+y+'</option>'; }).join('');
        yearFilter.addEventListener('change', function(){
          var y = yearFilter.value;
          var filtered = y ? sales.filter(function(s){ return parseYear(s.closedDate) === y; }) : sales;
          document.querySelectorAll('#gre-past-sales, .gre-past-sales-grid').forEach(function(c){
            c.innerHTML = filtered.map(card).join('');
          });
        });
      }

      // Neighborhood filter
      var hoodFilter = document.getElementById('gre-hood-filter');
      if (hoodFilter) {
        var hoods = Array.from(new Set(sales.map(function(s){ return s.neighborhood; }))).filter(Boolean).sort();
        hoodFilter.innerHTML = '<option value="">All neighborhoods</option>' + hoods.map(function(h){ return '<option value="'+h+'">'+h+'</option>'; }).join('');
        hoodFilter.addEventListener('change', function(){
          var h = hoodFilter.value;
          var filtered = h ? sales.filter(function(s){ return s.neighborhood === h; }) : sales;
          document.querySelectorAll('#gre-past-sales, .gre-past-sales-grid').forEach(function(c){
            c.innerHTML = filtered.map(card).join('');
          });
        });
      }
    })
    .catch(function(err){
      console.warn('Past sales load failed:', err);
      document.querySelectorAll('#gre-past-sales, .gre-past-sales-grid').forEach(function(c){
        c.innerHTML = '<p style="color:#888;font-style:italic;padding:1rem;">Past sales temporarily unavailable — please <a href="/contact.html">contact Nitin</a> directly for transaction history.</p>';
      });
    });
})();
