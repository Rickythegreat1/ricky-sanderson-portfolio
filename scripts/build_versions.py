#!/usr/bin/env python3
"""Build role editions without modifying the original portfolio or shared assets."""
import argparse, html, json, re, subprocess, sys
from pathlib import Path
from string import Template

ROOT = Path(__file__).resolve().parents[1]
E = html.escape

def inspector(project):
    item=project.get('inspect')
    if not item:return ''
    media=f'<img src="../../assets/{E(item["image"])}" alt="{E(item["alt"])}" width="1165" height="2063" loading="eager">' if item.get('image') else ''
    return f'<details class="evidence-inspect"><summary>{E(item["title"])}</summary><div class="evidence-content"><div class="evidence-content-inner">{media}<p>{E(item["copy"])}</p><a href="{E(item["link"])}">{E(item["link_text"])} ↗</a></div></div></details>'

def decision_preview(name, home=False):
    data={
      'crossroads':('01 / Team research → interface','A staff-led bulk sign-in flow.','Junior UX designer · Team project','Recreated interface · Sample data','element-attendance-layout.png',1440,872,'attendance','0.9','0.31','Element attendance detail, showing Bulk sign-in for selected sample students.'),
      'pcx':('02 / Requirements → prototype','Make task ranking explainable.','Design & prototyping','Frontend prototype · Mock data · No backend','pcx-prototype-home.webp',1165,747,'ranking','0.47','0.31','PCx prototype task recommendation with a Why is this first link.'),
      'taska':('03 / Research → interaction','Review the workflow before a run.','Independent research & design','Installation preview · Runtime not connected','taska/workflow.webp',1165,1157,'workflow','0.4','0.86','Taska workflow preview with separate Save workflow and Review and run controls.')
    }
    label,decision,role,scope,asset,w,h,window,x,y,alt=data[name]
    href=name+'.html' if home else '../../assets/'+asset
    attrs='' if home else f' data-screenshot data-zoom-focus-x="{x}" data-zoom-focus-y="{y}" data-viewer-caption="{E(scope)}. Full source image."'
    action='Read the '+('Crossroads Education' if name=='crossroads' else name.upper() if name=='pcx' else 'Taska')+' case' if home else 'Inspect the full source image'
    return f'<figure class="decision-preview preview-{name}"><p class="preview-kicker">{E(label)}</p><p class="preview-role">{E(role)}</p><div class="preview-stage"><a class="preview-window preview-{window}" href="{href}"{attrs} aria-label="{E(action)}"><img src="../../assets/{asset}" width="{w}" height="{h}" alt="{E(alt)}" loading="eager"></a></div><figcaption><strong>{E(decision)}</strong><span>{E(scope)}</span></figcaption></figure>'

