#!/usr/bin/env python3
"""Check generated editions, local links and fragments without extra dependencies."""
import json, re, hashlib, subprocess, sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
ROOT=Path(__file__).resolve().parents[1]
VOID=set('area base br col embed hr img input link meta param source track wbr'.split())
class Nest(HTMLParser):
    """Generated editions use explicit end tags; catch broken disclosure nesting."""
    def __init__(self, text):
        super().__init__(); self.stack=[]; self.errors=[]; self.feed(text)
    def handle_starttag(self, tag, attrs):
        if tag not in VOID: self.stack.append((tag,self.getpos()))
    def handle_endtag(self, tag):
        if not self.stack or self.stack[-1][0]!=tag:
            self.errors.append((self.getpos(),tag,self.stack[-3:]))
        else: self.stack.pop()
class Doc(HTMLParser):
    def __init__(self, text):
        super().__init__(); self.refs=[]; self.ids=[]; self.feed(text)
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if 'id' in a: self.ids.append(a['id'])
        self.refs.extend(a[k] for k in ['href','src','poster'] if k in a)
class ViewerSources(HTMLParser):
    def __init__(self,text):
        super().__init__(); self.active=None; self.errors=[]; self.feed(text)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='a' and 'data-screenshot' in a: self.active={'attrs':a,'image':False}
        if tag=='img' and self.active is not None: self.active['image']=True
    def handle_endtag(self,tag):
        if tag=='a' and self.active is not None:
            a=self.active['attrs']
            if not self.active['image'] and not (a.get('data-source-width') and a.get('data-source-alt')):
                self.errors.append(a.get('href'))
            self.active=None

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
baseline=[ROOT/'index.html',*(ROOT/'work').glob('*'),ROOT/'styles.css',ROOT/'script.js',ROOT/'case.js',ROOT/'case-base.css',ROOT/'case-theme.css']
before={p:digest(p) for p in baseline if p.is_file()}
generated={p:digest(p) for p in (ROOT/'versions').rglob('*') if p.is_file()}
subprocess.run([sys.executable,str(ROOT/'scripts/build_versions.py')],check=True)
assert all(digest(p)==v for p,v in before.items()),'Builder changed original portfolio'
assert all(digest(p)==v for p,v in generated.items()),'Generated files were stale or build is not deterministic'
pages=[ROOT/'index.html',*(ROOT/'work').glob('*.html'),*(ROOT/'versions').rglob('*.html')]
errors=[]
for p in pages:
    d=Doc(p.read_text())
    if p.is_relative_to(ROOT/'versions'):
        viewer=ViewerSources(p.read_text())
        if viewer.errors: errors.append((str(p),'viewer source missing image metadata',viewer.errors))
        nesting=Nest(p.read_text())
        if nesting.errors or nesting.stack: errors.append((str(p),'unbalanced generated markup',nesting.errors,nesting.stack))
    if len(d.ids)!=len(set(d.ids)): errors.append((str(p),'duplicate IDs'))
    for ref in d.refs:
        u=urlsplit(ref)
        if u.scheme or u.netloc: continue
        target=(p.parent/unquote(u.path)).resolve() if u.path else p
        if not target.exists(): errors.append((str(p.relative_to(ROOT)),ref,'missing file'))
        elif u.fragment and target.suffix=='.html' and unquote(u.fragment) not in Doc(target.read_text()).ids:
            errors.append((str(p.relative_to(ROOT)),ref,'missing fragment'))
assert not errors,json.dumps(errors,indent=2)
print(f'PASS: {len(pages)} HTML pages, local file/fragment references, unique IDs, generated markup nesting, deterministic build, original portfolio preserved.')
