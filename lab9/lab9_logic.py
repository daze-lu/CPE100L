"""Shared Lab 9 Boolean logic, K-map helpers, and offline verification.

Imported by build_lab9.py; this module does not generate a report.
"""
from pathlib import Path
from itertools import product
from collections import Counter
import json

from sympy import symbols, SOPform, And, Or, Not, true, false

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'output' / 'pdf'
OUT.mkdir(parents=True, exist_ok=True)
V = symbols('D C B A')
SEG = 'abcdefg'
CHARS = list('0123456789AbCdEF')
# Every string is ordered a,b,c,d,e,f,g; zero lights the corresponding segment.
PATTERNS = ['0000001','1001111','0010010','0000110','1001100',
            '0100100','0100000','0001111','0000000','0000100',
            '0001000','1100000','0110001','1000010','0110000','0111000']
LETTERS = ['0001000', '1100010', '0110000', '1000010']
GRAYORDER = [0, 1, 3, 2]
COLOR = ['blue!75!black', 'red!75!black', 'teal!80!black', 'violet!85!black', 'orange!80!black']


def terms(e):
    return list(e.args) if e.func is Or else [e]


def literals(t):
    return list(t.args) if t.func is And else [t]


def cube(t):
    ls = literals(t)
    return tuple(1 if v in ls else 0 if Not(v) in ls else None for v in V)


def covered(c):
    return [n for n in range(16) if all(x is None or x == ((n >> (3-i)) & 1) for i,x in enumerate(c))]


def ev(e, n):
    return int(bool(e.subs(dict(zip(V, [(n >> k) & 1 for k in (3,2,1,0)])))))


def mathterm(t):
    if t == true:
        return '1'
    if t == false:
        return '0'
    c = cube(t)
    return ''.join(str(v) if bit else r'\overline{' + str(v) + '}' for v,bit in zip(V,c) if bit is not None)


def formula(e):
    return ' + '.join(mathterm(t) for t in terms(e))


def setstr(ns):
    return r'\{' + ','.join(map(str,ns)) + r'\}'


def optimum(ones, dc):
    """Independent exhaustive implicant enumeration and exact covering DP."""
    if not ones:
        return (0, 0)
    allowed = set(ones) | set(dc)
    candidates = []
    for c in product((None,0,1), repeat=4):
        cs = set(covered(c))
        if cs <= allowed and cs & set(ones):
            mask = sum(1 << i for i,n in enumerate(ones) if n in cs)
            candidates.append((mask, sum(x is not None for x in c)))
    dp = {0:(0,0)}
    target = (1 << len(ones))-1
    for mask in range(target+1):
        if mask not in dp:
            continue
        for cm,cl in candidates:
            nm = mask | cm
            cost = (dp[mask][0]+1, dp[mask][1]+cl)
            if cost < dp.get(nm,(1000,1000)):
                dp[nm] = cost
    return dp[target]


def make_function(name, ones, dc):
    e = SOPform(V, ones, dc)
    for n in set(range(16))-set(dc):
        assert ev(e,n) == int(n in ones), (name,n,e)
    cost = (len(terms(e)), sum(len(literals(t)) for t in terms(e)))
    opt = optimum(ones,dc)
    assert cost == opt, (name,cost,opt)
    return {'name':name, 'ones':ones, 'dc':dc, 'expr':e, 'cost':cost}


BCD = [make_function(s,[n for n in range(10) if PATTERNS[n][j]=='1'],list(range(10,16))) for j,s in enumerate(SEG)]
HEX = [make_function(s,[n for n in range(16) if PATTERNS[n][j]=='1'],[]) for j,s in enumerate(SEG)]
X3 = [make_function(f'z_{k}',[n for n in range(10) if (n+3)>>k&1],list(range(10,16))) for k in (3,2,1,0)]


def bank(fs):
    unique=[]
    for f in fs:
        for t in terms(f['expr']):
            if t not in unique:
                unique.append(t)
    return unique


