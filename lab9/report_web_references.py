"""Attributed circuit illustrations and links for the English report generator."""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
URLS = {
    'bcd': 'https://github.com/jrmmendes/block-diagram-digital-clock/blob/master/modules/decoders/bcd_to_7segd.bdf',
    'hex': 'https://nathanabelortiz.github.io/projects/fpga-hex7.html',
    'hex_image': 'https://nathanabelortiz.github.io/assets/projects/fpga/hex7-schematic.png',
    'alu_bdf': 'https://github.com/shashwatKanth04/Altera-Quartus-2-Basic-Designs/blob/main/ALU.bdf',
    'alu': 'https://scalable.uni-jena.de/opt/ehp/chapters/assignment_alu.html',
    'alu_image': 'https://scalable.uni-jena.de/opt/ehp/_images/alu_basic.svg',
    'gray': 'https://embarcados.com.br/tutorial-de-verilog-codigo-binario-para-codigo-gray/',
    'gray_image': 'https://embarcados.com.br/wp-content/uploads/2015/11/gray-7.png',
    'excess_image': 'https://github.com/Mmamoonn/code-conversion-system/blob/main/hardware/circuit-diagrams/final_circuit_diagram.jpeg',
    'excess': 'https://github.com/Mmamoonn/code-conversion-system/blob/main/vhdl/src/bcdtoex3.vhd',
    'gray_code': 'https://github.com/Mmamoonn/code-conversion-system/blob/main/vhdl/src/bcdtogray.vhd',
}
ASSETS = ('hex7-schematic.png', 'alu-basic.png', 'gray-4bit.png', 'converters-combined.jpeg')


def links(items):
    return '\n'.join(r'\par\noindent ' + title + r':\par\nopagebreak[4]{\footnotesize\noindent\url{' + URLS[key] + r'}\par}\smallskip' + '\n'
                     for title, key in items)


def picture(name, caption, height):
    return (r'\par\begin{center}' + '\n' +
            r'\includegraphics[width=\linewidth,height=' + height +
            r'\textheight,keepaspectratio]{images/' + name + '}\n' +
            r'\par\vspace{.4em}\begin{minipage}{\linewidth}\small\refstepcounter{figure}\figurename~\thefigure: ' + caption + '\n' +
            r'\end{minipage}\end{center}\par' + '\n')


