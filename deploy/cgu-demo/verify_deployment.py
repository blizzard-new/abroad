"""Exercise only a fresh synthetic workspace, after verifying the demo identity."""
from __future__ import annotations

import argparse
import json
from urllib.parse import urlsplit

import requests


def verify(url: str, origin: str, proxy_check: bool = False) -> dict:
    url = url.rstrip('/')
    origin = origin.rstrip('/')
    if not origin.startswith('https://'):
        raise ValueError('Public origin must use HTTPS')
    if proxy_check and urlsplit(url).hostname not in ('127.0.0.1', 'localhost', '::1'):
        raise ValueError('HTTP proxy simulation is limited to loopback')
    if not proxy_check and url != origin:
        raise ValueError('Public verification must use the exact HTTPS origin')
    client = requests.Session()
    client.headers['Origin'] = origin
    if proxy_check:
        client.headers['Host'] = urlsplit(origin).netloc

    def call(method, path, **kwargs):
        return client.request(method, url + path, timeout=90, **kwargs)

    health_response = call('GET', '/health')
    health_response.raise_for_status()
    health = health_response.json()
    if health.get('mode') != 'cgu-demo' or health.get('ui') != 'shared-uniway-platform':
        raise RuntimeError('Not a CGU demo service; refusing all test writes')
    schools = call('GET', '/universities').json()
    assert [s['school_name'] for s in schools] == ['長庚大學']
    home = call('GET', '/')
    home.raise_for_status()
    assert 'UniWay CGU' in home.text and 'noindex' in home.headers['X-Robots-Tag']
    cookie = home.headers['Set-Cookie']
    assert 'Secure' in cookie and 'HttpOnly' in cookie and 'Domain=' not in cookie
    if proxy_check:
        # Simulate the edge forwarding the browser's Secure cookie over loopback.
        client.headers['Cookie'] = 'uniway_cgu_demo_session=' + client.cookies.get('uniway_cgu_demo_session')
    assert call('GET', '/auth/session').json()['display_name'] == '林小程（展示資料）'
    made = call('POST', '/account/application-paths', json=dict(revision=0,
        home_school='長庚大學', target_school='林肯大學 Lincoln University', academic_year='116',
        departure_year='2027', semester='fall'))
    assert made.status_code == 201, made.status_code
    plan = made.json()
    path = '/account/application-paths/' + plan['plan']['id']
    assert len(plan['stages']) == 6
    saved = call('PUT', path + '/steps/home', json={'revision':plan['revision'], 'step':{'confirmed':True}})
    saved.raise_for_status()
    assert call('GET', path).json()['plan']['steps']['home']['confirmed'] is True
    workspace = call('PUT', path + '/workspace', json={'revision':saved.json()['revision'],
        'tasks':[{'id':'deploysmoke123', 'title':'展示用品準備', 'date_kind':'personal', 'due_date':'2027-06-01'}]})
    workspace.raise_for_status()
    assert call('GET', path).json()['workspace']['tasks'][0]['date_kind'] == 'personal'
    assert call('POST', path + '/workspace/extract', json={}).status_code == 403
    assert call('POST', '/demo/reset', headers={'Origin':'https://elsewhere.invalid'}).status_code == 403
    reset = call('POST', '/demo/reset')
    reset.raise_for_status()
    if proxy_check:
        client.headers['Cookie'] = 'uniway_cgu_demo_session=' + client.cookies.get('uniway_cgu_demo_session')
    assert call('GET', '/account/application-paths').json()['items'] == []
    return {'status':'passed', 'revision':health.get('revision'), 'origin':origin,
            'transport':'loopback proxy simulation' if proxy_check else 'public HTTPS',
            'checks':['CGU-only', 'Secure cookie', 'six stages', 'saved progress', 'workspace', 'blocked upload', 'CSRF', 'reset']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', required=True)
    parser.add_argument('--public-origin', default='https://demo.uniway-tw.com')
    parser.add_argument('--proxy-check', action='store_true')
    args = parser.parse_args()
    print(json.dumps(verify(args.url, args.public_origin, args.proxy_check), ensure_ascii=False))
