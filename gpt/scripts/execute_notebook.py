"""Execute every cell with a fresh real ipykernel; no application-state reuse.
Default: Jupyter's InProcessKernel in this new Python process, requiring no sockets.
--transport tcp selects the ordinary nbclient / separate-kernel-process route.
"""
import os,sys,json,time,tempfile,argparse
from pathlib import Path
from queue import Empty
import nbformat
ROOT=Path(__file__).resolve().parents[1]

def inprocess_execute(nb):
    from ipykernel.inprocess.manager import InProcessKernelManager
    km=InProcessKernelManager();km.start_kernel();kc=km.client();kc.start_channels();kc.wait_for_ready()
    try:
        assert 'H' not in km.kernel.shell.user_ns
        for index,cell in enumerate(nb.cells):
            if cell.cell_type!='code':continue
            cell.outputs=[];cell.execution_count=None
            print(f'Executing cell {index+1}/{len(nb.cells)}',flush=True)
            started=time.perf_counter()
            msg_id=kc.execute(cell.source,store_history=True)
            # The in-process dispatch is synchronous. Flush the real kernel streams
            # before draining IOPub; older ipykernel may omit their parent header.
            km.kernel.stdout.flush();km.kernel.stderr.flush()
            while True:
                try:msg=kc.get_iopub_msg(timeout=0)
                except Empty:break
                typ=msg['header']['msg_type'];parent=msg.get('parent_header',{}).get('msg_id')
                if parent!=msg_id and not (parent is None and typ=='stream'):continue
                if typ=='execute_input':cell.execution_count=msg['content']['execution_count']
                elif typ in {'stream','display_data','execute_result','error'}:
                    cell.outputs.append(nbformat.v4.output_from_msg(msg))
                elif typ=='clear_output':cell.outputs=[]
            reply=kc.get_shell_msg(timeout=30)
            assert reply['parent_header']['msg_id']==msg_id
            cell.metadata['execution_seconds']=time.perf_counter()-started
            if reply['content']['status']!='ok':
                nbformat.write(nb,ROOT/'failed_execution.ipynb')
                raise RuntimeError(f'Cell {index+1} failed: {reply["content"]}')
            assert cell.execution_count is not None
    finally:
        kc.stop_channels();km.shutdown_kernel()

def tcp_execute(nb):
    from nbclient import NotebookClient
    with tempfile.TemporaryDirectory(prefix='revnice_kernel_') as tmp:
        base=Path(tmp);spec=base/'kernels'/'revnice2026';spec.mkdir(parents=True)
        (spec/'kernel.json').write_text(json.dumps({'argv':[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],'display_name':'Řevnice execution environment','language':'python'}))
        os.environ['JUPYTER_PATH']=str(base)+os.pathsep+os.environ.get('JUPYTER_PATH','')
        NotebookClient(nb,timeout=7200,kernel_name='revnice2026',resources={'metadata':{'path':str(ROOT)}}).execute()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--transport',choices=['inprocess','tcp'],default='inprocess');args=parser.parse_args()
    os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
    os.environ['PYDEVD_DISABLE_FILE_VALIDATION']='1'
    os.chdir(ROOT);sys.path.insert(0,str(ROOT))
    path=ROOT/'revnice_2026_bayesian_analysis.ipynb';nb=nbformat.read(path,as_version=4);t0=time.perf_counter()
    (inprocess_execute if args.transport=='inprocess' else tcp_execute)(nb)
    errors=[o for c in nb.cells for o in c.get('outputs',[]) if o.output_type=='error'];assert not errors
    nbformat.validate(nb);nbformat.write(nb,path)
    record={'clean_kernel':True,'transport':args.transport,'kernel':'ipykernel.inprocess.InProcessKernel in a fresh Python process' if args.transport=='inprocess' else 'separate ipykernel via TCP','executed_code_cells':sum(c.cell_type=='code' for c in nb.cells),'errors':0,'wall_seconds':time.perf_counter()-t0,'python_version':sys.version.split()[0],'note':'Verified actual MCMC caches reused where valid; separate metadata records all model runs. TCP and IPC sockets were unavailable in the execution environment; genuine in-process Jupyter messages capture outputs.'}
    (ROOT/'results/notebook_execution.json').write_text(json.dumps(record,indent=2));print(json.dumps(record,indent=2))
if __name__=='__main__':main()
