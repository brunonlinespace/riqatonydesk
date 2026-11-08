#!/usr/bin/env python3
"""Execute actual Fedora desktop/AppStream validators before a costly freeze.

Use correct public WM class, keep version/MIME checks, and reject mutated
source metadata. The builder's original source can be reconstructed exactly.
"""
from pathlib import Path
import hashlib,os,subprocess,tempfile
P=Path(__file__).resolve().parents[1]
b=P/'packaging/fedora/build-appimage.sh'
d=P/'packaging/appimage/riqatonydesk.desktop'
a=P/'packaging/appimage/io.github.brunonlinespace.riqatonydesk.metainfo.xml'
s=b.read_text(encoding='utf8')
assert 'validate_desktop_entry_basic "$APPIMAGE_PAYLOAD/riqatonydesk.desktop"' in s
assert 'validate_appstream_basic "$APPIMAGE_PAYLOAD/${APPSTREAM_ID}.metainfo.xml"' in s
assert 'assert values.get("StartupWMClass") == "RiqatonyDesk"' in s
assert 'if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then' in s
# The requested packaging fix has no side effects beyond these 3 changes and edition.
predecessor=s.replace('APP_VERSION="1.0.0"','APP_VERSION="1.0.0-x19.8"')
predecessor=predecessor.replace('    validate_desktop_entry_basic "$APPIMAGE_PAYLOAD/riqatonydesk.desktop"\n    validate_appstream_basic "$APPIMAGE_PAYLOAD/${APPSTREAM_ID}.metainfo.xml"\n','')
predecessor=predecessor.replace('assert values.get("StartupWMClass") == "RiqatonyDesk"','assert values.get("StartupWMClass") == "riqatonydesk"')
predecessor=predecessor.replace('if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then\n    main "$@"\nfi\n','main "$@"\n')
assert hashlib.sha256(predecessor.encode('utf8')).hexdigest()=="8a71a16cf28580467a2f7fed1bcacd57b9ba2b508fc1368ec6fc7b4957e47c58",'Builder changed beyond three approved corrections and version'
# Source the real shell functions; no venv/pip/Qt/build needed.
cmd=['bash','-c','source "$1"; validate_desktop_entry_basic "$2"; validate_appstream_basic "$3"','bash',str(b),str(d),str(a)]
base_env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
def run(desk,xml=a):
    proc=subprocess.run(cmd[:5]+[str(desk),str(xml)],env=base_env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=30)
    return proc
positive=run(d)
assert positive.returncode==0,(positive.stdout,positive.stderr)
# Exercise the complete real source preflight as it will be used before venv.
preflight=subprocess.run(['bash','-c','source "$1"; check_inputs','bash',str(b)],
    env={**base_env,'RIQATONYDESK_ALLOW_ROOT_BUILD':'1','RIQATONYDESK_ALLOW_UNSUPPORTED_HOST':'1'},
    stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=30)
assert preflight.returncode==0,(preflight.stdout,preflight.stderr)
with tempfile.TemporaryDirectory(prefix='riqatony-desk-appdir-check-') as tmp:
    text=d.read_text(encoding='utf8')
    for key, mutation in [('wrong WM class','StartupWMClass=riqatonydesk'),('wrong version','X-AppImage-Version=1.0.0-x19.9')]:
        p=Path(tmp)/'bad.desktop'
        target='StartupWMClass=RiqatonyDesk' if key=='wrong WM class' else 'X-AppImage-Version=1.0.0'
        assert text.count(target)==1
        p.write_text(text.replace(target,mutation),encoding='utf8')
        result=run(p)
        assert result.returncode!=0,f'Failed to reject {key}'
print('PASS x19.9: actual AppImage builder desktop/AppStream validators and negative metadata mutations')
