#!/usr/bin/env python3
"""Package distributable source only; exclude private renders and dependencies."""
import argparse
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]
FILES=['SKILL.md','README.md','README.zh-CN.md','LICENSE','THIRD_PARTY_NOTICES.md',
       'CONTRIBUTING.md','CHANGELOG.md','package.json','package-lock.json','requirements.txt','.gitignore']
DIRS=['scripts','assets','agents','references','tests','examples','.github']
EXCLUDE={'__pycache__','.DS_Store'}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();target=args.output.resolve()
    if target.exists():parser.error('Output exists; choose a new archive name')
    files=[ROOT/p for p in FILES]
    for directory in DIRS:
        files.extend(p for p in (ROOT/directory).rglob('*') if p.is_file()
                     and not EXCLUDE.intersection(p.parts) and p.suffix not in ('.pyc','.log'))
    for p in files:
        if p.is_symlink() or not p.is_file():parser.error(f'Invalid release source: {p}')
    target.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(target,'x',zipfile.ZIP_DEFLATED) as archive:
        for p in sorted(files):archive.write(p,Path('printer-effect')/p.relative_to(ROOT))
    print(f'{target}: {len(files)} source/example files; generated output excluded')

if __name__=='__main__':main()
