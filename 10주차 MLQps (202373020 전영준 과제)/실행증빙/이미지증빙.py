from pathlib import Path
import hashlib
import json
import subprocess
import zipfile

BASE=Path(__file__).resolve().parents[1]
CH=BASE/'practice/chapter10'
API=CH/'code/10-1-model-api'
E=BASE/'실행증빙'
def run(*args): return subprocess.check_output(args, text=True).strip()
info=json.loads(run('docker','image','inspect','ch10-model-api'))[0]
cid=run('docker','create','ch10-model-api')
try:
    subprocess.run(['docker','cp',cid+':/app/app.py',str(E/'image_app.py')],check=True)
    subprocess.run(['docker','cp',cid+':/app/export_info.json',str(E/'image_export_info.json')],check=True)
finally:
    subprocess.run(['docker','rm',cid],check=True)
raw=(API/'app.py').read_bytes()
assert raw==(E/'image_app.py').read_bytes()
assert (API/'model_export/export_info.json').read_bytes()==(E/'image_export_info.json').read_bytes()
lock=run('docker','run','--rm','--entrypoint','python','ch10-model-api','-m','pip','freeze')
(E/'container-requirements-lock.txt').write_text(lock+'\n',encoding='utf-8')
result={'image_id':info['Id'],'repo_tags':info['RepoTags'],'size_bytes':info['Size'],
        'host_app_sha256':hashlib.sha256(raw).hexdigest(),'container_app_sha256':hashlib.sha256((E/'image_app.py').read_bytes()).hexdigest(),
        'app_bytes_equal':True,'export_info_bytes_equal':True}
(E/'이미지검증.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
with zipfile.ZipFile(E/'MLflow_실행원본.zip','w',zipfile.ZIP_DEFLATED) as z:
    files=[CH/'data/output/mlflow.db']+list((CH/'mlruns').rglob('*'))+list((API/'model_export').rglob('*'))
    for p in files:
        if p.is_file(): z.write(p,p.relative_to(CH).as_posix())
print(json.dumps(result,ensure_ascii=False,indent=2))
