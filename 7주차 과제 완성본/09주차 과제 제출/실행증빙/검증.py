from pathlib import Path
from fractions import Fraction
import csv
import hashlib
import json

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / 'practice/chapter9/data/output'

def main():
    r = json.loads((OUT/'ch9_experiment_report.json').read_text(encoding='utf-8'))
    promotion = json.loads((OUT/'ch9_promotion_record.json').read_text(encoding='utf-8'))
    pairs = r['training_pairs']
    assert len(pairs) == 6
    x = [Fraction(p['x_prev_count']) for p in pairs]
    y = [Fraction(p['y_count']) for p in pairs]
    xm, ym = sum(x)/6, sum(y)/6
    slope = sum((a-xm)*(b-ym) for a,b in zip(x,y))/sum((a-xm)**2 for a in x)
    intercept = ym-slope*xm
    baseline = sum(abs(b-ym) for b in y)/6
    linear = sum(abs(b-(slope*a+intercept)) for a,b in zip(x,y))/6
    assert baseline == 1 and linear == Fraction(23,22)
    assert r['runs']['baseline_mean']['train_mae'] == float(baseline)
    assert r['runs']['linear']['train_mae'] == round(float(linear),4)
    assert r['reproducibility']['mae_equal'] and r['reproducibility']['coef_equal']
    assert r['reproducibility']['coef'] == {'slope':round(float(slope),4),'intercept':round(float(intercept),4)}
    assert r['registry']['champion_version'] == 1
    d1,d2=r['registry']['decisions']
    assert [d1['version'],d2['version']] == [1,2]
    assert all(d['metric_gate']=='train_mae <= 1.05' and d['metric_gate_pass'] for d in [d1,d2])
    assert d1['promoted'] is True and d2['promoted'] is False
    assert promotion['decisions'] == [d1,d2]
    assert r['serving_via_alias']=={'forecast':6.0,'input_prev_count':9.0}
    for name in ['baseline_mean','linear']:
        path=OUT/f'training_pairs_{name}.csv'
        assert hashlib.sha256(path.read_bytes()).hexdigest()==r['data_fingerprint_sha256']
        with path.open(encoding='utf-8',newline='') as f:
            rows=list(csv.DictReader(f))
        assert len(rows)==6
    assert 'CH9_RUN_PASS' in (BASE/'실행증빙/실행로그.txt').read_text(encoding='utf-8')
    assert json.loads((BASE/'실행증빙/실행상태.json').read_text(encoding='utf-8'))['exit_code']==0
    own = {'absolute_max':1.0,'min_improvement':.1,'v1_absolute_pass':baseline<=1,'v2_absolute_pass':linear<=1,'v2_improvement':float(baseline-linear),'v2_relative_pass':baseline-linear>=Fraction(1,10),'champion_version':1}
    result={'status':'PASS','independent_mae':{'baseline':str(baseline),'linear':str(linear)},'own_gate':own,'data_fingerprint':r['data_fingerprint_sha256'],'report_sha256':hashlib.sha256((OUT/'ch9_experiment_report.json').read_bytes()).hexdigest()}
    (BASE/'실행증빙/검증결과.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
