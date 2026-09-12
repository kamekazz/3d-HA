from pathlib import Path
p=Path('frontend/js/environment.js');s=p.read_text();s=s.replace('  const far = x => L.yardN - 260', '  // Photo 05/06/11/13 show a small, unresolved opposite-bank vegetation band.\n  // This visual depth estimate is about 260 ft across, not a surveyed distance.\n  const far = x => L.yardN - 260',1);p.write_text(s)