def run_checks():
    count={}
    # Derive individual circuit output bits and compare to literal specification.
    for fs,valid,label in [(BCD,range(10),'bcd'),(HEX,range(16),'hex')]:
        for n in valid:
            actual=''.join(str(ev(f['expr'],n)) for f in fs)
            assert actual==PATTERNS[n], (label,n,actual)
        count[label+'_input_codes']=len(valid)
    for n in range(10):
        actual=sum(ev(f['expr'],n) << k for f,k in zip(X3,(3,2,1,0)))
        assert actual==n+3
        D,C,B,A=[n>>k&1 for k in (3,2,1,0)]
        temp=A|B
        factored=((D|(C&temp))<<3)|((C^temp)<<2)|((1^(A^B))<<1)|(1^A)
        assert factored==actual
    count['excess3_valid_inputs']=10
    previous=None
    for n in range(16):
        b=[n>>k&1 for k in (3,2,1,0)]
        g=(b[0]<<3)|((b[0]^b[1])<<2)|((b[1]^b[2])<<1)|(b[2]^b[3])
        assert g == n^(n>>1)
        if previous is not None:
            assert (g^previous).bit_count()==1
        previous=g
    count['gray_inputs']=16
    count['gray_adjacent_pairs']=15
    # Exhaustively verify gate-level ALU equations against integer operations.
    for s in range(4):
        for a in range(4):
            for b in range(4):
                a0,a1=a&1,a>>1
                b0,b1=b&1,b>>1
                c1=a0&b0
                t0=a0^b0
                t1=a1^b1^c1
                c2=(a1&b1)|(a1&c1)|(b1&c1)
                y0=[a0&b0,a0|b0,a0^b0,t0][s]
                y1=[a1&b1,a1|b1,a1^b1,t1][s]
                y2=c2 if s==3 else 0
                expected=[a&b,a|b,a^b,a+b][s]
                assert y0+2*y1+4*y2==expected
                assert ''.join(str(ev(f['expr'],expected)) for f in HEX)==PATTERNS[expected]
    count['alu_cases']=64
    for s in range(4):
        s1,s0=s>>1,s&1
        p=[s0,s1^s0,s1&(1-s0),(1-s1)&(1-s0),0,s0,0]
        assert ''.join(map(str,p))==LETTERS[s]
        # Alternative second-hex7seg plus OR-mode glyph override.
        D=s1|(1-s0)
        C=s1
        B=1-s0
        A=s1&s0
        code=8*D+4*C+2*B+A
        h=list(map(int,PATTERNS[code]))
        q=(1-s1)&s0
        result=[h[0]|q,h[1]|q,h[2],h[3],h[4],h[5]|q,h[6]&(1-q)]
        assert ''.join(map(str,result))==LETTERS[s]
    count['letter_codes']=4
    count['independent_sop_optimality_checks']=len(BCD)+len(HEX)+len(X3)
    data={'status':'PASS','scope':'offline Boolean equations and settled logical values only; no FPGA or Quartus execution',
          'counts':count,
          'functions':{label:[{'output':f['name'],'expression':str(f['expr']),
                         'on_set':f['ones'],'dont_cares':f['dc'],
                         'minimum_terms':f['cost'][0],'minimum_literals_at_minimum_terms':f['cost'][1]}
                         for f in fs] for label,fs in [('bcd',BCD),('hex',HEX),('excess3',X3)]}}
    (OUT/'verification.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    return data




def table(cols, head, rows, size=r'\small'):
    return (r'\begin{center}'+size+'\n'+r'\begin{tabular}{'+cols+'}\n'+r'\toprule'+'\n'+head+r'\\\midrule'+'\n'+
            '\n'.join(' & '.join(map(str,r))+r'\\' for r in rows)+'\n'+r'\bottomrule\end{tabular}\end{center}'+'\n')


def runs(vs):
    groups=[]
    for v in sorted(vs):
        if groups and v==groups[-1][-1]+1:
            groups[-1].append(v)
        else:
            groups.append([v])
    return groups


def kmap(f):
    # Split wraparound rectangles into boundary pieces; same color denotes same group.
    s=[r'\begin{tikzpicture}[x=0.95cm,y=0.8cm,font=\normalsize]',
       r'\draw[gray!70] (0,0) grid (4,4);',
       r'\node[anchor=east] at (-0.1,4.48) {$DC\backslash BA$};']
    for i,g in enumerate(GRAYORDER):
        s.append(fr'\node at ({i+.5},4.45) {{\texttt{{{g:02b}}}}};')
        s.append(fr'\node[anchor=east] at (-.15,{3.5-i}) {{\texttt{{{g:02b}}}}};')
    for ri,r in enumerate(GRAYORDER):
        for ci,c in enumerate(GRAYORDER):
            n=4*r+c
            val='X' if n in f['dc'] else str(int(n in f['ones']))
            s.append(fr'\node at ({ci+.5},{3.5-ri}) {{{val}}};')
            s.append(fr'\node[font=\tiny,text=gray,anchor=north west] at ({ci+.03},{4-ri-.02}) {{{n}}};')
    for ti,t in enumerate(terms(f['expr'])):
        cov=covered(cube(t))
        rs=[i for i,r in enumerate(GRAYORDER) if any(n//4==r for n in cov)]
        cs=[i for i,c in enumerate(GRAYORDER) if any(n%4==c for n in cov)]
        off=.07+.035*ti
        for rr in runs(rs):
            for cc in runs(cs):
                s.append(fr'\draw[{COLOR[ti]},line width=.85pt,rounded corners=3pt] ({min(cc)+off},{3-max(rr)+off}) rectangle ({max(cc)+1-off},{4-min(rr)-off});')
    s.append(r'\end{tikzpicture}')
    return '\n'.join(s)












def export_tables():
    import csv
    with (OUT/'theoretical_expected_results.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f)
        w.writerow(['input_decimal','DCBA','character','abcdefg_active_low','gfedcba_active_low','gray_g3g2g1g0','gray_changed_bit','excess3_if_valid','excess3_character_if_valid','measurement_status'])
        for n in range(16):
            g=n^(n>>1)
            bit='' if not n else 'g'+str((g^((n-1)^((n-1)>>1))).bit_length()-1)
            w.writerow([n,f'{n:04b}',CHARS[n],PATTERNS[n],PATTERNS[n][::-1],f'{g:04b}',bit,f'{n+3:04b}' if n<10 else 'dont-care',CHARS[n+3] if n<10 else 'dont-care','NOT_MEASURED'])


def export_vcd():
    lines=['$comment Offline zero-delay theoretical waveform; not ModelSim simulation. $end',
           '$timescale 1ns $end','$scope module theoretical_hex7seg $end']
    for k in range(4):
        lines.append(f'$var wire 1 d{k} d{k} $end')
    lines += ['$var wire 7 seg abcdefg_active_low $end','$var wire 4 inp DCBA $end',
              '$upscope $end','$enddefinitions $end']
    for n in range(16):
        lines.append(f'#{n*10}')
        lines += [f'{n>>k&1}d{k}' for k in range(4)]
        lines += [f'b{PATTERNS[n]} seg',f'b{n:04b} inp']
    lines.append('#160')
    (OUT/'theoretical_hex7seg.vcd').write_text('\n'.join(lines)+'\n',encoding='ascii')
