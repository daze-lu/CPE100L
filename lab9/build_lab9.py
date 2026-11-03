"""Generate the English Lab 9 report using the verified shared logic engine."""
from pathlib import Path
import json
import re
from report_web_references import append_references

import lab9_logic as logic

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'output' / 'pdf'
OUT.mkdir(parents=True, exist_ok=True)
logic.OUT = OUT
BCD, HEX, X3 = logic.BCD, logic.HEX, logic.X3
terms, literals, cube = logic.terms, logic.literals, logic.cube
formula, mathterm, bank = logic.formula, logic.mathterm, logic.bank
table, kmap, setstr = logic.table, logic.kmap, logic.setstr
PATTERNS, CHARS = logic.PATTERNS, logic.CHARS
T = []


def add(s):
    T.append(s)


def schematic(body, scale=1):
    return (r'\begin{center}\begin{tikzpicture}[>=Latex,block/.style={draw=ink,'
            r'rounded corners=2pt,fill=blue!4,minimum height=.9cm,align=center},'
            r'font=\small,scale=' + str(scale) + r',transform shape]' + '\n' + body +
            '\n' + r'\end{tikzpicture}\end{center}')


def function_card(f, title):
    add(r'\noindent\begin{minipage}{\textwidth}')
    add(r'\subsection*{' + title + '}')
    add(r'\noindent $' + f['name'] + r'=\sum m' + setstr(f['ones']) + '$; ' +
        (r'$\mathcal{D}=' + setstr(f['dc']) + '$.' if f['dc'] else "no don't-cares."))
    add(r'\begin{center}' + kmap(f) + r'\end{center}')
    rows=[]
    for i,t in enumerate(terms(f['expr'])):
        fixed=','.join(str(v)+'='+str(bit) for v,bit in zip(logic.V,cube(t)) if bit is not None)
        rows.append([fr'\textcolor{{{logic.COLOR[i]}}}{{$G_{{{i+1}}}$}}',
                     '$'+setstr(logic.covered(cube(t)))+'$', '$'+fixed+'$', '$'+mathterm(t)+'$'])
    add(table('clll',r'Group & Cells covered (incl. X) & Fixed variables & Product term',rows,r'\small'))
    add(r'\noindent OR the group terms: $\boxed{' + f['name'] + '=' + formula(f['expr']) + '}$.')
    add(fr'\noindent Cost: {f["cost"][0]} product term(s), {f["cost"][1]} literal(s).')
    add(r'\end{minipage}\par\vspace{0.25cm}')


def maps(fs, label):
    for i in range(0,len(fs),2):
        if i:
            add(r'\clearpage')
        for f in fs[i:i+2]:
            function_card(f,label+': output $'+f['name']+'$')


def bank_section(fs,prefix,title):
    bs=bank(fs)
    add(r'\clearpage\subsection{'+title+': complete gate connections}')
    add(r'''Generate $\overline D,\overline C,\overline B,\overline A$ with four shared
inverters, then distribute both polarities of the four inputs. Each row in the left table
defines one product node: use a multi-input AND for a multi-literal term, or a direct wire
for a single literal. The right table gives every output connection. Use an OR gate for
each sum of multiple nodes. These signals are already active-low segment controls;
do not invert all seven outputs again.''')
    left=table('cl',r'Node & AND inputs / direct wire',
               [[f'${prefix}_{{{i+1}}}$','$'+mathterm(t)+'$'] for i,t in enumerate(bs)],r'\small')
    rows=[]
    for f in fs:
        ids=[bs.index(t)+1 for t in terms(f['expr'])]
        rows.append(['$'+f['name']+'$','$'+'+'.join(f'{prefix}_{{{i}}}' for i in ids)+'$'])
    right=table('cl',r'Output & OR inputs / wire',rows,r'\small')
    add(r'\noindent\begin{minipage}[t]{0.47\textwidth}'+left+
        r'\end{minipage}\hfill\begin{minipage}[t]{0.49\textwidth}'+right+r'\end{minipage}')
    add(schematic(fr'''
\node[block] (in) at (0,0) {{$D,C,B,A$\\4 inputs}};
\node[block] (not) at (3.1,0) {{Invert and\\distribute}};
\node[block] (and) at (6.5,0) {{Shared AND layer\\${prefix}_1\ldots {prefix}_{{{len(bs)}}}$}};
\node[block] (or) at (10.1,0) {{Output OR layer\\$a,b,c,d,e,f,g$}};
\draw[->] (in)--(not);\draw[->] (not)--(and);\draw[->] (and)--(or);
''',.97))
    add('The block diagram shows the layers; the two tables specify all individual nets. '
        'An FPGA maps the logic to LUTs, so discrete gate counts are not Quartus LE counts.')


def segment_diagram():
    body=[]
    for s,x1,y1,x2,y2,where in [
        ('a',.25,2,1.25,2,'above'),('b',1.45,1.8,1.45,.9,'right'),
        ('c',1.45,.55,1.45,-.35,'right'),('d',.25,-.55,1.25,-.55,'below'),
        ('e',.05,.55,.05,-.35,'left'),('f',.05,1.8,.05,.9,'left'),
        ('g',.25,.72,1.25,.72,'above')]:
        body.append(fr'\draw[line width=4pt,accent] ({x1},{y1})--({x2},{y2}) node[midway,{where}=4pt,text=black] {{${s}$}};')
    body.append(r'''\node[align=left] at (6,.7) {$\mathrm{HEX}x[0]=a,\ \mathrm{HEX}x[1]=b$\\
$\mathrm{HEX}x[2]=c,\ \mathrm{HEX}x[3]=d$\\
$\mathrm{HEX}x[4]=e,\ \mathrm{HEX}x[5]=f$\\$\mathrm{HEX}x[6]=g$};''')
    return schematic('\n'.join(body))


