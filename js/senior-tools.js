/* Gadura Real Estate — senior-friendly tools were rolled back on 2026-04-22
   per client request. This file now proactively removes any previously-
   injected elements (A+ toggle + floating Call Nitin button) and clears
   the localStorage large-text preference so cached pages revert cleanly. */
(function(){
  try {
    document.documentElement.classList.remove('large-text');
    localStorage.removeItem('gre-large-text');
  } catch(e){}

  function ready(fn){
    if (document.readyState !== 'loading') fn();
    else document.addEventListener('DOMContentLoaded', fn);
  }

  ready(function(){
    var toRemove = ['gre-text-size-toggle', 'gre-call-float'];
    toRemove.forEach(function(id){
      var el = document.getElementById(id);
      if (el && el.parentNode) el.parentNode.removeChild(el);
    });
  });
})();
