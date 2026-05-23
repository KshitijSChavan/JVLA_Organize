import re
import sys
import shutil
from pathlib import Path

if len(sys.argv) != 2:
    print("Usage: python reorganize.py <base_folder>")
    print("Example: python reorganize.py 24A-164/")
    sys.exit(1)

BASE = Path(sys.argv[1]).resolve()
if not BASE.is_dir():
    print(f"ERROR: '{BASE}' is not a directory.")
    sys.exit(1)

target_re = re.compile(r'J\d{4}[+-]\d{4}')
band_re   = re.compile(r'(L_band|S_band|C_band|X_band|Ku_band|K_band|Ka_band|Q_band)')

moved = 0
skipped = 0

for pipeline_dir in sorted(BASE.glob("imaging_pipeline.*")):
    if not pipeline_dir.is_dir():
        continue

    fits_files = list(pipeline_dir.glob("*.pbcor.tt0.fits"))
    if not fits_files:
        print(f"WARNING: no .pbcor.tt0.fits in {pipeline_dir.name} — skipping")
        skipped += 1
        continue

    fname = fits_files[0].name
    t_match = target_re.search(fname)
    b_match = band_re.search(fname)

    if not t_match or not b_match:
        print(f"WARNING: could not parse target/band from {fname} — skipping")
        skipped += 1
        continue

    target = t_match.group()
    band   = b_match.group()

    dest_dir = BASE / target / band
    dest_dir.mkdir(parents=True, exist_ok=True)

    dest = dest_dir / pipeline_dir.name
    shutil.move(str(pipeline_dir), str(dest))
    print(f"Moved {pipeline_dir.name}  →  {target}/{band}/")
    moved += 1

print(f"\nDone: {moved} folders moved, {skipped} skipped.")
