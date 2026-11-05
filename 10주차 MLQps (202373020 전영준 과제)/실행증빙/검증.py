"""실제 생성된 보고서·체크리스트·이미지 증빙을 대조한다 (실습 대체 아님)."""
from pathlib import Path
import hashlib
import json
import zipfile

BASE=Path(__file__).resolve().parents[1]
CH=BASE/'practice/chapter10'
OUT=CH/'data/output'
E=BASE/'실행증빙'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def main():
    report=OUT/'ch10_deploy_report.json'
    r=read(report)
    assert r['tests']['passed']==4
    assert r['bootstrap']==read(OUT/'ch10_bootstrap_summary.json')
    assert r['bootstrap']['fingerprint_matches_ch9'] is True
    assert r['bootstrap']['champion_version']==1 and r['bootstrap']['challenger_version']==2
    assert r['bootstrap']['export']['export_check_forecast']==6.0
    for name,source in [('host','registry-alias'),('container','local-dir')]:
        s=r[name]
        assert not s.get('skipped',False)
        assert s['predict_status']==200 and s['forecast']==6.0 and s['invalid_input_status']==422
        assert s['health']['status']=='ok' and s['health']['model_name']=='complaint_daily_forecaster'
        assert s['health']['model_version']=='1' and s['health']['model_source']==source
    assert r['host']['health']['shadow_enabled'] is True
    assert r['container']['health']['shadow_enabled'] is False
    assert r['consistency']=={'host_forecast':6.0,'container_forecast':6.0,'host_equals_container':True,'matches_ch9_forecast_6_0':True}
    assert r['shadow_observation']['champion_forecast']==6.0
    assert r['shadow_observation']['challenger_forecast']==round(81/11,4)
    checklist=read(OUT/'ch10_release_checklist.json')
    assert len(checklist)==8 and all(v is True for v in checklist.values())
    a=(CH/'code/10-1-model-api/app.py').read_bytes()
    assert a==(E/'image_app.py').read_bytes()
    sha=hashlib.sha256(a).hexdigest()
    image=read(E/'이미지검증.json')
    assert sha==image['host_app_sha256']==image['container_app_sha256']
    assert image['app_bytes_equal'] is True and image['export_info_bytes_equal'] is True
    export=read(E/'image_export_info.json')
    assert export['model_name']=='complaint_daily_forecaster' and export['champion_version']==1
    assert export['exported_from']=='models:/complaint_daily_forecaster@champion'
    with zipfile.ZipFile(E/'MLflow_실행원본.zip') as z:
        assert z.testzip() is None
        assert 'data/output/mlflow.db' in z.namelist()
    assert 'CH10_RUN_PASS' in (E/'run.log').read_text(encoding='utf-8')
    assert read(E/'GitHub실행.json')['conclusion']=='success'
    result={'status':'PASS','pytest_passed':4,'release_checks_passed':8,'host_forecast':6.0,'container_forecast':6.0,'invalid_input_status_both':422,'app_sha256':sha,'report_sha256':hashlib.sha256(report.read_bytes()).hexdigest()}
    (E/'검증결과.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