def append_references(tex, lang, out):
    images = out / 'images'
    images.mkdir(parents=True, exist_ok=True)
    # Packaged images allow regeneration without network access.
    for name in ASSETS:
        if not (images / name).exists():
            shutil.copy2(ROOT / 'tmp' / 'web-reference-images' / name, images / name)
    graphicspath = r'\graphicspath{{' + out.relative_to(ROOT).as_posix() + r'/}{./}}'
    tex = tex.replace(r'\begin{document}', graphicspath + '\n' + r'\begin{document}', 1)
    if lang != 'en':
        raise ValueError('Only the English report is supported.')
    else:
        appendix = r'''
\clearpage\section{Online circuit illustrations and source links}\label{app:webrefs}
This appendix collects the public circuit references discussed alongside the report.
URLs below each illustration are clickable. Author attribution and scope differences
are retained. These external examples do not establish compilation or board testing
of the designs in this report.
\subsection{Experiments 1 and 2: BCD and full hexadecimal decoders}
The BCD reference supplies a native Quartus BDF file, which requires Quartus to view.
The report's own derivations and connections remain the design for Experiment 1.
The illustration below is Nathan Abel Ortiz's full hexadecimal gate-level decoder,
useful for Experiment 2. It supports 0--F and is not the same minimization as a
BCD-only 0--9 decoder. Check its glyph conventions against this report's target table.
'''
        appendix += picture('hex7-schematic.png', "Nathan Abel Ortiz's Quartus hexadecimal seven-segment decoder (external reference).", '.43')
        appendix += links([('Experiment 1: native BCD BDF', 'bcd'), ('Experiment 2: author project page', 'hex'), ('Original image', 'hex_image')])
        appendix += r'''
\clearpage\subsection{Experiment 3: ALU organization and display connections}
The illustration below comes from the University of Jena's Experimental Hardware
Projects course. It shows the operation branches and result selection of a
parameterized ALU. The original diagram illustrates 64 bits; the board exercise
uses four-bit inputs and ADD/SUB/AND/OR. \textbf{Our experiment uses two-bit inputs
and 00 AND, 01 OR, 10 XOR, 11 ADD.} Adapt both the width and control mapping.
'''
        appendix += picture('alu-basic.png', 'ALU structure from the University of Jena course (original SVG converted to PNG).', '.24')
        appendix += links([('Course page: circuit and display integration', 'alu'), ('Original SVG', 'alu_image'), ('Separate four-bit Quartus ALU.bdf example', 'alu_bdf')])
        appendix += r'''
The linked BDF contains AND, OR, XOR, arithmetic, and selection blocks and can serve
as a hierarchy reference. Its width and functions still need adaptation. A public
top-level diagram exactly matching our result on HEX0 and A/o/E/d on HEX1 was not
found. Use this report's Experiment 3 dual-display diagram and letter-decoder logic
for those connections.
\clearpage\subsection{Experiment 4: correct four-bit binary-to-Gray circuit}
This diagram is from Thiago Lima's Embarcados tutorial. The most significant bit
passes through; three XOR gates compute the remaining outputs for all 16 inputs.
The article implements the circuit in Verilog. The same gates can be placed
individually in a Quartus BDF schematic.
'''
        appendix += picture('gray-4bit.png', 'Four-bit binary-to-Gray converter: three adjacent-bit XORs and one direct wire. Source: Thiago Lima / Embarcados.', '.37')
        appendix += links([('Tutorial and code', 'gray'), ('Original image', 'gray_image')])
        appendix += r'''
For this experiment, connect SW3--SW0 to the inputs and LEDR3--LEDR0 to the outputs:
\[g_3=b_3,\quad g_2=b_3\oplus b_2,\quad g_1=b_2\oplus b_1,\quad g_0=b_1\oplus b_0.\]
\clearpage\subsection{Experiment 4: BCD-to-excess-3 gate reference}
The hand-drawn diagram below is from Mmamoonn/code-conversion-system. Its lower
half implements excess-3; the upper half shows Gray conversion. This reference
drawing is \textbf{not a Quartus screenshot}.
'''
        appendix += picture('converters-combined.jpeg', 'Combined Gray and excess-3 reference drawing. Source: GitHub user Mmamoonn. The lower half is the excess-3 circuit.', '.52')
        appendix += links([('Circuit drawing source', 'excess_image'), ('Structural excess-3 VHDL', 'excess'), ('Gray source requiring care', 'gray_code')])
        appendix += r'''
\textbf{Drawing/code discrepancy:} the repository's Gray code uses OR for $g_2$,
whereas the drawing shows XOR. OR agrees with this XOR on valid BCD inputs 0--9
but fails for binary inputs 12--15. Use the preceding three-XOR circuit for our
0--15 Gray tests. Excess-3 tests cover valid BCD inputs 0--9: display the input
through a BCD decoder on HEX2 and the converted code through a Hex decoder on HEX3.
'''
        for title in ('Experiment 1: displaying a three-bit number', 'Experiment 2: complete hexadecimal display',
                      'Experiment 3: two-bit ALU and two displays', 'Experiment 4: two converters sharing one input'):
            token = r'\subsection{' + title + '}'
            tex = tex.replace(token, token + '\n' + r'\noindent\textit{Online circuit illustrations and clickable sources appear in Appendix~\ref{app:webrefs}, with differences from this experiment noted.}' + '\n', 1)
    return tex.replace(r'\end{document}', appendix + '\n' + r'\end{document}')
