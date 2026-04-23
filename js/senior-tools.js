/* Gadura Real Estate — senior-friendly tools (A+ toggle + call float injection).
   Loaded on every page. No dependencies. */
(function(){
  // Restore large-text preference BEFORE paint
  try {
    if (localStorage.getItem('gre-large-text') === '1') {
      document.documentElement.classList.add('large-text');
    }
  } catch(e){}

  function ready(fn){
    if (document.readyState !== 'loading') fn();
    else document.addEventListener('DOMContentLoaded', fn);
  }

  ready(function(){
    // Inject the A+ toggle into the first <nav> or <header>
    if (!document.getElementById('gre-text-size-toggle')) {
      var btn = document.createElement('button');
      btn.id = 'gre-text-size-toggle';
      btn.className = 'gre-text-size-toggle';
      btn.type = 'button';
      btn.setAttribute('aria-pressed', document.documentElement.classList.contains('large-text') ? 'true' : 'false');
      btn.textContent = 'A+ Larger Text';
      btn.style.marginLeft = '.5rem';
      btn.addEventListener('click', function(){
        var on = document.documentElement.classList.toggle('large-text');
        btn.setAttribute('aria-pressed', on ? 'true' : 'false');
        try { localStorage.setItem('gre-large-text', on ? '1' : '0'); } catch(e){}
      });
      var nav = document.querySelector('nav') || document.querySelector('header');
      if (nav) nav.appendChild(btn);
    }

    // Floating "Call Nitin" CTA removed per client request.
    // Also remove any previously-injected instance from cached/visited pages.
    var existing = document.getElementById('gre-call-float');
    if (existing && existing.parentNode) existing.parentNode.removeChild(existing);
  });
})();
