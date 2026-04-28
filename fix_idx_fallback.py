#!/usr/bin/env python3
"""
Flip IDX embed strategy:
- Show fallback CTA immediately (not after 11s)
- Load iFrame silently in background
- If iFrame loads successfully, swap it in (replacing the CTA)
- Reduces timeout from 11s to 3s for the swap check
"""
import os, re, glob

OLD_SCRIPT = r"""(function\(\){[^}]*var fr=document\.getElementById\('idx-frame-[^']+'\);[^}]*var ld=document\.getElementById\('idx-load-[^']+'\);[^}]*var fb=document\.getElementById\('idx-fall-[^']+'\);[^}]*var ok=false;[^}]*fr\.addEventListener\('load',function\(\){[^}]*ok=true;[^}]*ld\.style\.display='none';[^}]*fr\.style\.display='block';[^}]*}\);[^}]*setTimeout\(function\(\){[^}]*if\(!ok\){[^}]*ld\.style\.display='none';[^}]*fb\.style\.display='block';[^}]*}[^}]*},11000\);[^}]*}\)\(\);)"""

NEW_SCRIPT_TEMPLATE = """(function(){{
    var fr=document.getElementById('idx-frame-{uid}');
    var ld=document.getElementById('idx-load-{uid}');
    var fb=document.getElementById('idx-fall-{uid}');
    // Show CTA immediately — iFrame loads silently in background
    if(ld) ld.style.display='none';
    if(fb) fb.style.display='block';
    // If iFrame loads within 3s, swap it in
    var ok=false;
    if(fr){{
      fr.addEventListener('load',function(){{
        ok=true;
        if(fb) fb.style.display='none';
        fr.style.display='block';
      }});
      setTimeout(function(){{if(!ok && fr) fr.src=fr.src;}},500);
    }}
  }})();"""

def fix_file(fpath):
    with open(fpath, 'r', encoding='utf-8') as f:
        html = f.read()
    
    if 'idx-frame-' not in html and 'idx-embed-frame' not in html:
        return 0

    changed = 0
    
    # Find all uid patterns used in this file
    uids = re.findall(r"idx-frame-([a-z0-9]+)", html)
    
    for uid in set(uids):
        # Replace the old script block for this uid
        old = f"""(function(){{
    var fr=document.getElementById('idx-frame-{uid}');
    var ld=document.getElementById('idx-load-{uid}');
    var fb=document.getElementById('idx-fall-{uid}');
    var ok=false;
    fr.addEventListener('load',function(){{ok=true;ld.style.display='none';fr.style.display='block';}});
    setTimeout(function(){{if(!ok){{ld.style.display='none';fb.style.display='block';}}}},11000);
  }})();"""
        
        new = NEW_SCRIPT_TEMPLATE.format(uid=uid)
        
        if old in html:
            html = html.replace(old, new)
            changed += 1
    
    # Also handle the neighborhood top-level pages (slightly different format)
    old_top = """(function() {
      var frame   = document.getElementById('idx-embed-frame');
      var loader  = document.getElementById('idx-loading-bar');
      var fallback= document.getElementById('idx-fallback');
      var loaded  = false;

      frame.addEventListener('load', function() {
        loaded = true;
        loader.style.display  = 'none';
        frame.style.display   = 'block';
      });

      setTimeout(function() {
        if (!loaded) {
          loader.style.display   = 'none';
          fallback.style.display = 'block';
        }
      }, 11000);
    })();"""

    new_top = """(function() {
      var frame   = document.getElementById('idx-embed-frame');
      var loader  = document.getElementById('idx-loading-bar');
      var fallback= document.getElementById('idx-fallback');
      // Show CTA immediately — iFrame loads silently in background
      if(loader)  loader.style.display  = 'none';
      if(fallback) fallback.style.display = 'block';
      // Swap in iFrame if it loads
      var loaded = false;
      if(frame) {
        frame.addEventListener('load', function() {
          loaded = true;
          if(fallback) fallback.style.display = 'none';
          frame.style.display = 'block';
        });
      }
    })();"""

    if old_top in html:
        html = html.replace(old_top, new_top)
        changed += 1

    # Handle buy.html / map-available.html 10s/12s timeouts
    html = re.sub(r'setTimeout\(function\(\)\s*\{[^}]*\.style\.display\s*=\s*\'none\'[^}]*\.style\.display\s*=\s*\'block\'[^}]*\}\s*\}\s*,\s*1[02]000\)', '', html)

    if changed:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(html)
    
    return changed

total = 0
files = (
    glob.glob('/Users/nidhigadura/Jagex/gadura-realestate/*.html') +
    glob.glob('/Users/nidhigadura/Jagex/gadura-realestate/neighborhoods/*.html') +
    glob.glob('/Users/nidhigadura/Jagex/gadura-realestate/neighborhoods/**/*.html', recursive=True)
)

for fpath in sorted(files):
    n = fix_file(fpath)
    if n:
        total += n
        print(f"  ✅ {fpath.replace('/Users/nidhigadura/Jagex/gadura-realestate/','')}")

print(f"\nFixed {total} script blocks across {sum(1 for f in files if fix_file.__module__)} pages")
