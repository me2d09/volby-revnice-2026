import argparse,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.experiments import execute_suite
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--force',action='store_true');args=p.parse_args()
 execute_suite(force=args.force)
