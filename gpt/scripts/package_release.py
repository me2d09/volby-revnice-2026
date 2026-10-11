"""Validate and package the completed project and the executed notebook separately."""
from pathlib import Path
import json,hashlib,zipfile,shutil
import nbformat
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT.parent/'deliverables'
EXCLUDED={'.git','.venv','__pycache__','.pytest_cache','.ipynb_checkpoints'}
def included(p):
 return not any(v in EXCLUDED for v in p.relative_to(ROOT).parts) and p.suffix not in {'.log','.pyc','.nbc','.nbi','.tmp'} and not p.name.startswith('pilot') and p.name not in {'ui_desktop.png','ui_mobile.png'}
def main():
 nbpath=ROOT/'revnice_2026_bayesian_analysis.ipynb';nb=nbformat.read(nbpath,as_version=4)
 codes=[c for c in nb.cells if c.cell_type=='code'];assert all(c.execution_count is not None for c in codes)
 errors=[o for c in codes for o in c.get('outputs',[]) if o.output_type=='error'];assert not errors
 assert len(list((ROOT/'figures').glob('*.png')))==15
 assert len(list((ROOT/'figures').glob('*.svg')))==15
 assert len(list((ROOT/'interactive').glob('*.html')))==3
 assert json.loads((ROOT/'results/ui_smoke.json').read_text())['status']=='passed'
 assert json.loads((ROOT/'results/notebook_execution.json').read_text())['clean_kernel']
 files=sorted(p for p in ROOT.rglob('*') if p.is_file() and included(p) and p.name!='manifest_sha256.json')
 manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
 (ROOT/'manifest_sha256.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 files.append(ROOT/'manifest_sha256.json');DEST.mkdir(exist_ok=True)
 target=DEST/'revnice_2026_complete.zip'
 with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p in files:z.write(p,arcname='revnice_2026/'+str(p.relative_to(ROOT)))
 with zipfile.ZipFile(target) as z:
  assert z.testzip() is None
  for name,digest in manifest.items():assert hashlib.sha256(z.read('revnice_2026/'+name)).hexdigest()==digest
 shutil.copyfile(nbpath,DEST/nbpath.name)
 print(json.dumps({'files_in_zip':len(files),'zip_bytes':target.stat().st_size,'notebook_bytes':nbpath.stat().st_size,'executed_code_cells':len(codes),'errors':len(errors)},indent=2))
if __name__=='__main__':main()
