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

    // Inject the floating "Call Nitin" CTA
    if (!document.getElementById('gre-call-float')) {
      var a = document.createElement('a');
      a.id = 'gre-call-float';
      a.className = 'gre-call-float';
      a.href = 'tel:+19177050132';
      a.innerHTML = '<span class="desk">Call Nitin: </span>(917) 705-0132';
      a.setAttribute('aria-label', 'Call Nitin Gadura at 917-705-0132');
      document.body.appendChild(a);
    }
  });
})();
