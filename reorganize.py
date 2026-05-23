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

target_re  = re.compile(r'J\d{4}[+-]\d{4}')
band_re    = re.compile(r'(L_band|S_band|C_band|X_band|Ku_band|K_band|Ka_band|Q_band)')
pointing_re = re.compile(r'J\d{4}[+-]\d{4}_([A-Z]\d*)_sci')

moved = 0
skipped = 0
created_dirs = set()

for pipeline_dir in sorted(BASE.rglob("imaging_pipeline.*")):
    if not pipeline_dir.is_dir():
        continue

    fits_files = list(pipeline_dir.glob("*.pbcor.tt0.fits"))
    if not fits_files:
        print(f"WARNING: no .pbcor.tt0.fits in {pipeline_dir.relative_to(BASE)} — skipping")
        skipped += 1
        continue

    fname = fits_files[0].name
    t_match = target_re.search(fname)
    b_match = band_re.search(fname)
    p_match = pointing_re.search(fname)

    if not t_match or not b_match or not p_match:
        print(f"WARNING: could not parse target/band/pointing from {fname} — skipping")
        skipped += 1
        continue

    target   = t_match.group()
    band     = b_match.group()
    pointing = p_match.group(1)

    dest_dir = BASE / target / band / pointing
    dest_dir.mkdir(parents=True, exist_ok=True)
    created_dirs.add(dest_dir)

    dest = dest_dir / pipeline_dir.name
    if pipeline_dir == dest:
        continue

    shutil.move(str(pipeline_dir), str(dest))
    print(f"Moved  {pipeline_dir.relative_to(BASE)}")
    print(f"    →  {dest.relative_to(BASE)}/")
    moved += 1

print(f"\nDone: {moved} folders moved, {skipped} skipped.")
print("\nFolders created:")
for d in sorted(created_dirs):
    print(f"  {d.relative_to(BASE)}")
