import pytest
from arp.m5 import make_order
from arp.m5_analysis import analyze, cluster_interval


def tasks():
    return [{'task_id':f't{i:02d}','split':'development' if i<4 else 'confirmation'} for i in range(12)]


def test_randomized_task_blocks_retain_m3_and_have_exactly_forty_new_slots():
    order=make_order(tasks(),20261002)
    assert order==make_order(tasks(),20261002) and order!=make_order(tasks(),20261003)
    assert len(order)==40 and len({(r['task_id'],r['arm'],r['repeat']) for r in order})==40
    assert not any(r['split']=='confirmation' and r['arm']=='baseline' and r['repeat']==1 for r in order)
    blocks=[r['task_id'] for i,r in enumerate(order) if i==0 or order[i-1]['task_id']!=r['task_id']]
    assert len(blocks)==12 and len(set(blocks))==12


def test_cluster_bootstrap_pairs_tasks_and_hoeffding_fallback_is_honest():
    zero=cluster_interval([0]*8)
    assert zero['bootstrap_95']==[0,0] and zero['degenerate']
    assert zero['hoeffding_95']==pytest.approx([-.9603227913,.9603227913])
    assert zero['conclusion']=='inconclusive' and 'fallback' in zero['selected_method']
    gain=cluster_interval([.5,0,0,0,0,0,0,0])
    assert gain['estimate']==.0625 and gain['bootstrap_95'][0]==0 and gain['conclusion']=='inconclusive'


def data():
    return [dict(task_id=t['task_id'],split=t['split'],arm=arm,repeat=repeat,state='resolved',success=True,
                 agent_wall_seconds=20 if arm=='baseline' else 10,run_id=f"{t['task_id']}-{arm}-{repeat}",source='fixture')
            for t in tasks() for arm in ['baseline','intervention'] for repeat in [1,2]]


def test_full_design_keeps_all_attempts_and_wall_time_has_correct_sign():
    result=analyze(data(),tasks())
    assert result['complete_48_slot_design']
    assert result['confirmation']['arms']['baseline']['successes']==16
    assert result['all_tasks_descriptive']['arms']['intervention']['scored_attempts']==24
    assert result['key_secondary_confirmation_wall']['estimate']==-10
    assert len(result['unchanged'])==8 and result['primary_confirmation']['conclusion']=='inconclusive'


def test_infrastructure_missing_outcome_blocks_primary_and_duplicates_are_rejected():
    rows=data(); rows[-1].update(success=None,state='usage_limit')
    result=analyze(rows,tasks())
    assert not result['complete_48_slot_design'] and len(result['infrastructure_exclusions'])==1
    assert result['confirmation']['success_delta'] is None
    assert 'incomplete' in result['primary_confirmation']['conclusion']
    with pytest.raises(ValueError,match='Duplicate'):
        analyze(data()+[data()[0]],tasks())
