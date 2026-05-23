import io
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

target_re   = re.compile(r'J\d{4}[+-]\d{4}')
band_re     = re.compile(r'EVLA_([A-Z]+)')
pointing_re = re.compile(r'J\d{4}[+-]\d{4}_(\S+)')

def get_listobs_text(folder):
    # Try extracted weblog first
    for f in folder.rglob("listobs.txt"):
        return f.read_text(errors="ignore")
    # Try weblog.tgz directly or nested one level down
    wlog = next(folder.rglob("weblog.tgz"), None)
    if wlog:
        try:
            with tarfile.open(wlog, "r:gz") as tf:
                for member in tf.getmembers():
                    if member.name.endswith("listobs.txt"):
                        f = tf.extractfile(member)
                        if f:
                            return f.read().decode(errors="ignore")
        except Exception as e:
            print(f"  WARNING: could not read {wlog}: {e}")
    # Try double-nested: outer .tar.gz -> weblog.tgz -> listobs.txt
    for outer in folder.glob("*.tar.gz"):
        try:
            with tarfile.open(outer, "r:gz") as tf:
                wm = next((m for m in tf.getmembers() if m.name == "weblog.tgz"), None)
                if not wm:
                    continue
                wdata = tf.extractfile(wm).read()
            with tarfile.open(fileobj=io.BytesIO(wdata), mode="r:gz") as wf:
                lm = next((m for m in wf.getmembers() if m.name.endswith("listobs.txt")), None)
                if lm:
                    return wf.extractfile(lm).read().decode(errors="ignore")
        except Exception as e:
            print(f"  WARNING: could not read {outer}: {e}")
    return None

moved = 0
skipped = 0
created_dirs = set()

for entry in sorted(BASE.iterdir()):
    if not entry.is_dir():
        continue
    if entry.name in SKIP:
        continue
    if ".sb" not in entry.name or ".eb" not in entry.name:
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

    # Collect all unique pointing IDs from OBSERVE_TARGET lines
    pointings = set()
    for line in text.splitlines():
        if "OBSERVE_TARGET" in line:
            m = pointing_re.search(line)
            if m:
                pointings.add(m.group(1))

    # If BASE already sits inside the target/band tree, don't re-append them
    base_parts = BASE.parts
    already_in_target_band = target in base_parts and band in base_parts

    single_pointing = len(pointings) == 1
    if already_in_target_band:
        dest_dir = BASE / pointings.pop() if single_pointing else BASE
    else:
        dest_dir = BASE / target / band / pointings.pop() if single_pointing else BASE / target / band

    dest = dest_dir / entry.name
    if dest == entry:
        continue  # already in the right place

    dest_dir.mkdir(parents=True, exist_ok=True)
    created_dirs.add(dest_dir)
    shutil.move(str(entry), str(dest))
    print(f"Moved  {entry.name}")
    print(f"    →  {dest.relative_to(BASE)}/")
    moved += 1

print(f"\nDone: {moved} folders moved, {skipped} skipped.")
print("\nFolders created:")
for d in sorted(created_dirs):
    print(f"  {d}")