def a_gate_diagram():
    body=[]
    for i,t in enumerate(terms(HEX[0]['expr'])):
        y=3-i*1.4
        body.append(fr'\node[and gate US,draw,logic gate inputs=nnnn,minimum width=1.1cm,minimum height=.75cm] (g{i}) at (4,{y}) {{}};')
        for j,(v,b) in enumerate((v,b) for v,b in zip(logic.V,cube(t)) if b is not None):
            lab=str(v) if b else r'\overline{'+str(v)+'}'
            body.append(fr'\draw (g{i}.input {j+1}) -- ++(-.6,0) node[left] {{${lab}$}};')
        body.append(fr'\draw[->] (g{i}.output) -- ++(.7,0) node[right] {{$u_{{{i+1}}}$}};')
    body.append(r'\node[or gate US,draw,logic gate inputs=nnnn,minimum width=1.1cm,minimum height=1.2cm] (og) at (9,1) {};')
    for i in range(4):
        body.append(fr'\draw (og.input {i+1}) -- ++(-.5,0) node[left] {{$u_{{{i+1}}}$}};')
    body.append(r'\draw[->] (og.output) -- ++(.7,0) node[right] {$a=\mathrm{HEX}[0]$};')
    return schematic('\n'.join(body))


def timing_diagram():
    body=[]
    for k in range(4):
        y=4-k*.72
        body.append(fr'\node[anchor=east] at (-.15,{y+.18}) {{$d_{k}$}};')
        pts=[(0,y)]
        last=0
        for n in range(16):
            bit=n>>k&1
            if bit!=last:
                pts.append((n*.65,y+bit*.36))
            pts.append(((n+1)*.65,y+bit*.36))
            last=bit
        body.append(r'\draw[ink,line width=.7pt] '+' -- '.join(f'({x},{yy})' for x,yy in pts)+';')
    for n in range(16):
        x=n*.65
        body += [fr'\draw[gray!30] ({x},0.3)--({x},4.5);',
                 fr'\node[font=\scriptsize] at ({x+.325},.7) {{{CHARS[n]}}};']
        if n%2==0:
            body.append(fr'\node[font=\tiny] at ({x},-.1) {{{n*10}}};')
    body.append(r'\node[anchor=east] at (-.15,.7) {Digit};\node at (10.5,-.1) {ns};')
    return schematic('\n'.join(body))


