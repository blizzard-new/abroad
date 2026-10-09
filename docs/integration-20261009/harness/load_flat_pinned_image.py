"""Repackage the exact pinned rootfs as one layer without touching Docker settings.

Input comes from crane export by immutable digest. Original OCI config is kept
byte-for-byte as an object; only rootfs/history packaging metadata is replaced.
No file extraction into the host and no registry push occur.
"""
import copy
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile

root = Path('/workspace/integration-tools')
evidence = Path('/workspace/integration-evidence')
original = json.loads((evidence / 'pinned-supabase-image-config.json').read_text())
layer = root / 'supabase-pinned-rootfs.tar'
with layer.open('rb') as f:
    digest = hashlib.file_digest(f, 'sha256').hexdigest()
config = copy.deepcopy(original)
config['rootfs'] = {'type': 'layers', 'diff_ids': ['sha256:' + digest]}
config['history'] = [{'created': original.get('created'), 'created_by': 'Local exact pinned rootfs repack for VFS validation only'}]
assert config['config'] == original['config']
config_bytes = json.dumps(config, separators=(',', ':')).encode()
config_digest = hashlib.sha256(config_bytes).hexdigest()
tag = 'abroad-validation/supabase-pinned-flat:17.6.1.136'
manifest = [{'Config': config_digest + '.json', 'RepoTags': [tag], 'Layers': ['layer.tar']}]
with (evidence / 'pinned-image-flat-load.log').open('wb') as log:
    process = subprocess.Popen(['docker', 'load'], stdin=subprocess.PIPE, stdout=log, stderr=subprocess.STDOUT)
    with tarfile.open(fileobj=process.stdin, mode='w|') as tar:
        for name, data in [(config_digest + '.json', config_bytes), ('manifest.json', json.dumps(manifest).encode())]:
            info = tarfile.TarInfo(name); info.size = len(data); info.mode = 0o644
            tar.addfile(info, io.BytesIO(data))
        info = tarfile.TarInfo('layer.tar'); info.size = layer.stat().st_size; info.mode = 0o644
        with layer.open('rb') as f:
            tar.addfile(info, f)
    process.stdin.close()
    assert process.wait(timeout=180) == 0
inspection = json.loads(subprocess.check_output(['docker', 'image', 'inspect', tag]))[0]
assert inspection['Id'] == 'sha256:' + config_digest
assert inspection['RootFS']['Layers'] == ['sha256:' + digest]
for key, value in original['config'].items():
    if value is not None:
        assert inspection['Config'].get(key) == value, (key, inspection['Config'].get(key), value)
proof = {'source': 'supabase/postgres@sha256:f371b5f3f2ac0a05703f33d6e6134515fb2498cab708fb948a0aeb7481467c00',
         'platform': 'linux/amd64', 'original_layers': len(original['rootfs']['diff_ids']),
         'filesystem_sha256': digest, 'filesystem_tar_bytes': layer.stat().st_size,
         'local_image_id': inspection['Id'], 'local_image_tag': tag,
         'runtime_config_identical': True, 'config': original['config'],
         'changed': ['OCI rootfs layer packaging', 'OCI build history only'],
         'unchanged': ['root filesystem from pinned digest', 'database and extensions', 'entrypoint', 'environment', 'command', 'healthcheck', 'working directory', 'stop signal'],
         'docker_settings_changed': False, 'remote_registry_push': False}
(evidence / 'pinned-image-flat-proof.json').write_text(json.dumps(proof, indent=2) + '\n')
print(json.dumps(proof, indent=2), flush=True)
