"""Characterize the existing app defect; these assertions expect the defect."""
from pathlib import Path
import time

from fastapi.testclient import TestClient
import requests

from exchange_info import api, student_view

ROOT = Path(__file__).parent


def configure(monkeypatch):
    state = {'fail':False,'requests':[]}
    def source(url,*args,**kwargs):
        assert url.startswith('https://docs.google.com/spreadsheets/d/') and '/gviz/tq' in url
        state['requests'].append(url)
        if state['fail']:
            raise requests.HTTPError('Review-only controlled CGU source outage')
        sid=url.split('/d/')[1].split('/')[0]
        response=requests.Response();response.status_code=200;response.url=url
        response._content=(ROOT/'source-capture'/f'{sid}.gviz.json').read_bytes()
        response.encoding='utf-8'
        return response
    monkeypatch.setattr(student_view.requests,'get',source)
    original=api.build_student_dashboard
    def dashboard(*args,**kwargs):
        return original(*args,**kwargs,fetch_regulation_rules=False)
    monkeypatch.setattr(api,'build_student_dashboard',dashboard)
    return state


def test_current_cold_failure_keeps_partner_cache_empty_after_source_recovers(tmp_path,monkeypatch):
    state=configure(monkeypatch);state['fail']=True
    client=TestClient(api.create_app(tmp_path))
    params={'school':'林肯大學 Lincoln University','home_school':'長庚大學'}
    assert client.get('/application-workflow',params=params).status_code==404
    calls=len(state['requests']);state['fail']=False
    assert client.get('/application-workflow',params=params).status_code==404
    assert len(state['requests'])==calls,'Existing partner cache never retries the failed empty result'


def test_current_background_failure_replaces_good_dashboard_while_workflow_cache_differs(tmp_path,monkeypatch):
    state=configure(monkeypatch)
    client=TestClient(api.create_app(tmp_path))
    params={'school':'林肯大學 Lincoln University','home_school':'長庚大學'}
    initial=client.get('/student-dashboard',params={'school':'長庚大學'}).json()
    assert len(initial['partner_universities'])==77
    assert client.get('/application-workflow',params=params).status_code==200
    state['fail']=True
    monkeypatch.setattr(api,'DASHBOARD_CACHE_SECONDS',0)
    for _ in range(30):
        after=client.get('/student-dashboard',params={'school':'長庚大學'}).json()
        if not after['partner_universities']:break
        time.sleep(.01)
    assert after['partner_universities']==[]
    assert client.get('/application-workflow',params=params).status_code==200
    assert 'catalogue_source' not in after,'Existing response has no explicit upstream-unavailable status'
