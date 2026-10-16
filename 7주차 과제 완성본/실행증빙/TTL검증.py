"""원본 실습 실행 후 추가 조회만 수행한다. 4일 실패 조건은 기준 시점으로 모사한다."""
from pathlib import Path
from datetime import datetime, timezone
import json
import pandas as pd
from feast import FeatureStore

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / 'practice/chapter7/data/output'
store = FeatureStore(repo_path=str(OUT / 'feature_repo'))
svc = store.get_feature_service('complaint_model_v1')
as_of = datetime(2026, 7, 8, 9, tzinfo=timezone.utc)
keys = ['11440', '11620', '11680']
source = pd.read_parquet(OUT / 'complaint_daily_features.parquet')
latest_time = source.event_timestamp.max().to_pydatetime()
hist = store.get_historical_features(entity_df=pd.DataFrame({'lawd_cd': keys, 'event_timestamp': [as_of] * 3}), features=svc).to_df()
online = store.get_online_features(features=svc, entity_rows=[{'lawd_cd': k} for k in keys]).to_dict()
assert len(hist) == 0
assert dict(zip(online['lawd_cd'], online['complaint_count'])) == {'11440': 6, '11620': 5, '11680': 9}
assert all(round(v, 3) == 0.045 for v in online['day_unmapped_rate'])
result = {'scenario': '7월 4~7일 집계 공급 실패, 7월 8일 09:00 기준 시점으로 오프라인 조회; 온라인은 실제 실행 시각에 조회 (시계 조작 없음)',
          'as_of': as_of.isoformat(), 'latest_feature_timestamp': latest_time.isoformat(),
          'feature_age_hours_at_as_of': (as_of-latest_time).total_seconds()/3600,
          'ttl_hours': 72, 'historical_requested': 3, 'historical_returned': len(hist),
          'online_actual_query_time': datetime.now(timezone.utc).isoformat(), 'online': online,
          'PASS': True}
(BASE/'실행증빙/TTL검증결과.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps(result, ensure_ascii=False, indent=2))
