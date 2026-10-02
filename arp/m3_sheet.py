"""Prepare twelve human-review rows using the already frozen deterministic rubric."""
import csv
import html
import io
import json
from pathlib import Path
from .m3 import ROOT, validate_freeze
from .rules import LABELS, label

COLUMNS = ['trajectory','review_role','task','outcome','m5_assignment','agent_wall_seconds',
           'rule_primary','rule_secondary','key_trace_evidence','human_primary','human_secondary','human_notes']


def csv_text(rows):
    stream=io.StringIO(newline='')
    writer=csv.DictWriter(stream,fieldnames=COLUMNS); writer.writeheader(); writer.writerows(rows)
    return stream.getvalue()


def prepare(output):
    freeze=validate_freeze()
    summary=json.loads((output/'summary.json').read_text(encoding='utf-8'))
    if summary['status']!='M3_baselines_complete_pending_human_labels': raise ValueError('All eight baselines must complete first')
    records=summary['attempts']
    if [(r['task_id'],r['arm'],r['repeat']) for r in records] != [(p['task_id'],'baseline',1) for p in freeze['m3_plan']]:
        raise ValueError('M3 baseline/repeat plan differs')
    paths=sorted((ROOT/'artifacts/private/dev-ceiling-001').glob('*-baseline-*')) + [output/r['run_id'] for r in records]
    if len(paths)!=12: raise ValueError('Exactly four development and eight confirmation rows required')
    # Only rendering is redacted; originals stay host-private with their source hashes.
    auth=json.loads((Path.home()/'.codex/auth.json').read_text(encoding='utf-8'))
    secrets=[v for v in auth.get('tokens',{}).values() if isinstance(v,str) and len(v)>40]
    def clean(text):
        for secret in secrets: text=text.replace(secret,'[REDACTED_CREDENTIAL]')
        return text
    rows=[]; evidence=[]
    for number,attempt in enumerate(paths,1):
        record=label(attempt)
        role='development calibration' if number<=4 else 'held-out confirmation'
        compact=[]
        for e in record['evidence']:
            ref=e['item_id'] + (f" (JSONL line {e['event_line']})" if e['event_line'] else '')
            compact.append(ref+': '+e['excerpt'])
        row={'trajectory':f'M3-{number:02d}','review_role':role,'task':record['task_id'],
            'outcome':'pass' if record['success'] is True else 'not measured (infrastructure)' if record['success'] is None else 'fail',
            'm5_assignment':'baseline repeat 1; retain, do not rerun' if number>4 else 'development calibration only',
            'agent_wall_seconds':record['metrics']['agent_wall_seconds'],
            'rule_primary':record['rule_primary'],'rule_secondary':', '.join(record['rule_secondary']),
            'key_trace_evidence':clean(' | '.join(compact)),'human_primary':'','human_secondary':'','human_notes':''}
        rows.append(row)
        record['trajectory']=row['trajectory']; record['review_role']=role
        record['private_events_path']=str((attempt/'events.jsonl').resolve())
        record['evidence']=[{**e,'command':clean(e['command']),'output':clean(e['output'][:12000]),'excerpt':clean(e['excerpt'])} for e in record['evidence']]
        evidence.append(record)
    review=ROOT/'review'; review.mkdir(exist_ok=True)
    (review/'m3_labeling_sheet.csv').write_text(csv_text(rows),encoding='utf-8',newline='')
    bundle={'status':'ready_for_user_labels','human_labels_supplied':0,'rubric_sha256':freeze['rubric_sha256'],
            'intervention_sha256':freeze['intervention_sha256'],'rows':evidence}
    (review/'m3_labeling_evidence.json').write_text(json.dumps(bundle,indent=2)+'\n',encoding='utf-8',newline='\n')
    rendered=[]
    options='<option value="">Select your label</option>'+''.join(f'<option>{html.escape(v)}</option>' for v in LABELS)
    for i,(row,detail) in enumerate(zip(rows,evidence)):
        snippets=''.join('<p><strong>'+html.escape(e['item_id'])+'</strong> '+html.escape(e['excerpt'])+'</p>'+
             ('<details><summary>Public command and output</summary><pre>'+html.escape(e['command']+'\n\n'+e['output'])+'</pre></details>' if e['command'] else '') for e in detail['evidence'])
        rendered.append('<tr>'+''.join('<td>'+html.escape(str(row[k]))+'</td>' for k in ['trajectory','review_role','task','outcome','agent_wall_seconds'])+
            '<td>'+html.escape(row['rule_primary'])+'<small>Secondary: '+html.escape(row['rule_secondary'] or 'none')+'</small></td>'+
            '<td><details><summary>Key evidence ('+str(len(detail['evidence']))+' references)</summary>'+snippets+'</details><small>'+html.escape(detail['rule_reason'])+'</small></td>'+
            f'<td><select data-row="{i}" data-key="human_primary">'+options+'</select><input data-row="'+str(i)+'" data-key="human_secondary" placeholder="Secondary labels, comma separated"><textarea data-row="'+str(i)+'" data-key="human_notes" placeholder="Evidence reference and reasoning; uncertainty is allowed"></textarea></td></tr>')
    data=json.dumps(rows).replace('<','\u003c').replace('>','\u003e').replace('&','\u0026')
    page="""<!doctype html><html lang="en"><meta charset="utf-8"><title>M3 human labeling sheet</title>
<style>body{font:15px system-ui;margin:24px;color:#182433;background:#f5f7fa}h1{font-size:25px}.wrap{overflow:auto}table{border-collapse:collapse;background:white;min-width:1200px;width:100%}td,th{border:1px solid #d3dbe5;padding:10px;vertical-align:top;text-align:left}th{background:#e7edf4}small{display:block;margin-top:8px;color:#516174}select,input,textarea{box-sizing:border-box;width:100%;margin:4px 0;padding:8px;min-width:210px}textarea{min-height:85px}pre{white-space:pre-wrap;overflow-wrap:anywhere;max-height:400px;overflow:auto;font-size:12px}button{padding:10px 16px;margin:8px 10px 16px 0}summary{cursor:pointer}td:nth-child(7){min-width:300px}</style>
<h1>M3 human labeling sheet</h1><p>12 trajectories: 4 development calibration and 8 held-out confirmation. Human labels are blank. Review the evidence, select your primary label, and optionally add secondary labels and evidence references. Export the CSV and return it for agreement analysis.</p>
<p>Primary rule labels describe final outcomes; intermediate setup/behavior obstacles appear as secondary diagnostics. Expected xfails and intentional pre-fix reproductions need human judgment. Rule predictions are shown as requested: this review is unblinded and may be anchored. No independent blinded validation or human labels are claimed yet.</p>
<p>The eight confirmation rows are M5 baseline repeat 1 and will not be rerun. The intervention and rubric were frozen before these runs. No M5 intervention attempt has started.</p>
<button id="download">Download labeled CSV</button><span id="count"></span><div class="wrap"><table><thead><tr><th>Trajectory</th><th>Role</th><th>Task</th><th>Outcome</th><th>Agent seconds</th><th>Rule label</th><th>Key trace evidence</th><th>Your review</th></tr></thead><tbody>__ROWS__</tbody></table></div>
<script>const rows=__DATA__; const columns=__COLUMNS__; const storageKey=__STORAGE__;
function count(){document.getElementById('count').textContent=rows.filter(r=>r.human_primary).length+' / 12 primary labels entered';}
try{const saved=JSON.parse(localStorage.getItem(storageKey)||'null');if(saved&&saved.length===rows.length){saved.forEach((r,i)=>['human_primary','human_secondary','human_notes'].forEach(k=>rows[i][k]=r[k]||''));}}catch(e){}
document.querySelectorAll('[data-row]').forEach(el=>{el.value=rows[+el.dataset.row][el.dataset.key];el.addEventListener('input',()=>{rows[+el.dataset.row][el.dataset.key]=el.value;try{localStorage.setItem(storageKey,JSON.stringify(rows));}catch(e){}count();});});
function cell(value){let text=String(value??'');if(/^[=+@-]/.test(text))text="'"+text;return '"'+text.replaceAll('"','""')+'"';}
document.getElementById('download').onclick=()=>{const csv=[columns.map(cell).join(','),...rows.map(r=>columns.map(k=>cell(r[k])).join(','))].join('\r\n');const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download='m3_human_labels.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};count();</script></html>"""
    page=page.replace('__ROWS__',''.join(rendered)).replace('__DATA__',data).replace('__COLUMNS__',json.dumps(COLUMNS)).replace('__STORAGE__',json.dumps('arp-m3-'+freeze['rubric_sha256']))
    (review/'m3_labeling_sheet.html').write_text(page,encoding='utf-8',newline='\n')
    return rows


def main():
    rows=prepare(ROOT/'artifacts/private/m3-confirmation-001')
    print(json.dumps({'status':'ready_for_user_labels','rows':len(rows),'human_labels_supplied':0}))


if __name__=='__main__': main()