def generate():
    checks=logic.run_checks()
    add(r'''\documentclass[a4paper,11pt]{article}
\usepackage[margin=21mm,headheight=15pt]{geometry}
\usepackage[T1]{fontenc}
\usepackage{lmodern,amsmath,amssymb,booktabs,longtable,array}
\usepackage{tikz}
\usetikzlibrary{arrows.meta,positioning,calc,shapes.gates.logic.US}
\usepackage{xcolor,graphicx,fancyhdr,enumitem,hyperref}
\definecolor{ink}{HTML}{19354D}
\definecolor{accent}{HTML}{116B80}
\hypersetup{colorlinks=true,linkcolor=accent,urlcolor=accent,pdftitle={Lab 9: Seven-Segment Displays and Code Converters}}
\setlist{nosep,leftmargin=2em}
\setlength{\parskip}{0.4em}
\setlength{\emergencystretch}{2em}
\renewcommand{\arraystretch}{1.18}
\pagestyle{fancy}\fancyhf{}
\fancyhead[L]{\small CPE100L -- Lab 9}
\fancyhead[R]{\small Design and Analysis Report}
\fancyfoot[C]{\thepage}
\newcommand{\pending}{\textcolor{gray}{Pending}}
\newcommand{\photo}[1]{\begin{center}\fbox{\parbox[c][1.15cm][c]{0.9\linewidth}{\centering\small Photo to add: #1}}\end{center}}
\title{\textbf{Lab 9: Seven-Segment Displays\\and Code Converters}\\[0.5em]\large Complete Prelab and Postlab Derivations}
\author{Name: \underline{\hspace{3cm}}\qquad Student ID: \underline{\hspace{3cm}}}
\date{Course: CPE100L\qquad Experiment date: \underline{\hspace{2.5cm}}}
\begin{document}
\maketitle
\begin{center}\large\textcolor{accent}{Karnaugh maps -- Boolean minimization -- Circuit connections}\end{center}

\noindent\textbf{Scope of this report.} This English version contains the same design,
derivations, connection plans, expected results, and postlab answers as the Chinese version,
with exhaustive offline Boolean checks. Quartus compilation, ModelSim simulation, and
DE0-CV board testing have not been performed. Expected results are identified separately
from measurements. All diagrams are drawn in LaTeX/TikZ; board photographs, LE counts,
actual time spent, and TA sign-off remain to be supplied.

\noindent\textbf{Source and segment-pattern convention.} The task requirements come from
pages 4--7 of \texttt{CPE\_100\_Lab\_9.pdf}; the operation-select codes are confirmed by
pages 2--3 of the adjacent Lab 8 handout. On page 2 of Lab 9, the prose says that 6 omits
segment a and 9 omits segment d, but Table 2 assigns 0 to both positions, which lights them.
This report consistently follows the numeric entries in \textbf{Tables 2 and 3}: a is on
for 6, and d is on for 9. If the TA instead requires the prose convention, update the
truth table and repeat the minimization rather than mixing the two conventions.

\noindent\textbf{Experiment 3 diagram ambiguity.} The handout requests two
\texttt{hex7seg} symbols and also an independent letter decoder for HEX1. The direct
implementation here uses one \texttt{hex7seg} for the result on HEX0 and a separate
letter decoder for HEX1, because lowercase o is not a standard hexadecimal glyph.
Section~\ref{sec:lettervariant} also gives a complete alternative that retains a second
\texttt{hex7seg} and overrides its OR-mode glyph.

\clearpage\begingroup\small\setlength{\parskip}{0pt}\tableofcontents\endgroup
\clearpage
\section{Notation, segment patterns, and minimization method}
\subsection{Bit order and active-low outputs}
Define the display-decoder inputs as $D=d_3$, $C=d_2$, $B=d_1$, and $A=d_0$.
$D$ is the most significant bit and $A$ is the least significant bit. These names are
separate from the ALU operands $a_1a_0$ and $b_1b_0$.

Juxtaposition denotes AND, $+$ denotes Boolean OR, an overbar denotes NOT, and
$\oplus$ denotes XOR. Arithmetic addition is explicitly described as a sum or an ADD
operation. The segment vector is always written in the order $(a,b,c,d,e,f,g)$:
\textbf{0 turns a segment on; 1 turns it off}.
''')
    add(segment_diagram())
    add(r'''For a bus written as $\mathrm{HEX}x[6:0]$, the left-to-right bit string is
$gfedcba$. Reverse the $abcdefg$ strings in this report when writing that bus value.
The decimal point is not used.
\subsection{Complete target truth table}
The BCD decoder constrains only inputs 0--9; inputs 10--15 are X for all seven outputs.
The hexadecimal decoder constrains all sixteen inputs and has no don't-cares.
''')
    add(table('rccccc',r'Value & $DCBA$ & Glyph & $abcdefg$ & $gfedcba$ & Valid BCD?',[
        [n,fr'\texttt{{{n:04b}}}',CHARS[n],fr'\texttt{{{p}}}',fr'\texttt{{{p[::-1]}}}','Yes' if n<10 else 'No (X)']
        for n,p in enumerate(PATTERNS)]))
    add(r'''\clearpage\subsection{How to read and simplify every K-map}
\begin{enumerate}
\item Rows use $DC$ and columns use $BA$, both ordered $00,01,11,10$. The small gray
number inside each cell is its minterm index $m=8D+4C+2B+A$.
\item Enter the target output values. Since the functions being minimized are the
actual active-low outputs, \textbf{group the 1s, which mean segment off}. Do not group
the illuminated 0s for the SOP functions shown here. X cells may assist a group but
do not have to be covered.
\item Form rectangular groups of 1, 2, 4, 8, or 16 cells. Groups may overlap and wrap
across opposite boundaries, but cannot contain a specified 0. Boundary pieces of the
same color belong to one group.
\item Retain variables that remain fixed within a group. A fixed 1 gives the variable;
a fixed 0 gives its complement. Eliminate changing variables. A group of $2^k$ cells
eliminates $k$ variables. For example, $\{4,5,12,13\}$ fixes $C=1,B=0$, giving
$C\overline B$.
\item OR the product terms from the groups to obtain a sum of products (SOP). The table
under each map lists every group, its covered cells, its fixed variables, and the
resulting term. This supplies the elimination steps for each output.
\end{enumerate}

Each output is minimized independently: first minimize the number of terms, then the
number of literals among solutions with that term count. The supplied checker
independently enumerates all $3^4=81$ cubes and solves an exact covering problem by
dynamic programming. Sharing is then applied by reusing identical terms in the selected
SOPs. This is \textbf{not a claim of globally optimal multi-output logic}. Two-input gate
decomposition, fan-out, and FPGA LUT mapping use different cost models.

\clearpage\section{Prelab 1: BCD-to-seven-segment decoder}
For all seven functions, the don't-care set is
$\mathcal D=\{10,11,12,13,14,15\}$. The following maps show the full minimization.
''')
    maps(BCD,'BCD')
    bank_section(BCD,'p','BCD decoder')
    add(r'''\subsection{Sharing product terms between outputs}
Define
\[
P=C\overline A\overline B,\qquad Q=A\overline B\overline C\overline D,\qquad R=ABC.
\]
Then $a=P+Q$, $d=P+Q+R$, and $g=R+\overline B\overline C\overline D$.
Without sharing, $P$ and $Q$ are each generated separately for a and d; $R$ is generated
separately for d and g. Reusing each of these products saves \textbf{three multi-input
AND gates}, under the convention that one product is implemented by one AND gate.
The input inverters remain shared and the output OR gates are unchanged. For a single
example, sharing $P$ between a and d saves one three-input AND gate.

\clearpage\section{Prelab 2: complete hexadecimal decoder}
Combining digits 0--9 with A, b, C, d, E, and F defines all sixteen rows. There are no
don't-cares. Added rows can require either 0 or 1 for a segment, so a BCD grouping can
become invalid. For example, $C\overline A\overline B$ includes input 12, but glyph C
requires output a to be 0; therefore the corresponding a term needs an additional
$\overline D$ restriction.
''')
    maps(HEX,'Hex')
    bank_section(HEX,'q','hex7seg')
    add(r'\clearpage\subsection{Cost comparison}')
    rows=[['$'+b['name']+'$',b['cost'][0],h['cost'][0],b['cost'][1],h['cost'][1]] for b,h in zip(BCD,HEX)]
    rows.append(['Total',sum(f['cost'][0] for f in BCD),sum(f['cost'][0] for f in HEX),
                 sum(f['cost'][1] for f in BCD),sum(f['cost'][1] for f in HEX)])
    add(table('ccccc',r'Output & BCD terms & Hex terms & BCD literals & Hex literals',rows))
    add(table('lcc',r'After identical-term sharing & BCD & Hex',[
        ['Distinct product nodes (including direct wires)',len(bank(BCD)),len(bank(HEX))],
        ['Multi-input AND gates',sum(len(literals(t))>1 for t in bank(BCD)),sum(len(literals(t))>1 for t in bank(HEX))],
        ['Multi-input OR gates',sum(len(terms(f['expr']))>1 for f in BCD),sum(len(terms(f['expr']))>1 for f in HEX)],
        ['Input inverters',4,4],
        ['Product-layer literals after sharing',sum(len(literals(t)) for t in bank(BCD)),sum(len(literals(t)) for t in bank(HEX))],
        ['Quartus Total logic elements',r'\pending',r'\pending']]))
    add(r'''A literal is one occurrence of an input variable or its complement in a product;
OR connections are not counted as literals. Gate counts assume arbitrary fan-in.
The BCD term $A$ is a direct wire, not an AND gate. Exact FPGA LE counts cannot be
inferred from these abstract counts.

Experiment 1 also fixes $D=0$, enabling further synthesis simplification. Consequently,
its LE difference from Experiment 2 reflects both the input restriction and the
decoder change. A controlled BCD-versus-Hex comparison would retain four input ports,
the same FPGA target, and the same synthesis settings.
\subsection{Concrete gate circuit for hexadecimal segment a}
''')
    add(a_gate_diagram())
    add(r'''The four $u_i$ nets correspond, in order, to the four terms in the a expression.
Matching labels denote the same net. Construct the other six outputs using the full
connection tables; shared product nodes feed multiple output gates.''')
    add(r'''\clearpage\subsection{Theoretical timing for all sixteen codes}
The diagram below is a \textbf{zero-delay theoretical waveform}, not a ModelSim
screenshot. Start every input at 0 at $t=0$. Use periods of 20, 40, 80, and 160 ns for
$d_0,d_1,d_2,d_3$, each with a 50\% duty cycle. A new input code appears every 10 ns,
covering all sixteen codes during $[0,160)$ ns.
''')
    add(timing_diagram())
    add(table('cccc',r'Interval / ns & $DCBA$ & Expected glyph & Expected $abcdefg$',[
        [f'$[{10*n},{10*(n+1)})$',fr'\texttt{{{n:04b}}}',CHARS[n],fr'\texttt{{{PATTERNS[n]}}}'] for n in range(16)],r'\small'))
    add(r'''In a real simulation, sample after the combinational circuit settles, for
example at $5,15,\ldots,155$ ns. Different initial clock levels or phases change the
order of the codes; always interpret the input bus rather than assuming an order.

\clearpage\section{Prelab 3: result and operation-letter displays}
\subsection{Letter patterns and select logic}
Use the operation codes from Lab 8. Lowercase o uses segments c, d, e, and g, distinguishing
it from digit 0.
''')
    add(table('ccccc',r'$S_1S_0$ & Operation & Letter & Lit segments & $abcdefg$',[
        ['00','AND','A','a,b,c,e,f,g',r'\texttt{0001000}'],
        ['01','OR','o','c,d,e,g',r'\texttt{1100010}'],
        ['10','XOR','E','a,d,e,f,g',r'\texttt{0110000}'],
        ['11','ADD','d','b,c,d,e,g',r'\texttt{1000010}']]))
    add(r'''Let the HEX1 segment outputs be $\ell_a,\ldots,\ell_g$. Reading each column
of the four-row truth table gives
\begin{align*}
\ell_a&=S_0,&\ell_b&=S_1\oplus S_0,&\ell_c&=S_1\overline{S_0},\\
\ell_d&=\overline{S_1}\,\overline{S_0},&\ell_e&=0,&\ell_f&=S_0,&\ell_g&=0.
\end{align*}
For example, $\ell_c=1$ only for $S_1S_0=10$ (E); c is lit for the other letters.
Thus $\ell_c=S_1\overline{S_0}$. Outputs $\ell_a$ and $\ell_f$ share the $S_0$ wire.
''')
    add(schematic(r'''
\node[block] (s) at (0,0) {$S_1,S_0$};
\node[block] (l) at (4,0) {Letter decoder\\2 NOT, 2 AND, 1 XOR\\Other outputs: wires / 0};
\node[block] (h) at (9.5,0) {HEX1[0..6]\\$\ell_a\ldots\ell_g$};
\draw[->] (s)--(l);\draw[->] (l)-- node[above] {7 segment lines} (h);
'''))
    add(r'''Alternatively, use seven 4:1 multiplexers, one per segment. All share
$S_1,S_0$. Connect each column's four constants to $I_0,I_1,I_2,I_3$ in that order.
For a, the constants are $(0,1,0,1)$; for b, $(0,1,1,0)$; e and g are always 0.
\subsection{Alternative retaining a second hex7seg}\label{sec:lettervariant}
If two \texttt{hex7seg} instances are required at the top level, let the second initially
decode A, 0, E, and d. For $S_1S_0=00,01,10,11$, supply $1010,0000,1110,1101$,
respectively. The encoding logic is
\[
D_L=S_1+\overline{S_0},\quad C_L=S_1,\quad B_L=\overline{S_0},\quad A_L=S_1S_0.
\]
Let $q=\overline{S_1}S_0$, which is 1 only for OR, and let the second decoder outputs
be $h_a,\ldots,h_g$. Override the outputs as follows:
\[
\ell_a=h_a+q,\quad\ell_b=h_b+q,\quad\ell_f=h_f+q,\quad\ell_g=h_g\overline q,
\qquad\ell_c=h_c,\ \ell_d=h_d,\ \ell_e=h_e.
\]
For OR, this turns a, b, and f off and g on, changing 0 to o. The other three glyphs pass
unchanged. \textbf{Only the final override outputs drive HEX1; never connect two output
drivers together.} This alternative costs extra logic; the primary design uses the
direct letter decoder.

\clearpage\section{Prelab 4: binary-to-Gray and BCD-to-excess-3}
\subsection{Deriving the four Gray-code equations}
Let the binary input be $b_3b_2b_1b_0$. The most significant Gray bit equals the binary
MSB. Each remaining Gray bit indicates whether two neighboring binary bits differ:
\[
\boxed{g_3=b_3,\quad g_2=b_3\oplus b_2,\quad g_1=b_2\oplus b_1,\quad g_0=b_1\oplus b_0.}
\]
The XOR truth table is $00\mapsto0$, $01\mapsto1$, $10\mapsto1$, $11\mapsto0$.
Equal neighboring bits give 0; unequal bits give 1. In vector form,
$G=B\oplus(B\!\gg\!1)$. The circuit needs \textbf{three XOR gates and one direct wire};
no K-map is needed.
''')
    add(schematic(r'''
\draw[->] (0,3)--(7,3) node[right] {$g_3$};\node[left] at (0,3) {$b_3$};
\node[xor gate US,draw,logic gate inputs=nn,minimum width=1.2cm] (x2) at (5,1.7) {};
\node[xor gate US,draw,logic gate inputs=nn,minimum width=1.2cm] (x1) at (5,.2) {};
\node[xor gate US,draw,logic gate inputs=nn,minimum width=1.2cm] (x0) at (5,-1.3) {};
\draw (x2.input 1)--++(-1.2,0) node[left] {$b_3$};\draw (x2.input 2)--++(-1.2,0) node[left] {$b_2$};
\draw (x1.input 1)--++(-1.2,0) node[left] {$b_2$};\draw (x1.input 2)--++(-1.2,0) node[left] {$b_1$};
\draw (x0.input 1)--++(-1.2,0) node[left] {$b_1$};\draw (x0.input 2)--++(-1.2,0) node[left] {$b_0$};
\draw[->] (x2.output)--++(1.2,0) node[right] {$g_2$};
\draw[->] (x1.output)--++(1.2,0) node[right] {$g_1$};
\draw[->] (x0.output)--++(1.2,0) node[right] {$g_0$};
'''))
    add(r'''\subsection{Excess-3 truth table and bit-by-bit minimization}
Valid inputs are BCD digits 0--9. The target is $Z=\operatorname{value}(DCBA)+3$;
inputs 10--15 are don't-cares. Write the output as $z_3z_2z_1z_0$.
''')
    add(table('ccccc',r'Decimal & $DCBA$ & $z_3z_2z_1z_0$ & Hex glyph & Arithmetic',[
        [n,fr'\texttt{{{n:04b}}}',fr'\texttt{{{n+3:04b}}}',CHARS[n+3],f'${n}+3={n+3}$'] for n in range(10)]))
    add(r'\clearpage')
    maps(X3,'Excess-3')
    add(r'''\clearpage\subsection{Complete excess-3 connections}
Combining the four maps gives
\begin{align*}
z_3&=D+AC+BC=D+C(A+B),\\
z_2&=A\overline C+B\overline C+C\overline A\overline B
      =\overline C(A+B)+C\overline{(A+B)}=C\oplus(A+B),\\
z_1&=AB+\overline A\overline B=\overline{A\oplus B},\\
z_0&=\overline A.
\end{align*}
Introduce $T=A+B$ and $U=CT$ to reuse intermediate logic. These equations are specified
for valid BCD inputs only: \textbf{inputs 10--15 are not required to produce input plus 3}.
''')
    add(table('cll',r'Node & Gate / connection & Destination',[
        ['$T$',r'$\operatorname{OR}(A,B)$','AND input for $U$; XOR input for $z_2$'],
        ['$U$',r'$\operatorname{AND}(C,T)$','OR input for $z_3$'],
        ['$z_3$',r'$\operatorname{OR}(D,U)$','Output MSB'],
        ['$z_2$',r'$\operatorname{XOR}(C,T)$','Output bit 2'],
        ['$z_1$',r'$\operatorname{XNOR}(A,B)$','Output bit 1'],
        ['$z_0$',r'$\operatorname{NOT}(A)$','Output LSB']]))
    add(schematic(r'''
\node[block] (ab) at (0,2) {$A,B$};\node[block] (t) at (3,2) {OR\\$T=A+B$};
\node[block] (u) at (6,3.3) {AND\\$U=CT$};\node[block] (z3) at (9,3.3) {OR\\$z_3=D+U$};
\node[block] (z2) at (6,1) {XOR\\$z_2=C\oplus T$};
\node[block] (z1) at (3,-.4) {XNOR\\$z_1=\overline{A\oplus B}$};
\node[block] (z0) at (7,-.4) {NOT\\$z_0=\overline A$};
\draw[->] (ab)--(t);\draw[->] (t.east)-|(u.south);\draw[->] (t.east)-|(z2.north);
\draw[->] (u)--(z3);\draw[->] (6,4.6) node[above] {$C$}--(u);
\draw[->] (9,4.6) node[above] {$D$}--(z3);
\draw[->] (8,1) node[right] {$C$} -- (z2.east);
\draw[->] (0,-.4) node[left] {$A,B$}--(z1);
\draw[->] (5.2,-.4) node[left] {$A$}--(z0);
''',.95))
    add(r'''If an XNOR gate is unavailable, use XOR followed by NOT. This factored network
is multilevel, so its gate cost differs from the independent two-level SOP term count.
\subsection{Prelab question: common anode or common cathode?}
Table 2 represents a \textbf{common-anode display with active-low controls}, as specified
by the handout. For example, digit 0 lights a--f, whose entries are all 0, while g is 1
and stays off. A common-cathode interface normally uses active-high segment signals;
invert the seven outputs if the target interface requires the opposite polarity.

\clearpage\section{Postlab: operating principles and experiment connections}
\subsection{Operating principles, time, and handout issues}
All circuits are combinational. A decoder maps a numeric input to seven segment-control
bits; the ALU produces a numeric result for the selected operation; Gray and excess-3
converters change the representation. After propagation settles, the outputs depend
only on the current inputs. No board clock or register is required. The clocks in the
timing example are simulation stimuli for input enumeration.

Actual total time spent: \underline{\hspace{2cm}} hours.\quad
TA demonstration / sign-off: \underline{\hspace{3cm}}.

Handout issues include the prose/Table 2 conflict for digits 6 and 9, and the unclear
relationship between two \texttt{hex7seg} symbols and the separate letter decoder in
Experiment 3. In Experiment 4, ``a third hex7seg'' should not be read as requiring two
unused instances in that independent project: only two are needed, for HEX2 and HEX3.
\subsection{Global connection rules}
\begin{itemize}
\item This report specifies \textbf{logical board ports}: SW, KEY, LEDR, and HEX.
Physical FPGA \texttt{PIN\_xxx} assignments must come from the course's matching DE0-CV
pin table. Those physical pin numbers have not been checked or invented here.
\item To blank an unused seven-segment display, set all seven outputs to 1. Unused
LEDs may be set to 0. Use explicit logic constants for 0 and 1; do not leave inputs floating.
\item This design inverts each active-low KEY input:
$a_1=\overline{KEY3}$, $a_0=\overline{KEY2}$,
$b_1=\overline{KEY1}$, $b_0=\overline{KEY0}$.
Thus a pressed button represents operand bit 1 and a released button represents 0.
\item Connect by segment index: a to [0], through g to [6]. Do not confuse an
$abcdefg$ pattern with the order of the bus $[6:0]$.
\end{itemize}
\subsection{Experiment 1: displaying a three-bit number}
Use the BCD decoder with $D=0$, $C=SW2$, $B=SW1$, and $A=SW0$. Connect outputs a--g
to HEX0[0]--HEX0[6], respectively. Generate each complemented input with NOT gates.
''')
    add(schematic(r'''
\node[block] (sw) at (0,0) {SW2, SW1, SW0\\$C,B,A$};
\node[block] (dec) at (4.5,0) {BCD decoder\\$D=0$};
\node[block] (hex) at (9,0) {HEX0\\Digits 0--7};
\draw[->] (sw)--(dec);\draw[->] (dec)-- node[above] {$a\ldots g$} (hex);
'''))
    add('Set the switches to each value from 000 through 111. Compare the settled display '
        'with the expected digit, and record the actual observation separately.')
    add(table('ccccc',r'SW2 SW1 SW0 & Expected digit & $abcdefg$ & Actual HEX0 & Match?',[
        [fr'\texttt{{{n:03b}}}',n,fr'\texttt{{{PATTERNS[n]}}}',r'\pending',r'\pending'] for n in range(8)]))
    add(r'\photo{HEX0 showing a digit, with the corresponding switch positions visible.}')
    add(r'''\subsection{Experiment 2: complete hexadecimal display}
Replace the BCD decoder with \texttt{hex7seg}. Keep the lower three switch connections
and connect $D$ to SW3. Output a still goes to HEX0[0], through g to HEX0[6]. Verify all
sixteen rows in the target table.
''')
    add(table('ccccc',r'SW3--SW0 & Expected glyph & $abcdefg$ & Actual HEX0 & Match?',[
        [fr'\texttt{{{n:04b}}}',CHARS[n],fr'\texttt{{{PATTERNS[n]}}}',r'\pending',r'\pending'] for n in range(16)],r'\small'))
    add(r'\photo{HEX0 displaying one of A, b, C, d, E, or F.}')
    add(r'''Experiment 1 LE count: \underline{\hspace{1.5cm}}.\quad
Experiment 2 LE count: \underline{\hspace{1.5cm}}.
Adding hexadecimal constraints reduces minimization freedom; the selected independent
SOPs increase from 15 to 25 terms. Whether the mapped FPGA LE count increases, and by
how much, requires actual compilation reports from the same tool environment.

\clearpage\subsection{Experiment 3: two-bit ALU and two displays}
\textbf{Input and output connections.} Invert the four KEY signals as described above.
Connect $S_1=SW1$, $S_0=SW0$. Connect ALU outputs $y_2,y_1,y_0$ to decoder inputs
$C,B,A$, tie $D=0$, and send its segment outputs to HEX0. Send $S_1,S_0$ also to the
letter decoder and connect its seven outputs to HEX1.
''')
    add(schematic(r'''
\node[block] (key) at (0,2) {KEY3..KEY0\\Active-low};
\node[block] (inv) at (3,2) {4 NOT gates\\Pressed = 1};
\node[block] (alu) at (6.1,2) {2-bit ALU\\$y_2y_1y_0$};
\node[block] (dec) at (9.4,2) {hex7seg\\$D=0$};
\node[block] (h0) at (9.4,4) {HEX0: result};
\node[block] (sw) at (3,-.6) {SW1, SW0\\$S_1,S_0$};
\node[block] (ld) at (6.1,-.6) {Letter decoder\\$\ell_a\ldots\ell_g$};
\node[block] (h1) at (9.4,-.6) {HEX1: A/o/E/d};
\draw[->] (key)--(inv);\draw[->] (inv)--(alu);\draw[->] (alu)--(dec);\draw[->] (dec)--(h0);
\draw[->] (sw)--(ld);\draw[->] (ld)--(h1);
\draw[->] (sw.north) -- ++(0,.6) -| (alu.south);
''',.96))
    add(r'''\textbf{Complete ALU logic.} The following equations allow reconstruction
without an existing Quartus project. First form the two-bit arithmetic sum:
\begin{align*}
t_0&=a_0\oplus b_0,&c_1&=a_0b_0,\\
t_1&=a_1\oplus b_1\oplus c_1,&c_2&=a_1b_1+a_1c_1+b_1c_1.
\end{align*}
For $i=0,1$, use one 4:1 MUX with $I_0=a_ib_i$, $I_1=a_i+b_i$,
$I_2=a_i\oplus b_i$, and $I_3=t_i$. Both MUXs share $S_1,S_0$; their outputs are
$y_i$. The highest result bit is $y_2=S_1S_0c_2$, forcing it to 0 for logic operations.
This implementation is functionally equivalent to the two-slice ALU in Lab 8.

\textbf{Button example.} For arithmetic $3+3=6$, set SW1=SW0=1 and press all four
buttons. After inversion, $a=b=11$ and $y=110$. HEX0 should display 6 and HEX1 should
display d. Since HEX1 is to the left of HEX0, the board reads ``d6'' from left to right.

\clearpage\subsubsection*{Complete theoretical results: all 64 ALU cases}
Each result is $y_2y_1y_0$. The displayed digit is the unsigned value of those three
bits. All entries below are theoretical expectations; the last column is for measurement.
''')
    rows=[]
    for a in range(4):
        for b in range(4):
            rows.append([fr'\texttt{{{a:02b}}}',fr'\texttt{{{b:02b}}}',
                         *[fr'\texttt{{{n:03b}}}' for n in (a&b,a|b,a^b,a+b)],r'\pending'])
    add(table('ccccccc',r'$a_1a_0$ & $b_1b_0$ & AND / A & OR / o & XOR / E & ADD / d & Measured?',rows,r'\small'))
    add(r'''Sixteen operand pairs times four modes give 64 cases. ADD ranges from 0 to 6;
logic results range from 0 to 3. Include carry cases such as $1+3$, $2+2$, $2+3$, and
$3+3$, and confirm $y_2=0$ in each logic mode.''')
    add(r'\photo{an ADD result greater than 3 with d beside it, for example HEX1=d and HEX0=6.}')
    add(r'''\subsubsection*{Description of the letter decoder}
The design assigns active-low patterns to $00\to A$, $01\to o$, $10\to E$,
$11\to d$, then simplifies each segment function. It uses one XOR, two two-input ANDs,
and two NOTs; a/f share the $S_0$ wire and e/g share constant 0. The same select inputs
drive the ALU and the letters, so the operation label tracks the selected function.
If the second-hex7seg override circuit is used, describe that actual implementation instead.

\clearpage\subsection{Experiment 4: two converters sharing one input}
\textbf{Connections:}
\begin{enumerate}
\item Set $b_3=SW3$, $b_2=SW2$, $b_1=SW1$, $b_0=SW0$. Fan out these signals to
the Gray converter, the excess-3 converter, and the input-display decoder.
\item Connect $g_3,g_2,g_1,g_0$ to LEDR3, LEDR2, LEDR1, LEDR0, respectively.
\item Connect $b_3,b_2,b_1,b_0$ to $D,C,B,A$ of one hex7seg; connect its outputs to HEX2.
\item Connect $z_3,z_2,z_1,z_0$ to $D,C,B,A$ of another hex7seg; connect its outputs
to HEX3. Do not tie $z_3$ to 0: unlike Experiment 1, the full four-bit value is required.
\end{enumerate}
''')
    add(schematic(r'''
\node[block] (sw) at (0,0) {SW3..SW0\\$b_3b_2b_1b_0$};
\node[block] (gr) at (4.1,2) {Binary to Gray};
\node[block] (led) at (9,2) {LEDR3..LEDR0\\$g_3g_2g_1g_0$};
\node[block] (inhex) at (4.1,0) {hex7seg\\Input value};
\node[block] (h2) at (9,0) {HEX2};
\node[block] (x3) at (4.1,-2) {BCD to excess-3};
\node[block] (outhex) at (7.3,-2) {hex7seg\\$z_3z_2z_1z_0$};
\node[block] (h3) at (10.2,-2) {HEX3};
\draw[->] (sw.east)--++(.6,0)|-(gr.west);\draw[->] (gr)--(led);
\draw[->] (sw)--(inhex);\draw[->] (inhex)--(h2);
\draw[->] (sw.east)--++(.6,0)|-(x3.west);\draw[->] (x3)--(outhex);\draw[->] (outhex)--(h3);
''',.96))
    add(r'''\subsubsection*{Gray-code results and the changed bit}
The changed bit compares two consecutive \textbf{settled} Gray outputs. XOR the current
code with the previous code to locate that bit. The first row has no predecessor.
''')
    rows=[]
    for n in range(16):
        g=n^(n>>1)
        delta='None (first)' if not n else '$g_'+str((g^((n-1)^((n-1)>>1))).bit_length()-1)+'$'
        rows.append([fr'\texttt{{{n:04b}}}',fr'\texttt{{{g:04b}}}',delta,r'\pending',r'\pending'])
    add(table('ccccc',r'$b_3b_2b_1b_0$ & Expected $g_3g_2g_1g_0$ & Changed bit & Actual LEDs & Match?',rows,r'\small'))
    add(r'''\textbf{Transient behavior.} Adjacent target Gray codes differ in one bit,
but this combinational converter is not guaranteed glitch-free during mechanical
switch changes. Changing binary 0111 to 1000 requires four switches and can pass through
other intermediate inputs. Compare outputs only after the intended input has settled.
Synchronous sampling, debouncing, or a direct Gray-sequence generator would be needed
for stronger timing requirements.
\subsubsection*{Excess-3 display results}
''')
    add(table('cccccc',r'Input & BCD & Excess-3 & Expected HEX2 & Expected HEX3 & Measured?',[
        [n,fr'\texttt{{{n:04b}}}',fr'\texttt{{{n+3:04b}}}',CHARS[n],CHARS[n+3],r'\pending'] for n in range(10)],r'\small'))
    add(r'''For input 5, HEX2 shows 5 and HEX3 shows 8. For inputs 7, 8, and 9, HEX3
shows A, b, and C. It displays the four-bit excess-3 code as a hexadecimal glyph;
it does not expand values 10--12 into two decimal digits. Gray remains defined for
inputs 10--15, but those inputs are invalid BCD and are outside excess-3 acceptance.
''')
    add(r'\photo{HEX2 showing input 5 and HEX3 showing the corresponding excess-3 value 8.}')
    add(r'''\clearpage\section{Postlab: answers to the four questions}
\subsection{Why does the two-bit sum fit one digit? What about a three-bit ALU?}
Unsigned two-bit operands range from 0 to 3, so the maximum sum is $3+3=6=110_2$.
Three binary result bits are needed, but the numeric value is less than 10, so one
decimal seven-segment digit is sufficient.

Unsigned three-bit operands range from 0 to 7, giving a maximum sum of $7+7=14=1110_2$.
The result needs four binary bits. For \textbf{decimal display}, use two digits and
binary-to-decimal/BCD conversion: for $N\in[0,14]$, set the tens digit to
$t=[N\ge10]$ and the units digit to $u=N-10t$, then decode t and u separately.
For \textbf{hexadecimal display}, one existing hex7seg is still sufficient; the maximum
value 14 appears as E. Therefore, two display digits are required for decimal output,
not for every possible output base.
\subsection{Which product term was shared, and how many gates were saved?}
The BCD functions include
\[
a=C\overline A\overline B+A\overline B\overline C\overline D,\qquad
d=C\overline A\overline B+A\overline B\overline C\overline D+ABC.
\]
Sharing the first two terms saves two multi-input AND gates. Sharing $ABC$ between d
and g saves one more, for \textbf{three saved AND gates} under the stated cost model.

For one specific example, $C\overline A\overline B$ is reused by a and d, reducing two
three-input ANDs to one. If only two-input ANDs are allowed, a three-literal product
normally needs two cascaded ANDs, so sharing that product would save two two-input
ANDs instead. State the counting convention. Fan-out buffers are excluded, and these
numbers do not directly determine FPGA LE savings.
\subsection{Why can six extra hexadecimal rows increase decoder cost?}
BCD inputs 10--15 are don't-cares and can be assigned whichever values aid simplification.
Hexadecimal decoding fixes them to letter patterns. Some large groups extending into
the don't-care region become invalid and must be replaced by smaller groups, increasing
terms or literals. The number of \textbf{input constraints} increases even though the
number of outputs stays seven.

Here the selected independently minimized SOPs rise from 15 to 25 total terms. Individual
outputs, alternative glyph choices, or mapped FPGA LE counts need not increase strictly.
For a fixed exact cost model, adding constraints cannot enlarge the feasible implementation
set; the BCD function could already use a full Hex implementation, but its don't-cares
allow a cheaper choice.
\subsection{Why are K-map rows and columns labeled in Gray order?}
The order $00,01,11,10$ makes each adjacent pair differ in exactly one variable, including
the wraparound pair. Thus adjacent minterms can combine using
$XY+X\overline Y=X$, eliminating one variable. Four-cell and eight-cell groups eliminate
two and three variables, respectively.

In ordinary binary order $00,01,10,11$, adjacent labels 01 and 10 differ in two variables.
Treating them as a valid adjacent pair could include unwanted zero minterms, so that
ordering does not support the standard rectangular grouping rule.

\clearpage\section{Verification, conclusions, and remaining evidence}
\subsection{Offline checks actually performed}
The supplied Python generator uses the shared logic engine to generate SOPs with SymPy,
then independently enumerates all cubes and solves an exact covering problem to check
minimum term counts and their minimum literal counts. It evaluates every required
input and compares the ALU gate equations with integer operations.
''')
    add(table('lc',r'Check & Passed cases',[
        ['Valid BCD inputs (all seven segments per input)',10],
        ['All Hex inputs (all seven segments per input)',16],
        ['Valid excess-3 inputs (all four bits per input)',10],
        ['Gray inputs / consecutive settled pairs','16 / 15'],
        ['ALU cases (result and resulting segment pattern)',64],
        ['Letter-select modes, including the override alternative',4],
        ['Independent SOP cost checks',18]]))
    add(r'''The actual results are saved in \texttt{verification.json}. PASS applies to
\textbf{offline Boolean functionality and the specified SOP cost criterion}. It does
not establish FPGA timing, physical pin correctness, LE counts, button debouncing,
or observed display behavior. The theoretical waveform was not run in ModelSim.
\subsection{Design-stage conclusions}
The design derives both BCD and full hexadecimal active-low seven-segment logic.
Don't-cares enable larger K-map groups, while shared product terms reduce duplicated
logic. The letter decoder maps the operation selection to A/o/E/d, and the result
decoder preserves the three-bit ALU result, including the ADD carry. Three adjacent-bit
XORs implement binary-to-Gray conversion; the excess-3 circuit reuses the intermediate
term $A+B$ through factoring.

The main design issues are output polarity, bus bit order, active-low buttons, the
valid BCD domain, decimal versus hexadecimal display, and the distinction between
Gray-code steady-state properties and switching transients. The equations agree with
offline checks. Hardware agreement still requires the listed experiments. This is a
\textbf{design-stage conclusion}, not a claim that the board experiments have been completed.
\subsection{Complete after actual experimentation}
\begin{itemize}
\item Actual problems encountered: \underline{\hspace{8cm}}
\item How they were resolved: \underline{\hspace{8cm}}
\item Measured differences from theory and causes: \underline{\hspace{5cm}}
\item Total time and TA demonstration record: \underline{\hspace{6cm}}
\end{itemize}
\subsection{Submission requirements and current status}
''')
    add(table(r'>{\raggedright\arraybackslash}p{4.2cm}>{\raggedright\arraybackslash}p{10.1cm}',r'Required material & Current status / remaining work',[
        ['BCD and Hex K-maps','Complete: 14 maps, group elimination, expressions, and shared products.'],
        ['Gray and excess-3 derivations','Complete, including four additional excess-3 K-maps.'],
        ['Schematics and connections','Complete: TikZ diagrams, gate connection tables, and logical board-port mapping.'],
        ['Simulation waveform','Theoretical timing and patterns supplied. A genuine ModelSim screenshot still requires execution.'],
        ['Quartus screenshots and projects','Not created or connected, as requested. These drawings are not Quartus screenshots.'],
        ['Board measurements, photos, and LE counts','Pending actual experiments; all measurement columns are explicitly marked.'],
        ['Postlab questions and conclusions','All four answers and design conclusions are complete. Add actual laboratory experience later.'],
        ['Three project archives and links','Provide actual decoder, ALU-display, and converter projects when available. This document package is not a substitute for those projects.']
    ],r'\small'))
    add(r'''\appendix
\clearpage\section{Compilation and reproduction without Quartus}
The file \texttt{lab9\_prelab\_postlab.tex} is self-contained: all diagrams use TikZ,
with no external image dependencies. Compile it with XeLaTeX three times to update
the contents and cross-references:
\begin{verbatim}
xelatex -interaction=nonstopmode -halt-on-error lab9_prelab_postlab.tex
xelatex -interaction=nonstopmode -halt-on-error lab9_prelab_postlab.tex
xelatex -interaction=nonstopmode -halt-on-error lab9_prelab_postlab.tex
\end{verbatim}
The English version uses the standard article class and Latin Modern fonts; no Chinese
fonts or ctex package are required. On Overleaf, select XeLaTeX and upload the .tex file.
Common math packages, TikZ, booktabs, fancyhdr, enumitem, and hyperref are required.

Alternatively, run \texttt{build\_pdf.ps1} from the package root in PowerShell.
To regenerate the derivations, checks, CSV, and theoretical VCD, use Python 3.10 or later:
\begin{verbatim}
python -m pip install sympy
python build_lab9.py
\end{verbatim}
Keep \texttt{lab9\_logic.py} beside the English generator: it supplies the shared logic
engine and is imported without generating the Chinese report. Regenerating overwrites
the English .tex file, so back up hand edits first. The VCD contains zero-delay theoretical
values; the CSV contains expected answers, not board observations.

\section{Source files and page references}
\begin{enumerate}
\item \texttt{CPE\_100\_Lab\_9.pdf}: page 2, Table 2 (BCD patterns); page 3,
Table 3 (hexadecimal extension); page 4 (prelab, Gray, and excess-3); pages 5--6
(experiments and connections); page 7 (postlab, grading, and attachments).
\item Adjacent \texttt{lab8/CPE\_100\_Lab\_8.pdf}: page 2, Table 2 (operation codes
00/01/10/11); page 3 (the two-bit ALU and its carry/result outputs).
\end{enumerate}
\end{document}
''')
    tex='\n\n'.join(T)
    tex=tex.replace('All diagrams are drawn in LaTeX/TikZ; board photographs, LE counts,',
                    'Design diagrams use LaTeX/TikZ; the appendix adds attributed external circuit illustrations. Board photographs, LE counts,')
    tex=tex.replace('is self-contained: all diagrams use TikZ,\nwith no external image dependencies.',
                    'uses TikZ for the design diagrams and a companion images folder for the external reference illustrations. Keep that folder beside the .tex file when compiling.')
    tex=tex.replace('select XeLaTeX and upload the .tex file.',
                    'select XeLaTeX and upload the .tex file together with its images folder.')
    tex=append_references(tex, 'en', OUT)
    assert not re.search(r'[\u3400-\u9fff]',tex), 'Unexpected untranslated text'
    assert tex.count('Cells covered (incl. X)')==18
    target=OUT/'lab9_prelab_postlab.tex'
    target.write_text(tex,encoding='utf-8')
    logic.export_tables()
    logic.export_vcd()
    print(json.dumps({'status':'PASS','tex':str(target),'maps':18,'verification':checks['counts']},indent=2))


if __name__=='__main__':
    generate()
