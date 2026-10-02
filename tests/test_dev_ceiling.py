import json
import pytest
from arp import m2
from arp.adapters import AdapterConfig
from arp.dev_ceiling import catalog_config


def test_ceiling_rejects_confirmation_task_before_launch(tmp_path, monkeypatch):
    root=tmp_path/'root'; dataset=root/'artifacts/private/m1-v7'; dataset.mkdir(parents=True)
    tasks=[{'task_id':task,'split':'confirmation' if i==0 else 'development','human_acceptance':'accepted'}
           for i,(task,_) in enumerate(m2.CEILING_PLAN)]
    (dataset/'tasks.json').write_text(json.dumps(tasks))
    monkeypatch.setattr(m2,'ROOT',root)
    monkeypatch.setattr(m2,'Docker',lambda *a:pytest.fail('Docker launched despite confirmation split'))
    output=root/'artifacts/private/ceiling'
    with pytest.raises(ValueError,match='development'):
        m2.run_batch(dataset,output,tmp_path/'absent-auth','agent','proxy',ceiling_config=AdapterConfig('gpt-5.6-luna','low'))
    assert not output.exists()


def test_ceiling_absent_login_model_stops(tmp_path):
    catalog=tmp_path/'catalog.json'; catalog.write_text('[]')
    with pytest.raises(ValueError,match='absent'): catalog_config(catalog)


def test_explicit_low_effort_does_not_use_medium_catalog_default(tmp_path, monkeypatch):
    from arp.adapters import CodexCLIAdapter
    import subprocess
    class Container:
        name='fixture'
        def exec(self,*a):
            return subprocess.CompletedProcess([],0,json.dumps([{'model':'gpt-5.6-luna','catalog_default_reasoning_effort':'medium'}]).encode())
    class Process:
        returncode=0
        def __init__(self,*a,**kw):
            kw['stdout'].write(b'{"type":"turn.completed","usage":{"input_tokens":10,"output_tokens":1}}\n')
        def communicate(self,*a,**kw): pass
    monkeypatch.setattr(subprocess,'Popen',Process)
    adapter=CodexCLIAdapter(AdapterConfig('gpt-5.6-luna','low'))
    adapter.prepare(Container(),'probe',tmp_path)
    result=adapter.run()
    assert result.inference_settings['reasoning_effort']=='low'
    assert result.inference_settings['catalog_default_reasoning_effort']=='medium'
    assert result.inference_settings['observed_reasoning_effort'] is None
    assert 'explicit client' in result.inference_settings['evidence']
