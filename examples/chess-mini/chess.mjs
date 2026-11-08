/** Minimal dependency-free chess engine. Normal setup, legal moves, castling,
 * en passant, promotion, check/mate, stalemate, repetition, and move clocks.
 * A move uses [fromIndex, toIndex, promotionLetter, specialFlag].
 * This is educational software, not a tournament rules library.
 */
export const INITIAL_FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';
const OFFSETS = { n: [-33,-31,-18,-14,14,18,31,33], b: [-17,-15,15,17], r: [-16,-1,1,16], k: [-17,-16,-15,-1,1,15,16,17] };
const on = i => i >= 0 && i < 128 && !(i & 0x88);
const side = p => p === '.' ? 0 : p === p.toUpperCase() ? 1 : -1;
export const coord = i => 'abcdefgh'[i & 7] + (8 - (i >> 4));
export const at = s => (8 - Number(s[1])) * 16 + 'abcdefgh'.indexOf(s[0]);
export const moveKey = m => coord(m[0]) + coord(m[1]) + m[2];
export function parseFen(fen) {
  const x = fen.trim().split(/\s+/), b = Array(128).fill('.');
  if(x.length !== 6 || !/^[wb]$/.test(x[1]) || !/^(?:-|K?Q?k?q?)$/.test(x[2]) || !/^(?:-|[a-h][36])$/.test(x[3])) throw Error('Invalid FEN');
  const ranks = x[0].split('/');
  if(ranks.length !== 8) throw Error('Invalid rank count');
  ranks.forEach((r,y) => { let col = 0; for(const p of r){
    if(/^[1-8]$/.test(p)) col += Number(p);
    else { if(!/^[pnbrqkPNBRQK]$/.test(p) || col >= 8) throw Error('Invalid piece'); b[y*16+col++] = p; }
  } if(col !== 8) throw Error('Invalid rank length'); });
  if(b.filter(p=>p==='K').length!==1 || b.filter(p=>p==='k').length!==1) throw Error('FEN requires two kings');
  if(!/^\d+$/.test(x[4]) || !/^[1-9]\d*$/.test(x[5])) throw Error('Invalid clock');
  const rights = (x[2].includes('K')?1:0)|(x[2].includes('Q')?2:0)|(x[2].includes('k')?4:0)|(x[2].includes('q')?8:0);
  return { board:b, turn:x[1]==='w'?1:-1, rights, ep:x[3]==='-'?-1:at(x[3]), half:Number(x[4]), full:Number(x[5]) };
}
export function isAttacked(s, square, by) {
  for(let f=0;f<128;f++){
    if(!on(f) || side(s.board[f]) !== by) continue;
    const p = s.board[f].toLowerCase();
    if(p==='p') { if(square===f-16*by-1 || square===f-16*by+1) return true; continue; }
    for(const d of (OFFSETS[p] || OFFSETS.k)) {
      for(let t=f+d;on(t);t+=d) {
        if(t===square) return true;
        if(s.board[t]!=='.' || p==='n' || p==='k') break;
      }
    }
  }
  return false;
}
export const isChecked = (s, player=s.turn) => isAttacked(s, s.board.indexOf(player===1?'K':'k'), -player);
export function apply(s,m) {
  const [from,to,promotion='',special=''] = m, board=s.board.slice(), piece=board[from], captured=board[to];
  if(piece==='.' || side(piece)!==s.turn) throw Error('No current-player piece on source');
  let rights=s.rights;
  board[from]='.'; board[to]=promotion?(s.turn===1?promotion.toUpperCase():promotion):piece;
  if(special==='ep') board[to+16*s.turn]='.';
  if(special==='castle') { const rf=to>from?from+3:from-4, rt=to>from?from+1:from-1; board[rt]=board[rf]; board[rf]='.'; }
  if(piece==='K') rights&=~3;
  if(piece==='k') rights&=~12;
  const rookRights = {119:1,112:2,7:4,0:8};
  if(piece.toLowerCase()==='r') rights &= ~(rookRights[from]||0);
  if(captured.toLowerCase()==='r') rights &= ~(rookRights[to]||0);
  return { board, turn:-s.turn, rights, ep:piece.toLowerCase()==='p'&&Math.abs(to-from)===32?(from+to)/2:-1,
    half:piece.toLowerCase()==='p'||captured!=='.'||special==='ep'?0:s.half+1, full:s.full+(s.turn===-1?1:0) };
}
function pseudo(s) {
  const out=[];
  for(let f=0;f<128;f++){
    if(!on(f) || side(s.board[f])!==s.turn) continue;
    const p=s.board[f].toLowerCase();
    const add=(t,flag='')=> { if(s.board[t].toLowerCase()==='k') return;
      if(p==='p' && ((t>>4)===0||(t>>4)===7)) for(const q of ['q','r','b','n']) out.push([f,t,q,flag]);
      else out.push([f,t,'',flag]); };
    if(p==='p'){
      const to=f-16*s.turn;
      if(on(to) && s.board[to]==='.'){
        add(to); const two=to-16*s.turn;
        if((f>>4)===(s.turn===1?6:1) && s.board[two]==='.') add(two);
      }
      for(const delta of [-1,1]){
        const t=to+delta; if(!on(t))continue;
        if(side(s.board[t])===-s.turn) add(t);
        else if(t===s.ep && s.board[t]==='.' && s.board[t+16*s.turn]===(s.turn===1?'p':'P')) add(t,'ep');
      }
    } else {
      for(const delta of (OFFSETS[p] || OFFSETS.k)){
        for(let t=f+delta;on(t);t+=delta){
          if(side(s.board[t])===s.turn) break;
          add(t);
          if(s.board[t]!=='.'||p==='n'||p==='k') break;
        }
      }
      const home=s.turn===1?116:4, rook=s.turn===1?'R':'r', flags=s.turn===1?[1,2]:[4,8];
      if(p==='k' && f===home && !isChecked(s)){
        if((s.rights & flags[0]) && s.board[f+3]===rook && s.board[f+1]==='.' && s.board[f+2]==='.' &&
            !isAttacked(s,f+1,-s.turn) && !isAttacked(s,f+2,-s.turn)) add(f+2,'castle');
        if((s.rights & flags[1]) && s.board[f-4]===rook && s.board[f-1]==='.' && s.board[f-2]==='.' && s.board[f-3]==='.' &&
            !isAttacked(s,f-1,-s.turn) && !isAttacked(s,f-2,-s.turn)) add(f-2,'castle');
      }
    }
  }
  return out;
}
export const legalMoves = s => pseudo(s).filter(m=>!isChecked(apply(s,m), s.turn));
export const findMove = (s,uci) => legalMoves(s).find(m=>moveKey(m)===uci);
export function playUci(s, uci) { const move=findMove(s,uci); if(!move) throw Error('Illegal move: '+uci); return apply(s,move); }
export function positionKey(s) {
  const ep = s.ep>=0 && legalMoves(s).some(m=>m[3]==='ep') ? s.ep : -1;
  return s.board.join('')+':'+s.turn+':'+s.rights+':'+ep;
}
export function insufficient(s) {
  const pieces=[];
  for(let i=0;i<128;i++) if(on(i) && s.board[i]!=='.' && s.board[i].toLowerCase()!=='k') pieces.push([s.board[i].toLowerCase(),((i>>4)+(i&7))%2]);
  return pieces.length===0 || (pieces.length===1 && ['n','b'].includes(pieces[0][0])) ||
      (pieces.every(p=>p[0]==='b') && new Set(pieces.map(p=>p[1])).size===1);
}
export function gameStatus(history) {
  const s=history.at(-1), moves=legalMoves(s), check=isChecked(s), count=history.filter(h=>positionKey(h)===positionKey(s)).length;
  if(!moves.length) return {done:true, message:check?'Checkmate — '+(s.turn===1?'Black':'White')+' wins':'Stalemate — draw'};
  if(insufficient(s)) return {done:true, message:'Draw — insufficient material'};
  if(s.half>=150 || count>=5) return {done:true,message:'Draw — '+(s.half>=150?'75-move rule':'fivefold repetition')};
  return {done:false,message:(s.turn===1?'White':'Black')+' to move'+(check?' · check':''),
    claim:s.half>=100?'50-move rule':count>=3?'threefold repetition':null};
}
export const initialState = () => parseFen(INITIAL_FEN);
