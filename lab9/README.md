# Lab 9: English Prelab and Postlab

The English deliverables are in `output/pdf/`:

- `lab9_prelab_postlab.pdf`: the compiled report.
- `lab9_prelab_postlab.tex`: LaTeX source with TikZ diagrams and companion reference images.
- `verification.json`: actual offline Boolean checks and minimum-SOP results.
- `theoretical_expected_results.csv`: expected segment, Gray, and excess-3 values.
- `theoretical_hex7seg.vcd`: a zero-delay theoretical waveform, not a ModelSim record.

The report includes all 18 Karnaugh maps, group-by-group simplification, product sharing,
gate connection tables, circuit diagrams, all 64 ALU cases, experiment connection plans,
the four postlab answers, and design-stage conclusions.

## Scope

Offline derivations and checks have been performed. Quartus, ModelSim, and board experiments
have not been run. Actual measurements, photographs, LE counts, time spent, and TA sign-off
are explicitly pending. This is a document package, not the three Quartus project archives
required by the course.

Patterns follow the numeric entries of Lab 9 Tables 2 and 3. The prose on page 2 conflicts
with Table 2 for digits 6 and 9; this report lights a for 6 and d for 9. Segment strings
are **abcdefg**, with **0 = on**. A bus written as HEX[6:0] instead uses **gfedcba**.

## Compile the existing source

Use XeLaTeX with Latin Modern, TikZ, and the standard math/table packages. The English
source does not require Chinese fonts or ctex. In PowerShell at the package root:

```powershell
.\build_pdf.ps1
```

Or compile `lab9_prelab_postlab.tex` three times in `output/pdf/`:

```powershell
xelatex -interaction=nonstopmode -halt-on-error lab9_prelab_postlab.tex
xelatex -interaction=nonstopmode -halt-on-error lab9_prelab_postlab.tex
xelatex -interaction=nonstopmode -halt-on-error lab9_prelab_postlab.tex
```

On Overleaf, upload the .tex file and its companion images/ folder, then select XeLaTeX. The appendix includes attributed external circuit illustrations, clickable source URLs, and differences from this experiment.

## Regenerate and recheck

Use Python 3.10 or later:

```powershell
python -m pip install sympy
python build_lab9.py
.\build_pdf.ps1
```

Keep `lab9_logic.py` beside the English generator: it provides the shared computational
functions; the Chinese report generator and deliverables have been removed. The checker independently
enumerates all 81 cubes and solves the single-output covering problems to confirm minimum
term counts and the minimum literal counts at those term counts. It also checks the
converters, ALU cases, and both letter-decoder alternatives.

Regeneration overwrites the English .tex file; back up manual edits first. After actual
experimentation, enter only genuine observations in the measurement columns and update
the experiment conclusions accordingly.
