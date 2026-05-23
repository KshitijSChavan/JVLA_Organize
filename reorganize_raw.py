import re
import sys
import shutil
import tarfile
from pathlib import Path

if len(sys.argv) < 2:
    print("Usage: python reorganize_raw.py <base_folder>")
    print("Example: python reorganize_raw.py /media/chavank/Bumblebee/JVLA/")
    sys.exit(1)

BASE = Path(sys.argv[1]).resolve()
if not BASE.is_dir():
    print(f"ERROR: '{BASE}' is not a directory.")
    sys.exit(1)

SKIP = {"images"}

target_re = re.compile(r'J\d{4}[+-]\d{4}')
band_re   = re.compile(r'EVLA_([A-Z]+)')

def get_listobs_text(folder):
    # Try extracted weblog first
    for f in folder.rglob("listobs.txt"):
        return f.read_text(errors="ignore")
    # Try weblog.tgz
    wlog = folder / "weblog.tgz"
    if not wlog.exists():
        wlog_inner = next(folder.rglob("weblog.tgz"), None)
        if wlog_inner:
            wlog = wlog_inner
    if wlog and wlog.exists():
        try:
            with tarfile.open(wlog, "r:gz") as tf:
                for member in tf.getmembers():
                    if member.name.endswith("listobs.txt"):
                        f = tf.extractfile(member)
                        if f:
                            return f.read().decode(errors="ignore")
        except Exception as e:
            print(f"  WARNING: could not read {wlog}: {e}")
    return None

moved = 0
skipped = 0
created_dirs = set()

for entry in sorted(BASE.iterdir()):
    if not entry.is_dir():
        continue
    if entry.name in SKIP:
        continue

    text = get_listobs_text(entry)
    if not text:
        print(f"WARNING: no listobs.txt found in {entry.name} — skipping")
        skipped += 1
        continue

    # Extract target from OBSERVE_TARGET lines
    target = None
    for line in text.splitlines():
        if "OBSERVE_TARGET" in line:
            m = target_re.search(line)
            if m:
                target = m.group()
                break

    # Extract band from first SPW name (EVLA_X, EVLA_C, etc.)
    band = None
    for line in text.splitlines():
        m = band_re.search(line)
        if m:
            band = m.group(1) + "_band"
            break

    if not target or not band:
        print(f"WARNING: could not parse target/band for {entry.name} — skipping")
        skipped += 1
        continue

    dest_dir = BASE / target / band
    dest_dir.mkdir(parents=True, exist_ok=True)
    created_dirs.add(dest_dir)

    dest = dest_dir / entry.name
    shutil.move(str(entry), str(dest))
    print(f"Moved  {entry.name}")
    print(f"    →  {target}/{band}/")
    moved += 1

print(f"\nDone: {moved} folders moved, {skipped} skipped.")
print("\nFolders created:")
for d in sorted(created_dirs):
    print(f"  {d}")
