#!/usr/bin/env python3
"""x15.0 immutable x14.0 predecessor, safe shutdown, and embedded metadata gate."""
from pathlib import Path
import hashlib,json,ast

PACKAGE=Path(__file__).resolve().parents[1]
ROOT=PACKAGE.parent
PREVIOUS=Path(__file__).with_name('x150-predecessor-fingerprints.json')
PKG=PACKAGE.name

def hash_file(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    orig=json.loads(PREVIOUS.read_text(encoding='utf-8'))['files']
    current={p.relative_to(ROOT).as_posix():hash_file(p) for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and not p.name.endswith(('.pyc','.pyo')) and p.name!='SOURCE_MANIFEST.sha256'}
    expected_old={k for k in orig if k!=PKG+'/SOURCE_MANIFEST.sha256'}
    assert expected_old<=current.keys(),f'Historical files missing: {sorted(expected_old-current.keys())}'
    allowed_changed={
        'README.md','suite-pythoine-component.json',
        PKG+'/__init__.py',PKG+'/app_constants.py',PKG+'/'+('maqaronydesk' if PKG=='maqarony_desk' else 'riqatonydesk')+'.json',
        PKG+'/widgets/main_window.py',PKG+'/docs/RELEASE_NOTES.md',PKG+'/docs/CHANGELOG.md',
        PKG+'/packaging/README.md',PKG+'/packaging/appimage/'+('maqaronydesk' if PKG=='maqarony_desk' else 'riqatonydesk')+'.desktop',
        PKG+'/packaging/appimage/io.github.brunonlinespace.'+('maqaronydesk' if PKG=='maqarony_desk' else 'riqatonydesk')+'.metainfo.xml',
        PKG+'/packaging/fedora/build-appimage.sh',PKG+'/packaging/fedora/test-appimage.sh',
        PKG+'/tools/release_check.py',
    }
    if PKG=='maqarony_desk':allowed_changed|={PKG+'/docs/BUILDING.md',PKG+'/docs/RELEASE_CHECKLIST.md'}
    changed={k for k in expected_old if orig[k]!=current[k]}
    assert changed<=allowed_changed,f'Unapproved predecessor changes: {sorted(changed-allowed_changed)}'
    new_files=set(current)-expected_old
    permitted_new={'desk-health-check.json',PKG+'/'+('tools' if PKG=='maqarony_desk' else 'qa')+'/x150-predecessor-fingerprints.json',PKG+'/'+('tools' if PKG=='maqarony_desk' else 'qa')+'/x150_shutdown_compatibility_qa.py'}
    if PKG=='riqatony_desk':permitted_new|={PKG+'/docs/RELEASE_CHECKLIST-x15.0.md',PKG+'/qa/x150_historical_replay_qa.py'}
    assert new_files==permitted_new,f'Unexpected new files: {sorted(new_files^permitted_new)}'
    t=(PACKAGE/'widgets/main_window.py').read_text(encoding='utf-8')
    old='        # Hide the large main hierarchy while retaining the small dialog.\n        self.editor_manager.dashboard.set_loading(False)\n        self.navigation.set_loading(False)\n'
    new='        # Hide the main hierarchy without rebuilding Dashboard cards on exit.\n        # The Dashboard is not becoming interactive on a successful close.\n        self.navigation.set_loading(False)\n'
    failure_old='        if not scan_stopped:\n            self._closing = False\n            closing_dialog.close()\n            self.centralWidget().show()\n'
    failure_new='        if not scan_stopped:\n            self._closing = False\n            closing_dialog.close()\n            # Shutdown was cancelled: restore the normal, usable Dashboard.\n            self.editor_manager.dashboard.set_loading(False)\n            self.centralWidget().show()\n'
    assert t.count(new)==1 and t.count(failure_new)==1 and old not in t and failure_old not in t
    previous=t.replace(new,old).replace(failure_new,failure_old)
    assert hashlib.sha256(previous.encode('utf-8')).hexdigest()==orig[PKG+'/widgets/main_window.py'], 'Production shutdown diff exceeds approved lines'
    ast.parse(t)
    import json as _json
    meta=_json.loads((ROOT/'desk-health-check.json').read_text(encoding='utf-8'))
    suite=_json.loads((ROOT/'suite-pythoine-component.json').read_text(encoding='utf-8'))
    assert meta['application']['version']==suite['version']=='1.0.0-x15.0'
    assert meta['application']['id']==('maqarony-desk' if PKG=='maqarony_desk' else 'riqatony-desk')
    assert meta['adapter']['id']==('maqarony-desk-v1' if PKG=='maqarony_desk' else 'riqatony-desk-v1')
    for rel,digest in meta['source_files'].items():
        assert hash_file(ROOT/rel)==digest, f'Stale compatibility fingerprint: {rel}'
    print('x15.0 shutdown, unchanged historical sources and embedded compatibility: OK')

if __name__=='__main__':main()
