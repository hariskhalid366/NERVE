import {initialState,legalMoves,apply,gameStatus,coord,moveKey} from './chess.mjs';
const GLYPH={K:'♔',Q:'♕',R:'♖',B:'♗',N:'♘',P:'♙',k:'♚',q:'♛',r:'♜',b:'♝',n:'♞',p:'♟','.' :''};
const boardEl=document.querySelector('#board'), statusEl=document.querySelector('#status'),errorEl=document.querySelector('#error');
const historyEl=document.querySelector('#history'),promoteEl=document.querySelector('#promotion');
let states=[initialState()], movesPlayed=[], selected=-1, claimed='';
const state=()=>states.at(-1);
const side=p=>p==='.'?0:p===p.toUpperCase()?1:-1;
function render(){
  const s=state(), status=gameStatus(states), legal=legalMoves(s);
  boardEl.replaceChildren();
  for(let y=0;y<8;y++)for(let x=0;x<8;x++){
    const i=y*16+x,p=s.board[i],b=document.createElement('button');
    b.type='button';b.className='square '+((x+y)%2?'dark':'light');b.setAttribute('role','gridcell');
    b.setAttribute('aria-label',coord(i)+' '+(p==='.'?'empty':p));
    if(i===selected)b.classList.add('selected');
    if(selected>=0&&legal.some(m=>m[0]===selected&&m[1]===i))b.classList.add('target');
    if(p!=='.') {b.textContent=GLYPH[p];b.classList.add(side(p)===1?'piece-white':'piece-black');}
    b.addEventListener('click',()=>selectSquare(i));boardEl.append(b);
  }
  statusEl.textContent=claimed||status.message;
  historyEl.replaceChildren();movesPlayed.forEach(uci=>{const li=document.createElement('li');li.textContent=uci;historyEl.append(li);});
  document.querySelector('#undo').disabled=states.length===1;
  const claim=document.querySelector('#claim'); claim.hidden=!(status.claim&&!status.done&&!claimed);claim.textContent='Claim '+status.claim;
}
function perform(m){ states.push(apply(state(),m));movesPlayed.push(moveKey(m));selected=-1;claimed='';errorEl.textContent='';render(); }
function selectSquare(i){
  if(claimed || gameStatus(states).done)return;
  const s=state(),candidate=legalMoves(s).filter(m=>m[0]===selected&&m[1]===i);
  if(side(s.board[i])===s.turn){selected=i;errorEl.textContent='';render();return;}
  if(candidate.length===1){perform(candidate[0]);return;}
  if(candidate.length>1){showPromotion(candidate);return;}
  selected=-1;errorEl.textContent='Select a piece and one of its legal destinations.';render();
}
function showPromotion(choices){
  const container=document.querySelector('#choices');container.replaceChildren();
  for(const m of choices){ const btn=document.createElement('button');btn.type='button';btn.textContent=({q:'Queen',r:'Rook',b:'Bishop',n:'Knight'})[m[2]];
    btn.addEventListener('click',()=>{promoteEl.close();perform(m);});container.append(btn); }
  promoteEl.showModal();
}
document.querySelector('#undo').addEventListener('click',()=>{if(states.length>1){states.pop();movesPlayed.pop();selected=-1;claimed='';errorEl.textContent='';render();}});
document.querySelector('#reset').addEventListener('click',()=>{states=[initialState()];movesPlayed=[];selected=-1;claimed='';errorEl.textContent='';render();});
document.querySelector('#claim').addEventListener('click',()=>{const status=gameStatus(states);if(status.claim&&!status.done){claimed='Draw claimed — '+status.claim;render();}});
render();
