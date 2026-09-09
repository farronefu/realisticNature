"""Download CC0 assets with source metadata. No account credentials required."""
import json, urllib.request, hashlib, shutil, argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'assets'; ASSETS.mkdir(exist_ok=True)
HEADERS={'User-Agent':'realisticNature scene study / 1.0'}
def request(url):
    return urllib.request.urlopen(urllib.request.Request(url,headers=HEADERS),timeout=120)
def fetch(job):
    asset,rel,spec=job
    dest=ASSETS/asset/rel; dest.parent.mkdir(parents=True,exist_ok=True)
    if not dest.exists() or dest.stat().st_size!=spec['size']:
        with request(spec['url']) as r, open(dest,'wb') as f: shutil.copyfileobj(r,f)
    print('ASSET',asset,rel,flush=True)
    return {'asset':asset,'path':str(dest.relative_to(ROOT)).replace('\\','/'),'url':spec['url'],'bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'license':'CC0-1.0','source':'https://polyhaven.com/a/'+asset}
def main():
    p=argparse.ArgumentParser();p.add_argument('--extra-only',action='store_true');a=p.parse_args()
    models={'pine_roots':'2k'}
    if not a.extra_only: models.update({'fern_02':'4k','rock_moss_set_01':'4k','dead_tree_trunk':'4k','shrub_04':'4k','fir_tree_01':'2k','moss_01':'2k'})
    jobs=[]
    for asset,res in models.items():
        with request('https://api.polyhaven.com/files/'+asset) as r: d=json.load(r)
        spec=d['blend'][res]['blend'];jobs.append((asset,asset+'_'+res+'.blend',spec))
        jobs.extend((asset,k,v) for k,v in spec['include'].items())
    for asset,channels in {'forest_leaves_02':['diff','nor_gl','rough','disp'],'bark_brown_01':['diff','nor_dx','rough']}.items():
        if not channels: continue
        with request('https://api.polyhaven.com/files/'+asset) as r: d=json.load(r)
        for ch in channels:
            key=next(k for k in d if k.lower() in (ch,'diffuse' if ch=='diff' else ch,'displacement' if ch=='disp' else ch))
            fmt='png' if ch=='disp' else 'jpg'
            spec=d[key]['4k'].get(fmt) or next(iter(d[key]['4k'].values()))
            jobs.append((asset,asset+'_'+ch+'_4k.'+spec['url'].split('.')[-1],spec))
    asset='forest_slope'
    with request('https://api.polyhaven.com/files/'+asset) as r: d=json.load(r)
    spec=d['hdri']['4k']['hdr'];jobs.append((asset,'forest_slope_4k.hdr',spec))
    with ThreadPoolExecutor(max_workers=4) as pool: result=list(pool.map(fetch,jobs))
    (ROOT/'docs').mkdir(exist_ok=True)
    (ROOT/'docs'/'download_manifest.json').write_text(json.dumps(result,indent=2))
if __name__=='__main__': main()
