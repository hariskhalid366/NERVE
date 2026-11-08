"""Reproducible dogfood trial over a runnable chess project.

Deterministic retrieval/transport measurements only: no LLM API is called.
Synthetic incident notes are labeled as test fixtures, not historical user facts.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from nerve.core import Nerve, tokens
from nerve.brief import project_brief

CHESS = Path(__file__).resolve().parents[2] / 'examples' / 'chess-mini'
# These stable IDs must exist in the real code scan. Each synthetic observation
# is a test fixture recording a code decision or verified regression test.
TARGETS = [
    {'id':'symbol:chess.mjs:legalMoves','aliases':['legal destinations','valid chess moves'],'desc':'Filters pseudo legal moves that would leave the king in check.',
     'note':'After testing pinned pieces, keep filtering pseudo moves against the king-in-check rule.',
     'event':'Regression verified: a pinned rook cannot step sideways and expose its king.',
     'queries':['legalMoves','legal destinations','the pinned rook moved sideways and exposed the king','the function that filters moves that put your own monarch in danger']},
    {'id':'symbol:chess.mjs:parseFen','aliases':['board notation parser','setup import'],'desc':'Builds a chess board and game metadata from a FEN position.',
     'note':'Keep FEN validation strict for rank lengths and both kings; the fixture tests malformed strings.',
     'event':'Starting position has white queen on d1 and black queen on d8.',
     'queries':['parseFen','board notation parser','starting board queens were on the wrong home files','the importer that creates a position from a compact text notation']},
    {'id':'symbol:chess.mjs:apply','aliases':['move transition','board update'],'desc':'Applies a validated move and updates castling, en passant, clocks, and board state.',
     'note':'Store complete snapshots after applying moves so undo restores castling rights and en passant.',
     'event':'Special capture removes a pawn from the square behind its destination.',
     'queries':['apply','move transition','special capture failed to remove the adjacent pawn','the state updater preserving rights when pieces change squares']},
    {'id':'symbol:chess.mjs:gameStatus','aliases':['endgame detector','game conclusion'],'desc':'Computes checkmate, stalemate, automatic draw, and claimable draws.',
     'note':'Offer a draw claim at threefold repetition; automatically end the game on fivefold repetition.',
     'event':'Fools mate regression verified: black checkmates white after the fourth ply.',
     'queries':['gameStatus','endgame detector','fools mate winner was not announced','which calculation decides whether the match has finished']},
    {'id':'symbol:chess.mjs:positionKey','aliases':['repetition signature','position fingerprint'],'desc':'Stable board signature for checking threefold and fivefold repetition.',
     'note':'Do not include the en passant square in repetition signatures unless a legal en passant move exists.',
     'event':'Threefold repetition fixture completed with knight moves returning to their home squares.',
     'queries':['positionKey','repetition signature','knights returning home did not count as same board','where identical states are recognized across a series of turns']},
    {'id':'symbol:app.mjs:selectSquare','aliases':['tile click handler','square interaction'],'desc':'Validates selection of a source and destination in the browser interface.',
     'note':'Selecting a friendly piece switches the current selection rather than attempting an illegal capture.',
     'event':'Illegal destination now displays a message instead of modifying the game.',
     'queries':['selectSquare','tile click handler','clicking an impossible destination changed pieces','the code listening when a person touches a board cell']},
    {'id':'symbol:app.mjs:showPromotion','aliases':['pawn promotion dialog','upgrade chooser'],'desc':'Opens a dialog to select queen, rook, bishop or knight.',
     'note':'Offer four promotion options rather than automatically promoting every pawn to a queen.',
     'event':'Pawn on a7 can promote on a8 to each of four piece types.',
     'queries':['showPromotion','upgrade chooser','pawn reaching last rank had no knight option','the popup where a player chooses a new piece']},
    {'id':'symbol:app.mjs:render','aliases':['board painter','interface update'],'desc':'Draws the accessible 64-square chess board and move history.',
     'note':'Render legal destination markers and descriptive square labels for accessibility.',
     'event':'Board redraw now updates undo state and turn status together.',
     'queries':['render','board painter','the grid was not refreshed after undo','where the visible squares and pieces get painted again']},
    {'id':'file:style.css','aliases':['mobile layout','board styling'],'desc':'CSS grid and responsive sizing for an interactive chess board.',
     'note':'Keep the chess board square and switch to one column on narrow screens.',
     'event':'Styles limit the board to eight equal columns with an aspect ratio of one.',
     'queries':['style.css','mobile layout','board became non-square at small widths','the file responsible for touch-friendly cell dimensions']},
    {'id':'file:index.html','aliases':['document shell','web page markup'],'desc':'Accessible HTML skeleton containing the board, status, controls and promotion dialog.',
     'note':'Use the aria-live status region to announce whose turn it is.',
     'event':'HTML loads the JavaScript chess interface using a module script.',
     'queries':['index.html','document shell','the status area was not announced to assistive technology','which page defines the controls and live game status']},
    {'id':'symbol:chess.mjs:insufficient','aliases':['material draw','dead position'],'desc':'Checks whether remaining material is insufficient for checkmate.',
     'note':'The king-versus-king fixture should finish as an automatic draw.',
     'event':'Regression verified: kings alone are insufficient mating material.',
     'queries':['insufficient','material draw','kings alone were not declared a draw','the logic determining whether victory is impossible from remaining pieces']},
    {'id':'symbol:chess.mjs:isAttacked','aliases':['threat detector','attacked tile'],'desc':'Determines whether a square is attacked by the opponent.',
     'note':'Do not allow a king to castle across an attacked transit square.',
     'event':'Castling through a square defended by a black rook was rejected.',
     'queries':['isAttacked','threat detector','the king crossed a defended cell while castling','how the game finds squares threatened by enemy pieces']},
]
UNKNOWN = [
    'where is the payment checkout gateway', 'the missing multiplayer matchmaking server',
    'fix the neural network training optimizer', 'why did the database delete customer accounts',
    'the VR helmet tracking layer','video transcoding codec options',
    'which SQL migration altered the inventory schema','bitcoin wallet private key storage',
    'how is satellite telemetry processed','the PDF printer queue scheduling',
]


def seed(n: Nerve) -> dict:
    index=n.scan()
    for entry in TARGETS:
        exact=n.context(entry['id'])
        if not exact['found']:
            raise AssertionError(f"Missing real source symbol: {entry['id']}")
        n.observe(entry['id'],exact['label'],exact['kind'],entry['desc'],entry['aliases'],
                  exact['source_path'],origin='benchmark-observer',state={'regression_test':'passing','seed':'invented chess evaluation fixture'})
        n.event(entry['id'],'regression',entry['event'])
        n.remember(entry['note'],entry['id'],author='synthetic-agent-A',category='verified-fixture')
    n.remember('The demo uses native browser JavaScript and no external dependencies.',author='synthetic-agent-A')
    return index


def flat_rank(n: Nerve, query: str) -> str | None:
    """Transparent simple bag-of-words baseline over equivalent structured facts."""
    q=tokens(query)
    if not q:return None
    data=[]
    for r in n.conn.execute('SELECT * FROM targets'):
        history=[e[0] for e in n.conn.execute('SELECT message FROM events WHERE target_id=?',(r['target_id'],))]
        history += [m[0] for m in n.conn.execute('SELECT text FROM memories WHERE target_id=?',(r['target_id'],))]
        text=' '.join([r['label'],r['source_path'],r['description'],r['aliases'],*history])
        overlap=len(q & tokens(text))
        if overlap:data.append((overlap,r['target_id']))
    return sorted(data,key=lambda x:(-x[0],x[1]))[0][1] if data else None


def approx_pieces(o:object)->int:
    # NOT a tokenizer or actual model consumption number.
    return len(re.findall(r"\w+|[^\w\s]",json.dumps(o,ensure_ascii=False)))


def mcp_handoff(root:Path,first_id:str)->dict:
    # New Python process starts after the seeding process closed its SQLite handle.
    messages=[{'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'chess-handoff','version':'0.1'}}},
              {'jsonrpc':'2.0','id':2,'method':'tools/list','params':{}},
              {'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'resolve_target','arguments':{'query':'legal destinations'}}},
              {'jsonrpc':'2.0','id':4,'method':'tools/call','params':{'name':'get_target_context','arguments':{'target_id':first_id}}}]
    env={'PYTHONPATH':str(Path(__file__).resolve().parents[2]),'NERVE_MCP_BACKEND':'builtin'}
    import os
    run=subprocess.run([sys.executable,'-m','nerve','--project',str(root),'mcp'],input='\n'.join(json.dumps(m) for m in messages)+'\n',text=True,
                       capture_output=True,env={**os.environ,**env},timeout=20,check=True)
    data=[json.loads(l) for l in run.stdout.splitlines()]
    resolved=json.loads(data[2]['result']['content'][0]['text'])
    exact=json.loads(data[3]['result']['content'][0]['text'])
    return {'initialize':data[0]['result']['serverInfo']['name']=='nerve-local',
            'tools_exposed':len(data[1]['result']['tools']),
            'resolve_correct':resolved['candidates'][0]['target_id']==first_id,
            'context_contains_A_note':any('pinned pieces' in x['text'] for x in exact['memories'])}


def run(output:Path, persist_project:Path|None=None):
    with tempfile.TemporaryDirectory(prefix='nerve-chess-bench-') as temp:
        root=Path(temp)/'chess-mini'
        shutil.copytree(CHESS,root,ignore=shutil.ignore_patterns('.nerve','__pycache__'))
        with Nerve(root) as a:
            index=seed(a)
        # Source memories live on disk, A is closed; B opens in a fresh process via MCP.
        handoff=mcp_handoff(root,TARGETS[0]['id'])
        cases=[{'category':category,'query':query,'gold':entry['id']}
               for entry in TARGETS for category,query in zip(['exact','alias','history','paraphrase'],entry['queries'])]
        per_case=[]
        with Nerve(root) as b:
            full_history={'targets':[dict(r) for r in b.conn.execute('SELECT * FROM targets')],
                          'events':[dict(r) for r in b.conn.execute('SELECT * FROM events')],
                          'memories':[dict(r) for r in b.conn.execute('SELECT * FROM memories')]}
            for case in cases:
                out=b.resolve(case['query']); predicted=out['candidates'][0]['target_id'] if out['candidates'] else None
                flat=flat_rank(b,case['query'])
                exact=b.context(predicted) if predicted else {}
                payload={'candidates':out, 'context':exact}
                per_case.append({**case,'nerve_prediction':predicted,'nerve_correct':predicted==case['gold'],
                                 'flat_prediction':flat,'flat_correct':flat==case['gold'],
                                 'decision':out['decision'],'payload_pieces':approx_pieces(payload),
                                 'full_history_pieces':approx_pieces(full_history)})
            negatives=[]
            for query in UNKNOWN:
                out=b.resolve(query)
                negatives.append({'query':query,'candidate_count':len(out['candidates']),
                                  'decision':out['decision'],'no_candidate':not out['candidates'],
                                  'no_supported_candidate':out['decision']!='supported_candidate'})
            # With exact stable ID, new process successfully recovers all A notes.
            evidence=[]
            for entry in TARGETS:
                record=b.context(entry['id'])
                evidence.append({'id':entry['id'], 'found':record['found'],
                                 'note_recovered':any(m['text']==entry['note'] for m in record['memories']),
                                 'event_recovered':any(e['message']==entry['event'] for e in record['events'])})
            brief=project_brief(b)
        cat={k: {'cases':len([x for x in per_case if x['category']==k]),
                 'nerve_correct':sum(x['nerve_correct'] for x in per_case if x['category']==k),
                 'flat_correct':sum(x['flat_correct'] for x in per_case if x['category']==k)}
             for k in ['exact','alias','history','paraphrase']}
        overall={'known_queries':len(cases),'nerve_top1_correct':sum(x['nerve_correct'] for x in per_case),
                 'flat_top1_correct':sum(x['flat_correct'] for x in per_case),
                 'negative_queries':len(negatives),'negative_no_candidate':sum(x['no_candidate'] for x in negatives),
                 'negative_no_supported_candidate':sum(x['no_supported_candidate'] for x in negatives),
                 'explicit_id_context_facts':sum(x['note_recovered'] and x['event_recovered'] for x in evidence),
                 'explicit_id_context_total':len(evidence),
                 'avg_selected_payload_pieces':round(sum(x['payload_pieces'] for x in per_case)/len(per_case),1),
                 'full_history_payload_pieces':approx_pieces(full_history),
                 'payload_reduction_vs_full_history_percent':round(100*(1-sum(x['payload_pieces'] for x in per_case)/len(per_case)/approx_pieces(full_history)),2)}
        result={'method':'deterministic chess dogfood; no LLM or provider tokens','source_project':'examples/chess-mini',
                'environment':'fresh temp copy and separate MCP subprocess','index':index,'categories':cat,
                'overall':overall,'mcp_handoff':handoff,'negative_cases':negatives,'per_case':per_case}
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        if persist_project:
            shutil.copytree(root,persist_project,ignore=shutil.ignore_patterns('__pycache__'))
        return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=Path('benchmark/results/CHESS_DOGFOOD.json'))
    p.add_argument('--copy-seeded-project',type=Path,default=None)
    args=p.parse_args()
    result=run(args.output,args.copy_seeded_project)
    print(json.dumps({key:result[key] for key in ("method","index","categories","overall","mcp_handoff")},indent=2))

if __name__=='__main__': main()
