import argparse
import concurrent.futures
import hashlib
import json
import os
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path

DEST = Path(__file__).resolve().parents[1]
ROOT = DEST.parents[1]
EVIDENCE = DEST / '실행증빙'
EVIDENCE.mkdir(parents=True, exist_ok=True)
parser = argparse.ArgumentParser(description='API 연결 확인. 인증값과 요청 URL은 출력·저장하지 않습니다.')
parser.add_argument('--env-file', type=Path, help='사용자가 지정한 기존 키 설정 파일')
parser.add_argument('--service', choices=['all', 'airkorea', 'law'], default='all')
args = parser.parse_args()
config = {}
config_path = args.env_file or ROOT / '.env'
if not config_path.exists() and args.env_file is None:
    config_path = ROOT / '02_강의저장소/mlops_public/.env.example'
lines = config_path.read_text(encoding='utf-8-sig').splitlines() if config_path.exists() else []
for line in lines:
    if '=' in line and not line.lstrip().startswith('#'):
        k, v = line.split('=', 1)
        config[k.strip()] = v.strip().strip('\"').strip("'")

def call(service, key_name, endpoint, params):
    key = os.environ.get(key_name) or config.get(key_name, '')
    record = {'service': service, 'checked_at': datetime.now(timezone(timedelta(hours=9))).isoformat(), 'endpoint': endpoint, 'parameters_without_credentials': params.copy(), 'credential_variable': key_name, 'request_sent': False}
    if not key or any(x in key.lower() for x in ['your_', 'your-', '여기에', '발급받은']):
        record.update(success=False, error='missing_or_placeholder_credential')
        return record
    params['serviceKey' if service == 'airkorea' else 'OC'] = urllib.parse.unquote(key) if service == 'airkorea' else key
    try:
        record['request_sent'] = True
        req = urllib.request.Request(endpoint + '?' + urllib.parse.urlencode(params), headers={'User-Agent': 'week2-course-practice/1.0'})
        try:
            with urllib.request.urlopen(req, timeout=35) as resp:
                record['http_status'] = resp.status
                raw = resp.read()
        except urllib.error.HTTPError as exc:
            record['http_status'] = exc.code
            raw = exc.read()
        text = raw.decode('utf-8-sig', errors='replace')
        try:
            payload = json.loads(text)
        except ValueError:
            payload = None
        record['success'] = False
        if service == 'airkorea' and isinstance(payload, dict):
            response = payload.get('response', {})
            record['api_header'] = response.get('header', {})
            body = response.get('body', {})
            items = body.get('items', [])
            if record['http_status'] == 200 and response.get('header', {}).get('resultCode') == '00' and isinstance(items, list) and items:
                assert key not in text and urllib.parse.unquote(key) not in text
                path = DEST / 'practice/chapter2/data/input/airquality_seoul_live.json'
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
                record.update(success=True, station_count=len(items), total_count=body.get('totalCount'), event_times=sorted({x.get('dataTime', '') for x in items}), response_file=path.relative_to(DEST).as_posix(), response_sha256=hashlib.sha256(raw).hexdigest())
        elif service == 'law' and isinstance(payload, dict):
            result = payload.get('LawSearch', {})
            laws = result.get('law', [])
            if isinstance(laws, dict):
                laws = [laws]
            if record['http_status'] == 200 and laws:
                record.update(success=True, total_count=result.get('totalCnt'), laws=[{k: x.get(k) for k in ['법령명한글', '법령ID', '법령일련번호', '공포일자', '시행일자']} for x in laws])
            else:
                record['response_top_level_fields'] = list(payload)
                record['error_fields'] = {k: payload[k] for k in ['result', 'msg'] if k in payload}
        if not record['success']:
            try:
                node = ET.fromstring(text)
                fields = {tag: node.findtext('.//' + tag) for tag in ['returnReasonCode', 'returnAuthMsg', 'errMsg', 'resultCode', 'resultMsg'] if node.findtext('.//' + tag)}
                if fields:
                    record['error_fields'] = fields
            except ET.ParseError:
                record['error'] = 'response_not_recognized_as_success'
    except Exception as exc:
        record.update(success=False, error_type=type(exc).__name__)
    # Never write request URLs, OC values, or raw exception strings.
    safe = json.dumps(record, ensure_ascii=False)
    for secret in [key, urllib.parse.unquote(key)]:
        if secret:
            safe = safe.replace(secret, '[REDACTED]')
    return json.loads(safe)

with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    services = [
        ('airkorea', 'DATA_GO_KR_API_KEY', 'https://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getCtprvnRltmMesureDnsty', {'returnType': 'json', 'numOfRows': '100', 'pageNo': '1', 'sidoName': '서울', 'ver': '1.0'}),
        ('law', 'LAW_OPEN_API_OC', 'https://www.law.go.kr/DRF/lawSearch.do', {'target': 'law', 'type': 'JSON', 'query': '개인정보 보호법', 'display': '3', 'page': '1'}),
    ]
    futures = [pool.submit(call, *service) for service in services if args.service in ['all', service[0]]]
    results = [f.result() for f in futures]
report_path = EVIDENCE / 'API_호출확인.json'
previous = json.loads(report_path.read_text(encoding='utf-8')) if args.service != 'all' and report_path.exists() else []
combined = [r for r in previous if r['service'] not in {x['service'] for x in results}] + results
report_path.write_text(json.dumps(combined, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(results, ensure_ascii=False, indent=2))
