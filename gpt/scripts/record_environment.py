"""Record installed versions for the actual dependency closure, not unrelated runtime packages."""
from pathlib import Path
import sys,json,platform,importlib.metadata as md,datetime
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
ROOT=Path(__file__).resolve().parents[1]
queue=[Requirement(x).name for x in (ROOT/'requirements.txt').read_text().splitlines() if x.strip() and not x.startswith('#')]
seen={}
while queue:
 name=canonicalize_name(queue.pop())
 if name in seen:continue
 dist=md.distribution(name);seen[name]=dist.version
 for raw in dist.requires or []:
  r=Requirement(raw)
  if r.marker is None or r.marker.evaluate({'extra':''}):queue.append(r.name)
(ROOT/'requirements-lock.txt').write_text('# Actual dependency closure; Python 3.12, Linux x86-64.\n'+'\n'.join(f'{k}=={v}' for k,v in sorted(seen.items()))+'\n')
(ROOT/'environment_record.json').write_text(json.dumps({'recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'python':sys.version,'platform':platform.platform(),'machine':platform.machine(),'packages':dict(sorted(seen.items())),'numerical_threads':{'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1'},'sampler':'NumPy + SciPy + Numba, custom FFBS/Gibbs/Metropolis, four processes','optional_ui_qa':{'playwright':md.version('playwright') if md.packages_distributions().get('playwright') else None}},ensure_ascii=False,indent=2))
print('Recorded',len(seen),'dependencies')
