"""Observe real browser events around the existing unmodified clock/debounce test."""
import json
from pathlib import Path
import sys
import pytest

name=sys.argv[1]
root=Path('/workspace/integration-evidence')/name
class Observe:
    @pytest.hookimpl(hookwrapper=True)
    def pytest_fixture_setup(self,fixturedef,request):
        outcome=yield
        if fixturedef.argname=='page':
            page=outcome.get_result()
            page.add_init_script('''
                window.__navigationEvidence=[];
                const record=(kind,extra={})=>window.__navigationEvidence.push({kind,hash:location.hash,
                    open:document.body?.classList.contains('glass-menu-open'),
                    expanded:document.querySelector('#glass-menu-toggle')?.getAttribute('aria-expanded'),
                    inert:document.querySelector('#glass-navigation')?.inert,...extra});
                addEventListener('hashchange',()=>record('hashchange'));
                addEventListener('popstate',()=>record('popstate'));
                for(const type of ['pointerdown','pointerup','mousedown','mouseup','click','blur','focusin','input','change']) addEventListener(type,e=>record(type,{target:e.target.id||e.target.closest?.('[id]')?.id,trusted:e.isTrusted}),true);
            ''')
    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self,item,call):
        outcome=yield
        report=outcome.get_result()
        page=item.funcargs.get('page')
        if report.when=='call' and page:
            evidence=page.evaluate('({events:window.__navigationEvidence,hash:location.hash,bodyClass:document.body.className,nav:document.querySelector("#glass-navigation")?.outerHTML.slice(0,200),home:state.homeSchool,template:state.activeApplicationTemplateId})')
            (root/'navigation-events.json').write_text(json.dumps({'nodeid':item.nodeid,'outcome':report.outcome,**evidence},ensure_ascii=False,indent=2)+'\n')
raise SystemExit(pytest.main(['-q','--tb=short',*sys.argv[2:],'--junitxml='+str(root/'junit.xml')],plugins=[Observe()]))
