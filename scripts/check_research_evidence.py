#!/usr/bin/env python3
"""Guard the approved aggregate research presentation and its scope labels."""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
case=(ROOT/'versions/clay-ux-researcher/crossroads.html').read_text()
# These question-specific bases are deliberately kept separate.
attendance={'yes':264,'no':64}
duration={'less_than_one_hour':31,'about_one_hour':73,'more_than_one_hour':72,'multiple_hours':28}
assert sum(attendance.values())==328
assert sum(duration.values())==204
assert 87 >= 74 >= 34 >= 18
for fragment in (
    '<strong>328</strong>', '<strong>204</strong>',
    '34 <small>responses</small>', '18 <small>responses</small>',
    'Q8 had 87 response records; 74 had at least one assigned code.',
    'A response could receive multiple tags.',
    'not percentages of the full survey',
    'not a survey of Nexus product outcomes',
    'does not establish a shipped change or measured improvement',
    'These are measurement plans, not reported improvements.',
    'Two archived responses, paraphrased.',
    '<dt>Provide more tutors.</dt><dd>understaffed</dd>',
    '<dt>Add tables for busy periods.</dt><dd>space</dd>',
):
    assert fragment in case, f'Research evidence scope/count changed: {fragment}'
assert 'Study plans, recruiting materials, participant counts and analysis outputs are not included.' not in case
# Private research sources are never embedded or linked in the public edition.
for path in (ROOT/'versions/clay-ux-researcher').rglob('*.html'):
    content=path.read_text()
    assert not re.search(r'https?://(?:docs|drive)\.google\.com',content), f'Private source link: {path}'
print('PASS: question-specific totals, coded-count scope, recommendation/metric boundaries, no private Drive links.')
