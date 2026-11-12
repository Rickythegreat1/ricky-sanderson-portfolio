#!/usr/bin/env python3
"""Build role editions without modifying the original portfolio or shared assets."""
import argparse, hashlib, html, json, re, subprocess, sys
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
      'crossroads':('01 / Crossroads Education','Research with the team.','Junior UX designer · 2017–2020','Original team workshop photograph · 2018','crossroads-team-workshop-2018.webp','0.5','0.5'),
      'pcx':('02 / PCx Career Path','Explain the order.','Requirements synthesis & prototyping','Decision diagram · Prototype uses mock data','pcx-prototype-home.webp','0.47','0.31'),
      'taska':('03 / Taska','A deliberate path to execution.','Independent interaction design','Interaction diagram · Runtime not connected','taska/workflow.webp','0.4','0.86')
    }
    label,decision,role,scope,asset,x,y=data[name]
    href=name+'.html' if home else '../../assets/'+asset
    source_caption={'crossroads':'Original Crossroads team workshop photograph, 2018.','pcx':'Original PCx frontend-prototype screenshot. Mock data; no backend.','taska':'Original Taska installation-preview screenshot. Illustrative workflow; runtime not connected.'}[name]
    source_alt={'crossroads':'Crossroads team reviewing grouped task notes around a table.','pcx':'PCx agent-day prototype showing ranked daily tasks, career stage and a task-ranking explanation.','taska':'Taska workflow editor with separate Save workflow and Review and run controls.'}[name]
    attrs='' if home else f' data-screenshot data-zoom-focus-x="{x}" data-zoom-focus-y="{y}" data-viewer-start="{'fit' if name=='crossroads' else '1'}" data-source-width="{1600 if name=='crossroads' else 1165}" data-source-alt="{E(source_alt)}" data-viewer-caption="{E(source_caption)}"'
    action='Read the '+('Crossroads Education' if name=='crossroads' else name.upper() if name=='pcx' else 'Taska')+' case' if home else 'Inspect the original source image'
    if name=='crossroads':
        graphic='<img class="original-preview-photo" src="../../assets/crossroads-team-workshop-2018.webp" width="1600" height="1069" alt="Original photograph of the Crossroads team reviewing grouped task notes around a table." loading="eager">'
    elif name=='pcx':
        graphic='<div class="ranking-diagram"><p class="diagram-label">Proposed task order</p><ol><li><span class="rank-number">01</span><span><strong>Overdue</strong><small>Medium priority</small></span><span class="rank-marker" aria-hidden="true">↑</span></li><li><span class="rank-number">02</span><span><strong>Due today</strong><small>High priority</small></span></li></ol><p class="diagram-rule">Urgency before priority.</p></div>'
    else:
        graphic='<div class="workflow-diagram"><p class="diagram-label">Before a consequential action</p><ol><li><span class="flow-node" aria-hidden="true">1</span><span>Draft the workflow</span></li><li><span class="flow-node" aria-hidden="true">2</span><span>Review the specific action</span></li><li><span class="flow-node" aria-hidden="true">3</span><span>Approve it once</span></li></ol><p class="workflow-rule"><span aria-hidden="true">↳</span> Changed draft? Review again.</p></div>'
    return f'<figure class="decision-preview preview-{name}"><p class="preview-kicker">{E(label)}</p><p class="preview-role">{E(role)}</p><div class="preview-stage"><a class="preview-window decision-graphic graphic-{name}" href="{href}"{attrs} aria-label="{E(action)}">{graphic}<span class="graphic-action">'+('Read case' if home else 'Inspect source')+f' <span aria-hidden="true">↗</span></span></a></div><figcaption><strong>{E(decision)}</strong><span>{E(scope)}</span></figcaption></figure>'

