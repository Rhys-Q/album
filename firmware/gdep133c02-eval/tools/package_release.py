#!/usr/bin/env python3
"""Build, test, then package the local ESP-IDF 6.1 evaluation firmware. Never flashes."""
import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
BUILD = ROOT / 'build/idf6.1'
OUT = ROOT / 'releases/eval-v0.1'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(argv, env=None):
    result = subprocess.run(argv, cwd=ROOT, env=env, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if result.returncode:
        print(result.stdout)
        raise SystemExit(f'Failed: {argv}; existing release retained')
    return result.stdout


def main():
    build_log = run(['bash', 'tools/idf.sh', 'build'])
    env = dict(os.environ)
    env['PATH'] = str(ROOT / '.venv/bin') + os.pathsep + env['PATH']
    tests_log = run(['bash', 'tools/test.sh'], env=env)
    description = json.loads((BUILD / 'project_description.json').read_text())
    idf = Path(description['idf_path'])
    commit = run(['git', '-C', str(idf), 'rev-parse', 'HEAD']).strip()
    if commit != 'fff9895c82d744c7237be8847347bdd1b07c6643':
        raise SystemExit('Unexpected IDF checkout')
    config = (ROOT / 'sdkconfig').read_text()
    for required in ['CONFIG_IDF_TARGET="esp32s3"', 'CONFIG_ESPTOOLPY_FLASHSIZE_8MB=y',
                     'CONFIG_SPIRAM_MODE_OCT=y', 'CONFIG_ESP_CONSOLE_UART_BAUDRATE=115200']:
        if required not in config:
            raise SystemExit(f'Missing config: {required}')
    stage = ROOT / 'build/release-stage'
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    for name in ['bootloader/bootloader.bin', 'partition_table/partition-table.bin',
                 'gdep133c02_eval.bin', 'gdep133c02_eval.elf', 'flash_args', 'flasher_args.json']:
        target = stage / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(BUILD / name, target)
    for name in ['README.md', 'sdkconfig', 'sdkconfig.defaults', 'partitions.csv']:
        shutil.copy2(ROOT / name, stage / name)
    (stage / 'build.log').write_text(build_log)
    (stage / 'tests.log').write_text(tests_log)
    (stage / 'python-packages-photo.txt').write_text(run([str(ROOT/'.venv/bin/python'), '-m', 'pip', 'freeze']))
    idf_python = description.get('python') or str(Path.home()/'.espressif/tools/python/v6.1/venv/bin/python')
    (stage / 'python-packages-idf.txt').write_text(run([idf_python, '-m', 'pip', 'freeze']))
    shutil.copytree(ROOT / 'docs', stage / 'docs')
    (stage / 'FLASH.md').write_text('''# 预编译包烧录

本包来自 ESP-IDF v6.1；只适用于 README 中接线的 N8R8 评估板。
先断开屏幕 J1 电源；选择 CH343 串口，禁止刷新中烧录。

在已激活的本机 IDF v6.1 终端，进入本目录运行：

```bash
python -m esptool --chip esp32s3 --port /dev/cu.usbserial-实际端口 --baud 460800 --before default-reset --after hard-reset write-flash @flash_args
```

偏移以 flash_args 为准：bootloader=0x0、分区表=0x8000、app=0x10000。
串口115200；上电不刷新。完整操作见源工程 README.md；本包 README 是来源快照，其中构建脚本路径指源工程。
''')
    source_hashes = {}
    for path in sorted(ROOT.rglob('*')):
        relative = path.relative_to(ROOT)
        if not path.is_file() or any(p in {'build', 'releases', '.venv', '__pycache__'} for p in relative.parts):
            continue
        if path.name in {'sdkconfig', 'sdkconfig.old'}:
            continue
        source_hashes[str(relative)] = sha(path)
    hardware = REPO / 'hardware/pcb/gdep133c02-driver'
    hardware_hashes = {str(p.relative_to(REPO)): sha(p) for p in sorted(hardware.glob('*.kicad_*')) if p.suffix in {'.kicad_sch', '.kicad_pcb'}}
    manifest = {
        'generated_utc': datetime.now(timezone.utc).isoformat(),
        'idf_version': 'v6.1', 'idf_commit': commit, 'target': 'esp32s3',
        'source_base_git_commit': run(['git', 'rev-parse', 'HEAD']).strip(),
        'note': 'Source SHA256 records include uncommitted new firmware; not an existing Git release tag.',
        'software_checks': {'idf_build': 'PASS', 'host_c_asan_ubsan': 'PASS', 'python_tests': 'PASS'},
        'hardware_checks': 'NOT RUN; no board flashed or optical/electrical measurements performed',
        'sources_sha256': source_hashes, 'hardware_reference_sha256': hardware_hashes,
        'artifacts_sha256': {str(p.relative_to(stage)):sha(p) for p in sorted(stage.rglob('*')) if p.is_file()}
    }
    (stage / 'verification.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    OUT.parent.mkdir(parents=True, exist_ok=True)
    # Only replace this software package after build/tests and staging succeeded.
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(stage, OUT)
    print(f'Packaged {OUT}; software PASS, hardware NOT RUN')


if __name__ == '__main__':
    main()