def build(config):
    d = json.loads(config.read_text())
    slug = d['slug']
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', slug):
        raise ValueError('Use a lowercase, hyphenated slug.')
    if d.get('theme') == 'clay': subprocess.run([sys.executable, str(ROOT/'scripts/build_clay_motion.py')], check=True)
    out = ROOT / 'versions' / slug
    out.mkdir(parents=True, exist_ok=True)
    values = {k:E(str(d[k])) for k in ['label','title','discipline','intro','focus']}
    # Headline is trusted, authored local markup. Other configuration text is escaped.
    values['headline'] = d['headline']
    values['featured_preview'] = decision_preview('crossroads',home=True)
    values['description'] = E(f"Selected UX research and product work by Ricky Sanderson, prepared for {d['label']}.")
    for k,v in d['featured'].items(): values['featured_'+k] = E(str(v))
    values['methods'] = '\n'.join(f'<article class="method-card"><h3>{E(m["title"])}</h3><p>{E(m["copy"])}</p><a href="{E(m["link"])}">See the evidence ↗</a></article>' for m in d['methods'])
    values['supporting'] = '\n'.join(f'''<article class="support-card">{decision_preview(p['link'].removesuffix('.html'),home=True)}<p class="support-type">{E(p['type'])}</p><h3><a href="{E(p['link'])}">{E(p['name'])}</a></h3><p class="support-copy">{E(p['copy'])}</p><p class="scope">{E(p['scope'])}</p><a class="read-case" href="{E(p['link'])}">Read the case <span aria-hidden="true">↗</span></a>{inspector(p)}</article>''' for p in d['supporting'])
    home = Template((ROOT/'templates/role-home.html').read_text()).substitute(values)
    if d.get('theme') == 'clay': home = home.replace('</head>', '<link rel="stylesheet" href="../clay.css"><script src="../clay.js" defer></script></head>')
    (out/'index.html').write_text(home)
    for name in ['crossroads','pcx','taska']:
        source = (ROOT/'work'/f'{name}.html').read_text()
        for old,new in d.get('case_overrides',{}).get(name,[]):
            if source.count(old)!=1: raise ValueError(f'{slug}/{name}: expected exactly one source match: {old[:80]}')
            source = source.replace(old,new)
        source = source.replace('<body>', '<body class="role-case">')
        source = source.replace('Product &amp; UX designer', E(d['discipline']))
        if d.get('theme') == 'clay':
            source = source.replace('class="nav-link" href="mailto:', 'class="nav-link contact-pill" href="mailto:')
        source = source.replace('href="../index.html', 'href="./index.html')
        source = re.sub(r'((?:src|href|poster)=[\"\'])\.\./',r'\1../../',source)
        source = source.replace('href="./omnipilot.css"','href="../../work/omnipilot.css"')
        source = source.replace('href="../../concepts/','href="./concepts/')
        if d.get('theme') == 'clay': source = re.sub(r'src="../../case\.js[^"]*"', 'src="../clay-case.js"', source)
        source = source.replace('</head>', '<link rel="stylesheet" href="../role.css">' + ('<link rel="stylesheet" href="../clay.css"><script src="../clay.js" defer></script>' if d.get('theme') == 'clay' else '') + '\n</head>')
        source = source.replace('</title>',f' · {E(d["label"])}</title>')
        bar = f'<div class="edition-bar"><span>{E(d["label"])}</span><a href="./index.html#work">Back to selected work ↗</a></div>'
        source = source.replace('</header>', '</header>'+bar,1)
        if name == 'crossroads' and d.get('theme') == 'clay':
            source = source.replace('</div></section><section class="case-row" id="mac-check-in">', '</div></section><details class="omni-disclosure research-context"><summary>Research scope and evidence <span aria-hidden="true">+</span></summary><div class="research-scope"><p>This case documents my contribution to a team project and the connection between research, constraints and a design decision.</p><p>The original study plan, recruiting materials, participant counts and analysis outputs are not included in this portfolio. The outcome described here is qualitative staff feedback.</p></div></details><section class="case-row" id="mac-check-in">')
            source = source.replace('student check-in<br>', 'student <span class="no-wrap">check-in</span><br>')
            first = source.index('<section class="case-row" id="mac-check-in">')
            last = source.index('<figure class="case-feature-figure" id="attendance-interface">')
            context = source[first:last]
            source = source[:first] + '<details class="omni-disclosure research-context"><summary>Read the observation and constraints in full <span aria-hidden="true">+</span></summary><div class="research-context-body">' + context + '</div></details>' + source[last:]
            source = re.sub(r'(<figure class="(?:case-feature-figure|gallery-figure)"[^>]*>\s*)(<img\b[^>]*src="([^"]+)"[^>]*>)', lambda m: m[1] + '<a class="screenshot-link" data-screenshot href="' + m[3] + '" aria-label="Enlarge this research artifact">' + m[2] + '</a><p class="artifact-zoom-hint">Select the image to enlarge</p>', source)
        if d.get('theme') == 'clay':
            source = source.replace('loading="lazy"','loading="eager"')
        if name == 'crossroads' and d.get('theme') == 'clay':
            source = source.replace('<a class="screenshot-link" data-screenshot href="../../assets/element-attendance-layout.png"', '<a class="screenshot-link attendance-detail-window" data-screenshot data-zoom-focus-x="0.9" data-zoom-focus-y="0.31" data-viewer-caption="Element attendance. Recreated layout with sample data. Full layout." href="../../assets/element-attendance-layout.png"')
            source = source.replace('<figure class="case-feature-figure" id="attendance-interface">', '<figure class="case-feature-figure" id="attendance-interface"><div class="decision-artifact"><div class="decision-artifact-copy"><p class="artifact-eyebrow">The decision in the interface</p><h3>One action for the selected students.</h3><p>The staff-led flow brings the bulk sign-in action beside the attendance list.</p></div>')
            source = source.replace('</a><p class="artifact-zoom-hint">Select the image to enlarge</p>\n          <figcaption>Element attendance', '</a></div><p class="artifact-zoom-hint">Detail view. Select the image to inspect the full layout.</p>\n          <figcaption>Element attendance',1)
            source = source.replace('<a class="screenshot-link" data-screenshot href="../../assets/crossroads-scheduling-sketch-2018.webp"', '<a class="screenshot-link sketch-detail-window" data-screenshot data-zoom-focus-x="0.5" data-zoom-focus-y="0.43" href="../../assets/crossroads-scheduling-sketch-2018.webp"')
            source = source.replace('<nav class="case-shortcuts"', '<p class="scope-brief">Team research contribution · Qualitative feedback. Study-planning and recruitment records are not included.</p><nav class="case-shortcuts"',1)
        if name == 'taska' and d.get('theme') == 'clay':
            source = source.replace('<details class="omni-disclosure"><summary>Research and implementation evidence', '<details class="omni-disclosure" id="research-decisions"><summary>Research and implementation evidence',1)
            source = re.sub(r'<nav class="omni-contents"[^>]*>.*?</nav>', '<nav class="case-shortcuts" aria-label="Case study sections"><a href="#research-decisions">Research &amp; decisions</a><a href="#workflow">Workflow</a><a href="#control">Approval &amp; recovery</a><a href="#system">Design system</a><a href="#motion-reference">Portfolio motion reference</a></nav>', source, count=1)
        if d.get('theme') == 'clay':
            if name == 'pcx':
                end=source.index('</header>',source.index('<header class="case-header">'))+len('</header>')
                source=source[:end]+'<nav class="case-shortcuts" aria-label="Case study sections"><a href="#requirements">Requirements</a><a href="#ranking-detail">Task-ranking decision</a><a href="#gallery-title">Prototype views</a></nav>'+source[end:]
                source=source.replace('<h2 class="case-label">Resolve conflicting requirements.</h2>','<h2 class="case-label" id="requirements">Resolve conflicting requirements.</h2>')
                a=source.index('<nav class="case-next case-next-back"');b=source.index('</nav>',a)+len('</nav>')
                previous=source[a:b].replace('Crossroads Education</a>','Crossroads</a>')
                following='<nav class="case-next" aria-label="Next project"><p class="eyebrow">Next</p><a href="./taska.html">Taska <svg class="arrow-icon arrow-ne" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 18 18 6M7 6h11v11"/></svg></a></nav>'
                source=source[:a]+'<div class="case-pagination">'+previous+following+'</div>'+source[b:]
            source=source.replace('<nav class="case-shortcuts"','<nav class="case-shortcuts case-contents"')
            source=re.sub(r'(<nav class="case-shortcuts case-contents"[^>]*>)',r'\1<span class="case-contents-label">Explore this case</span>',source)
            if name == 'crossroads':
                a=source.index('<section class="case-row" id="modernized-interfaces">');b=source.index('<section class="case-row" id="artifacts">',a)
                segment=source[a:b].replace(' id="modernized-interfaces"','',1)
                source=source[:a]+'<details class="omni-disclosure interface-explorer" id="modernized-interfaces"><summary>Explore the updated interfaces <span aria-hidden="true">+</span></summary>'+segment+'</details>'+source[b:]
                marker='<a class="screenshot-link" data-screenshot href="../../assets/crossroads-team-workshop-2018.webp"'
                a=source.index(marker);b=source.index('</a>',a)+len('</a>')
                source=source[:a]+'<div class="workshop-evidence"><div class="workshop-note"><p class="artifact-eyebrow">Methods described in this case</p><h3>Review the structure before the screens.</h3><ul><li>Card sorting</li><li>Personas</li><li>User flows</li></ul><p>Used with the team to review information architecture before developing screens.</p></div>'+source[a:b]+'</div>'+source[b:]
                # Put the reading aid beside the original artifact, before a full-size inspection.
                a=source.index('<figure class="gallery-figure">',source.index('id="task-group-panel"'))
                b=source.index('</figure>',a)
                group=source[a:b]
                t=group.index('<div class="artifact-transcription">')
                transcription=group[t:]
                group=group[:t]
                photo_start=group.index('<a class="screenshot-link"')
                photo_end=group.index('</a>',photo_start)+len('</a>')
                photo=group[photo_start:photo_end]
                group=group[:photo_start]+'<div class="task-group-reading">'+transcription+photo+'</div>'+group[photo_end:]
                source=source[:a]+group+source[b:]
                needle='<a class="screenshot-link sketch-detail-window"'
                start=source.index(needle);end=source.index('</a>',start)
                pins='<span class="artifact-pin" style="--pin-x:18%" aria-hidden="true">01</span><span class="artifact-pin" style="--pin-x:48%" aria-hidden="true">02</span><span class="artifact-pin" style="--pin-x:82%" aria-hidden="true">03</span>'
                source=source[:end]+pins+source[end:]
        if d.get('theme') == 'clay':
            dates=d['case_timing']
            end=source.index('</header>',source.index('<header class="case-header">'))
            source=source[:end]+'<p class="case-timing">'+dates[name]+'</p>'+source[end:]
            source=source.replace('class="case-shortcuts case-contents"','class="case-shortcuts case-contents" id="case-sections" tabindex="-1"')
            source=source.replace('</body>','<a class="case-section-return" href="#case-sections" hidden>Case sections <span aria-hidden="true">↑</span></a></body>')
            if name == 'pcx':
                source=source.replace('data-screenshot href="../../assets/pcx-prototype-home.webp"','data-screenshot data-zoom-focus-x="0.55" data-zoom-focus-y="0.35" href="../../assets/pcx-prototype-home.webp"')
            if name == 'taska':
                source=source.replace('Authored research &amp; specifications','Technical research &amp; specifications')
                source=source.replace('id="motion-reference" open','id="motion-reference"')
                source=source.replace('<div class="gallery" data-tabs="portfolio-motion">','<p class="motion-purpose">Try the patterns used on this portfolio: clear selection, readable state changes and a return to your place after image inspection.</p><div class="gallery" data-tabs="portfolio-motion">')
                source=re.sub(r'(<p class="omni-note">Shared tokens:.*?</p>)',r'<details class="omni-disclosure motion-spec"><summary>Implementation timings <span aria-hidden="true">+</span></summary>\1</details>',source,count=1)

                a=source.index('<figure class="omni-hero">');b=source.index('</figure>',a)+len('</figure>')
                source=source[:a]+'<details class="omni-disclosure case-depth"><summary>Inspect the application preview <span aria-hidden="true">+</span></summary>'+source[a:b]+'</details>'+source[b:]
                source=source.replace('<details class="omni-disclosure" id="research-decisions">','<details class="omni-disclosure" id="research-decisions" open>')
                a=source.index('<figure class="case-feature-figure editorial-detail" id="recovery-detail">');b=source.index('</figure>',a)+len('</figure>')
                recovery=source[a:b];source=source[:a]+source[b:]
                at=source.index('<section class="omni-chapter" id="workflow">')
                source=source[:at]+recovery+source[at:]
                # The original motion examples sit inside the system chapter. Keep them
                # independently reachable after collapsing only that chapter's overview.
                ending='    </section>\n\n    <nav class="case-next case-next-back"'
                assert source.count(ending)==1, 'Taska final chapter boundary changed'
                source=source.replace(ending,'    <nav class="case-next case-next-back"',1)
                motion='<details class="omni-disclosure motion-reference"'
                at=source.index(motion)
                source=source[:at]+'</section>\n'+source[at:]
                chapters=[('workflow','Explore the five-step workflow','<section class="omni-chapter" id="control">'),('control','Inspect approval, recovery and memory','<section class="omni-chapter" id="system">'),('system','Explore the design system and mobile view','<details class="omni-disclosure motion-reference"')]
                for chapter,label,following in chapters:
                    marker='<section class="omni-chapter" id="'+chapter+'">'
                    a=source.index(marker);b=source.index(following,a)
                    part=source[a:b].replace(' id="'+chapter+'"','',1)
                    source=source[:a]+'<details class="omni-disclosure case-depth" id="'+chapter+'"><summary>'+label+' <span aria-hidden="true">+</span></summary>'+part+'</details>'+source[b:]
                depths={'Inspect the application preview':'1 screen', 'Explore the five-step workflow':'5 steps · 1 screen', 'Inspect approval, recovery and memory':'2 decisions · 1 screen', 'Explore the design system and mobile view':'Mobile view · Optional component library'}
                for label,depth in depths.items():
                    source=source.replace('<summary>'+label+' <span aria-hidden="true">+', '<summary><span class="depth-label">'+label+'<small>'+depth+'</small></span><span aria-hidden="true">+')
                source=re.sub(r'<a href="(../../assets/taska/[^"]+)"',r'<a data-zoom-focus-x="0.55" data-zoom-focus-y="0.4" href="\1"',source)
        if d.get('theme')=='clay':
            start=source.index('<header class="case-header">')+len('<header class="case-header">')
            meta=source.index('<dl class="case-meta',start)
            lead=source[start:meta]
            source=source[:start]+'<div class="case-opening"><div class="case-heading-copy">'+lead+'</div>'+decision_preview(name)+'</div>'+source[meta:]
        (out/f'{name}.html').write_text(source)
    (out/'concepts').mkdir(exist_ok=True)
    for name in ['attendance','mac-checkin']:
        source = (ROOT/'concepts'/f'{name}.html').read_text()
        source = source.replace('../work/crossroads.html','../crossroads.html')
        source = source.replace('../assets/','../../../assets/')
        for resource in ['ui.css','state.js','app.js']:
            source = source.replace('./'+resource,'../../../concepts/'+resource)
        (out/'concepts'/f'{name}.html').write_text(source)
    print(f'Built versions/{slug}/index.html')
    return d

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('slug',nargs='?'); args=p.parse_args()
    files=[ROOT/'variants'/f'{args.slug}.json'] if args.slug else sorted((ROOT/'variants').glob('*.json'))
    for config in files: build(config)
    variants=[json.loads(p.read_text()) for p in sorted((ROOT/'variants').glob('*.json'))]
    entries=''.join(f'<li><a href="./{E(d["slug"])}/index.html">{E(d["label"])}</a><p>Role-specific introduction, project emphasis and case-study context.</p></li>' for d in variants)
    catalog=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Portfolio editions | Ricky Sanderson</title><link rel="stylesheet" href="../styles.css"><style>main{{max-width:800px;margin:64px auto;padding:0 24px}}h1{{font-size:42px;letter-spacing:-.04em}}ul{{padding:0;list-style:none}}li{{padding:24px 0;border-top:1px solid #343437}}li a{{display:inline-flex;align-items:center;min-height:44px;font-size:22px;color:#ff479b}}p{{color:#aaa9a7;line-height:1.6}}a:focus-visible{{outline:2px solid #ff479b}}</style></head><body><main><p>Ricky Sanderson</p><h1>Portfolio editions</h1><p>Separate versions for different roles, with shared assets and a preserved general portfolio.</p><ul><li><a href="../index.html">General · Product &amp; UX design</a><p>The original portfolio, unchanged.</p></li>{entries}</ul></main></body></html>'''
    (ROOT/'versions/index.html').write_text(catalog)