def version_assets(markup):
    """Keep returning visitors on matching edition CSS/JS after a Pages update."""
    for asset in ('clay.css','clay.js','clay-case.js'):
        stamp=hashlib.sha256((ROOT/'versions'/asset).read_bytes()).hexdigest()[:12]
        markup=markup.replace('/'+asset+'"','/'+asset+'?v='+stamp+'"')
    return markup

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
    values['methods'] = '\n'.join(f'<article class="method-card"><h3>{E(m["title"])}</h3><p>{E(m["copy"])}</p><a href="{E(m["link"])}">Explore ↗</a></article>' for m in d['methods'])
    values['supporting'] = '\n'.join(f'''<article class="support-card">{decision_preview(p['link'].removesuffix('.html'),home=True)}<h3><a href="{E(p['link'])}">{E(p['name'])}</a></h3><p class="support-copy">{E(p['copy'])}</p><a class="read-case" href="{E(p['link'])}">Read the case <span aria-hidden="true">↗</span></a>{inspector(p)}</article>''' for p in d['supporting'])
    home = Template((ROOT/'templates/role-home.html').read_text()).substitute(values)
    if d.get('theme') == 'clay': home = home.replace('</head>', '<link rel="stylesheet" href="../clay.css"><script src="../clay.js" defer></script></head>')
    (out/'index.html').write_text(version_assets(home))
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
            source = source.replace('</div></section><section class="case-row" id="mac-check-in">', '</div></section><details class="omni-disclosure research-context"><summary>Research scope and evidence <span aria-hidden="true">+</span></summary><div class="research-scope"><p>Study plans, recruiting materials, participant counts and analysis outputs are not included. The result reported here is qualitative staff feedback, not a measured outcome.</p></div></details><section class="case-row" id="mac-check-in">')
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
            source = source.replace('<nav class="case-shortcuts"', '<p class="scope-brief">Team research contribution · Qualitative staff feedback.</p><nav class="case-shortcuts"',1)
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
                source=source[:a]+'<div class="workshop-evidence"><div class="workshop-note"><p class="artifact-eyebrow">Original team process</p><h3>The work behind the interface.</h3><p>The team reviewed grouped tasks before developing screens. The original scheduling sketch and selected notes follow below.</p></div>'+source[a:b]+'</div>'+source[b:]
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
            source=re.sub(r'(<nav class="case-shortcuts case-contents".*?</nav>)',r'\1<a class="case-section-return" href="#case-sections" hidden>Case sections <span aria-hidden="true">↑</span></a>',source,count=1,flags=re.S)
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
        if d.get('theme') == 'clay':
            if name == 'taska':
                source=re.sub(r'<section class="case-row" id="problem">.*?</section>', '',source,count=1,flags=re.S)
                a=source.index('<details class="omni-disclosure case-depth"><summary><span class="depth-label">Inspect the application preview')
                b=source.index('</details>',a)+len('</details>')
                preview=source[a:b];source=source[:a]+source[b:]
                at=source.index('<details class="omni-disclosure case-depth" id="workflow">')
                source=source[:at]+preview+source[at:]
                flow=re.search(r'<ol class="omni-flow" aria-label="Workflow sequence">.*?</ol>',source,re.S)
                if flow:
                    compact=flow[0].replace('class="omni-flow"','class="omni-flow compact-workflow"')
                    source=source[:flow.start()]+source[flow.end():]
                    at=source.index('<details class="omni-disclosure case-depth" id="workflow">')
                    source=source[:at]+'<section class="visible-workflow"><p class="artifact-eyebrow">The complete review cycle</p>'+compact+'</section>'+source[at:]
                source=source.replace('class="visible-workflow"','class="visible-workflow" id="workflow"').replace('class="omni-disclosure case-depth" id="workflow"','class="omni-disclosure case-depth" id="workflow-editor"')
                source=source.replace('Explore the five-step workflow','Inspect the workflow editor')
                source=source.replace('5 steps · 1 screen','Drafting details · 1 screen')
                source=source.replace('01 / Codex sub-harness','01 / Coding-task editor (Codex sub-harness)')
                source=source.replace('The Codex sub-harness lets users draft coding tasks','Taska’s coding-task editor, labeled “Codex sub-harness” in the application, lets users draft coding tasks')
                source=source.replace('<p>If an interruption makes the result unclear, the interface shows that uncertainty instead of offering a blind retry. This is intended to prevent the same change from being sent twice.</p>','')
                source=source.replace('Show when the result is uncertain. Check whether a change happened before sending the same action again.','Make recovery a distinct, reviewable interaction state.')
                source=source.replace('“An interrupted write is blocked from replay. Inspect the target and reconcile observed evidence.”','“An interrupted write is blocked from replay.”')
                source=source.replace('Visible rule in the interaction-state library.','Excerpt from the installation-preview state library. Inspect the source for the full rule.')
                source=source.replace('<p>Select any application screenshot to open its viewer. Closing returns you to the source image, with a brief focus cue so you can resume reading.</p>', '<p>Open the example, change the zoom, then close it to return here. Escape closes the viewer and returns focus.</p><a class="motion-inspection-demo" data-screenshot data-source-width="1165" data-source-alt="Taska interaction-state library with draft, approval, execution and recovery states." data-viewer-caption="Original Taska installation-preview state library. Runtime not connected." href="../../assets/taska/interaction-states.webp">Try image inspection <span aria-hidden="true">↗</span></a>')
                source=source.replace('<a class="screenshot-link recovery-detail-window"','<a class="screenshot-link recovery-detail-window source-thumbnail"')
                source=source.replace('This detail shows the recovery rule; select it to inspect all states. Runtime not connected.','Select the source thumbnail to inspect all states. Runtime not connected.')
            if name == 'pcx':
                source=re.sub(r'<section class="case-row">\s*<h2 class="case-label">Explain task ranking.</h2>.*?</section>', '', source,count=1,flags=re.S)
                source=source.replace('<p>“Why is this first?” makes the ranking explainable beside the recommended task.</p>', '<p>To answer the founder’s “What should I do today?”, I proposed urgency before priority, with “Why is this first?” explaining the rule.</p>')
                source=source.replace('<a class="screenshot-link" data-screenshot data-zoom-focus-x="0.55"', '<a class="screenshot-link agent-day-focus" data-screenshot data-viewer-start="1" data-zoom-focus-x="0.55"')
                source=source.replace('Original agent-day prototype <span aria-hidden="true">·</span> Mock data<br>', 'Original agent-day prototype <span aria-hidden="true">·</span> Mock data<br><span class="mobile-crop-note">Detail of the recommended task and its ranking explanation. Open to inspect the full screen.</span>')
                source=source.replace('<a class="screenshot-link pcx-detail-window"','<a class="screenshot-link pcx-detail-window source-thumbnail"')
                source=source.replace('Prototype detail · Mock data; no backend. Ranking labels annotate the shown rule. Select to inspect the full screen.','Original prototype screenshot · Mock data; no backend. Select the source thumbnail to inspect the full screen.')
            if name == 'crossroads':
                source=source.replace('<div><dt>Feedback</dt><dd>Staff responded positively. The documented outcome is qualitative; no measured time savings are claimed.</dd></div>', '<div id="feedback"><dt>Feedback</dt><dd>Staff responded positively. Interviews and weekly meetings with Learning Center Directors kept everyday issues and rollout plans in the process.</dd></div>')
                source=re.sub(r'<section class="case-row" id="feedback">.*?</section>', '',source, count=1, flags=re.S)
                source=source.replace('<section class="case-row" id="artifacts">\n          <h2 class="case-label">Other Crossroads work.</h2>\n          <div class="case-prose"><p>The workshop photos and scheduling sketch document our team process. The Nexus prototype shows search in a tutoring knowledge base.</p></div>\n        </section>', '<section class="case-row" id="artifacts"><h2 class="case-label" id="structure">Organize information with the team.</h2><div class="case-prose"><p>I used open, closed and hybrid card sorting, personas and user flows to review information architecture with the team before developing screens. The original notes and sketch below document staff information, hours and scheduling.</p></div></section>')
                source=re.sub(r'<section class="case-row" id="structure">.*?</section>', '',source, count=1, flags=re.S)
                source=source.replace('<div class="workshop-note"><p class="artifact-eyebrow">Original team process</p><h3>The work behind the interface.</h3><p>The team reviewed grouped tasks before developing screens. The original scheduling sketch and selected notes follow below.</p></div>', '')
                source=source.replace('class="workshop-evidence"','class="workshop-evidence workshop-photo"')
                source=re.sub(r'<figure class="case-feature-figure">\s*<div class="workshop-evidence workshop-photo">.*?<figcaption>Crossroads team workshop</figcaption>\s*</figure>', '',source,count=1,flags=re.S)
                source=source.replace('View the full-size sketch','Open the original sketch in a new tab ↗')
                source=source.replace('View the full-size task grouping','Open the original task grouping in a new tab ↗')
                source=source.replace('<a class="screenshot-link attendance-detail-window"','<a class="screenshot-link attendance-detail-window source-thumbnail"')
                source=source.replace('Detail view. Select the image to inspect the full layout.','Recreated interface. Select the source thumbnail to inspect the full layout.')
        if d.get('theme') == 'clay':
            source=source.replace('source-thumbnail" data-screenshot', 'source-thumbnail" data-screenshot data-viewer-start="1"')
        if name == 'pcx' and d.get('theme') == 'clay':
            source=source.replace('data-zoom-focus-x="0.55"','data-zoom-focus-x="0.37"').replace('data-zoom-focus-x="0.47"','data-zoom-focus-x="0.37"')
        if d.get('theme') == 'clay':
            source=source.replace(' data-viewer-start="1"','')
            if name=='crossroads':
                source=source.replace('>01 Task grouping</a>',' aria-label="01 Task grouping">01 Grouping</a>')
                source=source.replace('>02 Working notes</a>',' aria-label="02 Working notes">02 Notes</a>')
                source=source.replace('>03 Search prototype</a>',' aria-label="03 Search prototype">03 Search</a>')
                source=source.replace('The original notes and sketch below document staff information, hours and scheduling.','This related IA work covers staff scheduling and the Nexus knowledge base. The original notes and sketch follow below.')
            if name in ('pcx','taska'):
                question={'pcx':'Does urgency-first ordering help agents choose their next task, and can they explain why it was recommended?','taska':'Can people explain what an approval permits and recover confidently when an action’s result is uncertain?'}[name]
                marker='<div class="case-pagination">' if name=='pcx' else '<nav class="case-next case-next-back"'
                at=source.index(marker)
                source=source[:at]+'<aside class="open-research-question"><p>Open research question</p><h2>'+question+'</h2><span>This is a question for future validation, not a study result.</span></aside>'+source[at:]
        (out/f'{name}.html').write_text(version_assets(source))
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
