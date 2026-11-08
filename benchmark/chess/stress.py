"""Supplemental never-tuned-to stress probe on the existing chess fixture.

Caution: these queries are authored with knowledge of the 12 seeded targets.
They are NOT an independently sampled generalization benchmark, and the
underlying facts are the same as the primary dogfood evaluation.
"""
from __future__ import annotations
import json
import shutil
import tempfile
from pathlib import Path
from nerve.core import Nerve
from benchmark.chess.run import CHESS, TARGETS, seed, flat_rank

# Query wording differs from the primary fixture. Fixing retrieval code on these
# questions invalidates their future use as a held-out stress probe.
STRESS = {
    'symbol:chess.mjs:legalMoves': [
        'Which routine rejects leaving my own king exposed?',
        'Find the validator responsible for legal chess choices'],
    'symbol:chess.mjs:parseFen': [
        'Where does a FEN string become a board position?',
        'The import notation was parsed into an impossible arrangement'],
    'symbol:chess.mjs:apply': [
        'Undo failed to restore castling entitlement after moving a rook',
        'Which transition mutates captured pawn handling?'],
    'symbol:chess.mjs:gameStatus': [
        'Draw adjudication is triggered too early',
        'The game does not end when a player is checkmated'],
    'symbol:chess.mjs:positionKey': [
        'The same configuration appears thrice but the game ignores the repetition',
        'Which representation normalizes en passant availability for repeated states?'],
    'symbol:app.mjs:selectSquare': [
        'Tapping the wrong chessboard cell still changed the game',
        'Where is the selection input for chessboard squares handled?'],
    'symbol:app.mjs:showPromotion': [
        'Where are new queen and knight choices displayed?',
        'Advancing a pawn to the end should offer multiple outcomes'],
    'symbol:app.mjs:render': [
        'The squares are not redrawn after taking back a turn',
        'Find the function painting positions on screen'],
    'file:style.css': [
        'At phone width the playing area becomes stretched',
        'Which stylesheet defines the grid sizing?'],
    'file:index.html': [
        'Screen readers cannot announce whose move it is',
        'Which document contains the game elements loaded into the browser?'],
    'symbol:chess.mjs:insufficient': [
        'Only two kings remain and the game should be tied',
        'Which check handles no possible mating sequence?'],
    'symbol:chess.mjs:isAttacked': [
        'The monarch moved through a threatened square during castling',
        'Where are enemy-controlled tiles detected?'],
}
NEGATIVE = [
    'Which Stripe payment webhook retries failed charges?',
    'Explain the Kubernetes autoscaler in our deployment',
    'Find the authentication login token refresh middleware',
    'Where is the NPC neural chess opponent model?',
    'What database migration created user subscriptions?',
    'Locate the telemetry for GPS satellite tracking',
    'Where are multiplayer chat messages persisted?',
    'How are PDF invoices produced after checkout?',
]

def evaluate(output: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix='nerve-chess-stress-') as td:
        root=Path(td)/'chess'
        shutil.copytree(CHESS, root, ignore=shutil.ignore_patterns('.nerve','__pycache__'))
        with Nerve(root) as n:
            seed(n)
            positive=[]
            for target_id,qs in STRESS.items():
                for query in qs:
                    out=n.resolve(query)
                    pred=out['candidates'][0]['target_id'] if out['candidates'] else None
                    base=flat_rank(n,query)
                    positive.append({'query':query,'target_id':target_id,'nerve':pred,
                                     'baseline':base,'nerve_correct':pred==target_id,
                                     'baseline_correct':base==target_id,'decision':out['decision']})
            negative=[{'query':q,'decision':n.resolve(q)['decision'],
                       'no_candidate':not n.resolve(q)['candidates']} for q in NEGATIVE]
    report={
        'qualification':'Hand-authored stress probes on chess targets; not statistically independent, not LLM performance',
        'positive_count':len(positive),'nerve_top1_correct':sum(x['nerve_correct'] for x in positive),
        'flat_top1_correct':sum(x['baseline_correct'] for x in positive),
        'negative_count':len(negative),'negative_no_candidate':sum(x['no_candidate'] for x in negative),
        'negative_needs_confirmation_or_no_match':sum(x['decision']!='supported_candidate' for x in negative),
        'positive':positive,'negative':negative}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+'\n')
    return report

if __name__=='__main__':
    target=Path('benchmark/results/CHESS_STRESS_V0_6.json')
    r=evaluate(target)
    print(json.dumps({k:v for k,v in r.items() if k not in ('positive','negative')},indent=2))
