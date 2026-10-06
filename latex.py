#!/usr/bin/env python3
"""LaTeX table generation for IRM results (Frischhoff-2025 style).

to_latex() takes a test result tuple -- (states, messages) or
(states, messages, lexica) -- runs the IRM pipeline on it, and renders
the peeling process as a colored LaTeX table.
"""

from fractions import Fraction

from irm import build_table, match, avg_tables

# ---------------------------------------------------------------- latex

# cell colors for the peeling steps (Frischhoff-2025 / table_latex.tex style)
LATEX_COLORS = {
    "iter1": (255, 204, 204),   # identified in iteration I (pink)
    "elim1": (230, 230, 230),   # eliminated after iteration I (light gray)
    "iter2": (255, 255, 179),   # identified in iteration II (light yellow)
    "elim2": (190, 190, 190),   # eliminated after iteration II (darker gray)
    "iter3": (204, 255, 204),   # identified in iteration III (light green)
    "elim3": (150, 150, 150),   # eliminated after iteration III
    "iter4": (204, 226, 255),   # light blue
    "elim4": (110, 110, 110),
    "iter5": (255, 216, 179),   # light orange
    "elim5": (70, 70, 70),
}

def to_roman(n):
    vals = [(10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
    out = ""
    for v, s in vals:
        while n >= v:
            out += s
            n -= v
    return out

def _is_q_state(state):
    return state and all(c in "NSA" for c in state)

def _state_to_latex(state):
    """Render a state spec as math-mode LaTeX.

    Quantifier states (N/S/A strings): N -> \neg\exists, S -> (\exists \land
    \neg\forall), A -> \forall; subscripted with P_i when >1 person.
    Propositional states: ^ -> \land, | -> \lor, ~ -> \neg.
    Mixed states: bare some/xsome/all/none keywords and "Pi hit q" atoms
    get the same quantifier rendering, composed with the letter operators.
    """
    if _is_q_state(state):
        parts = []
        for i, c in enumerate(state, 1):
            if c == "N":
                expr = r"\neg\exists"
            elif c == "S":
                expr = r"(\exists \land \neg\forall)"
            else:  # "A"
                expr = r"\forall"
            if len(state) > 1:
                expr += "_{P_%d}" % i
            parts.append(expr)
        return r"\(%s\)" % r" \land ".join(parts)
    import re as _re
    def _q_sub(m):
        i = m.group(1)
        q = m.group(2)
        expr = {"some": r"\exists", "xsome": r"(\exists \land \neg\forall)",
                "all": r"\forall"}[q]
        return expr + ("_{P_%s}" % i if i else "")
    spec = _re.sub(r"\bP(\d*)\s+hit\s+(some|xsome|all)\b", _q_sub, state)
    spec = _re.sub(r"\bnone\b", lambda m: r"\neg\exists", spec)
    spec = _re.sub(r"\bxsome\b", lambda m: r"(\exists \land \neg\forall)", spec)
    spec = _re.sub(r"\bsome\b", lambda m: r"\exists", spec)
    spec = _re.sub(r"\ball\b", lambda m: r"\forall", spec)
    spec = _re.sub(r"\bor\b", lambda m: r"\lor ", spec)
    spec = _re.sub(r"\band\b", lambda m: r"\land ", spec)
    spec = _re.sub(r"\bnot\b", lambda m: r"\neg ", spec)
    spec = (spec.replace("~", r"\neg ")
                 .replace("^", r" \land ")
                 .replace("|", r" \lor "))
    return r"\(%s\)" % spec

def _cell_latex(v):
    """Exact fraction when reasonable (denominator <= 100), else 2 decimals."""
    if v == 0:
        return r"\(0\)"
    f = Fraction(v)
    if f.denominator == 1:
        return r"\(%d\)" % f.numerator
    if f.denominator <= 100:
        return r"\(\frac{%d}{%d}\)" % (f.numerator, f.denominator)
    return r"\(%.2f\)" % float(f)

def to_latex(result, caption=None, label=None, out_path=None):
    """Render a test's result as a LaTeX table (Frischhoff-2025 style).

    result: (states, messages) or (states, messages, lexica).
    For lexica, tables are built per lexicon and averaged row-wise with
    p(L|t) uniform over lexica that can express t, then the usual
    peeling runs on the averaged table.
    Returns the \\begin{table}...\\end{table} block (with \\definecolor
    lines for the used colors); writes to out_path if given.
    """
    if len(result) == 3:
        states, messages, lexica = result
        tables = [build_table(messages, states, lex) for lex in lexica]
        table = avg_tables(tables)
    else:
        states, messages = result
        table = build_table(messages, states)
    ids, marks = match(messages, states, table, verbose=False)

    used = sorted({("iter" if kind == "id" else "elim") + str(round)
                   for kind, round in marks.values()})
    lines = ["% \\usepackage[table]{xcolor} needed"]
    for name in used:
        r, g, b = LATEX_COLORS[name]
        lines.append(r"\definecolor{%s}{RGB}{%d, %d, %d}" % (name, r, g, b))
    lines.append(r"\renewcommand{\arraystretch}{1.2}")
    lines.append(r"\begin{table}[h]")
    lines.append(r"\centering")
    if caption:
        lines.append(r"\caption{%s}" % caption)
    if label:
        lines.append(r"\label{tab:%s}" % label)
    colspec = "| l || " + " | ".join(["c"] * len(messages)) + " |"
    lines.append(r"\begin{tabular}{%s}" % colspec)
    lines.append(r"\hline")
    header = [r"$P(m|t)$"] + ["'%s'" % m for m in messages]
    lines.append(" & ".join(header) + r" \\")
    lines.append(r"\hline \hline")
    for i, state in enumerate(states):
        cells = []
        for j, v in enumerate(table[i]):
            if (i, j) in marks:
                kind, rnd = marks[(i, j)]
                color = ("iter" if kind == "id" else "elim") + str(rnd)
                cells.append(r"\cellcolor{%s}%s" % (color, _cell_latex(v)))
            else:
                cells.append(_cell_latex(v))
        lines.append(" & ".join([_state_to_latex(state)] + cells) + r" \\")
        lines.append(r"\hline")
    lines.append(r"\end{tabular}")
    if used:
        lines.append("")
        lines.append(r"\vspace{0.6em}")
        legend = []
        for name in used:
            rnd = int(name[4:])
            kind = "identified message-state pairs in iteration" \
                if name.startswith("iter") else "cells eliminated after iteration"
            legend.append(r"\textcolor{%s}{\(\blacksquare\)} %s %s"
                          % (name, kind, to_roman(rnd)))
        lines.append(r"{\small")
        lines.append(" \\quad ".join(legend))
        lines.append("}")
    lines.append(r"\end{table}")
    out = "\n".join(lines)
    if out_path:
        with open(out_path, "w") as fh:
            fh.write(out + "\n")
    return out
