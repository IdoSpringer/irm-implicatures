#!/usr/bin/env python3
"""Simple IRM (Fox-Katzir style) prototype.

States are strings like "AB" (the set of letters that are true).
Messages are logical phrases like "A or B", "A and C".
"""

import itertools
import re
import sys

# ---------------------------------------------------------------- states

def gen_states(letters):
    """All non-empty subsets of letters, as sorted strings."""
    out = []
    for r in range(1, len(letters) + 1):
        for combo in itertools.combinations(sorted(letters), r):
            out.append("".join(combo))
    return out

def truth_state(state):
    return set(state)

def gen_states_q(n):
    """All quantifier states: n persons, each N (none), S (some) or A (all)."""
    return ["".join(t) for t in itertools.product("NSA", repeat=n)]

# ---------------------------------------------------------------- parser

TOKEN_RE = re.compile(r"\s*(\(|\)|\bor\b|\band\b|\bxor\b|\bnot\b|\bP\d+\b|\bhit\b|\bsome\b|\bxsome\b|\ball\b|[A-Z]+)")

def tokenize(msg):
    pos, toks = 0, []
    while pos < len(msg):
        m = TOKEN_RE.match(msg, pos)
        if not m:
            raise ValueError(f"bad token at {msg[pos:]!r} in {msg!r}")
        toks.append(m.group(1))
        pos = m.end()
    return toks

class P:  # tiny recursive-descent parser
    def __init__(self, toks):
        self.toks, self.i = toks, 0
    def peek(self):
        return self.toks[self.i] if self.i < len(self.toks) else None
    def next(self):
        t = self.peek(); self.i += 1; return t
    def parse(self):
        node = self.or_()
        if self.peek() is not None:
            raise ValueError(f"trailing token {self.peek()!r}")
        return node
    def or_(self):
        node = self.xor_()
        while self.peek() == "or":
            self.next()
            node = ("or", node, self.xor_())
        return node
    def xor_(self):
        node = self.and_()
        while self.peek() == "xor":
            self.next()
            node = ("xor", node, self.and_())
        return node
    def and_(self):
        node = self.atom()
        while self.peek() == "and":
            self.next()
            node = ("and", node, self.atom())
        return node
    def atom(self):
        t = self.next()
        if t == "not":
            return ("not", self.atom())
        if t == "(":
            node = self.or_()
            if self.next() != ")":
                raise ValueError("missing )")
            return node
        if t is not None and re.fullmatch(r"P\d+", t):
            player = int(t[1:]) - 1
            if self.peek() == "hit":
                self.next()
            q = self.next()
            if q == "some":
                return ("some", player)
            if q == "xsome":
                return ("xsome", player)
            if q == "all":
                return ("all", player)
            raise ValueError(f"expected some/all after {t}, got {q!r}")
        if t is None or not (t.isalpha() and t.isupper()):
            raise ValueError(f"unexpected token {t!r}")
        return ("lit", t)

def parse(msg):
    return P(tokenize(msg)).parse()

def truth(ast, state):
    """Is the phrase true in the state? A letter is true iff present."""
    s = truth_state(state)
    op = ast[0]
    if op == "lit":
        return ast[1] in s
    if op == "some":
        return state[ast[1]] in "SA"
    if op == "xsome":
        return state[ast[1]] == "S"
    if op == "all":
        return state[ast[1]] == "A"
    if op == "not":
        return not truth(ast[1], state)
    if op == "and":
        return truth(ast[1], state) and truth(ast[2], state)
    if op == "or":
        return truth(ast[1], state) or truth(ast[2], state)
    if op == "xor":
        return truth(ast[1], state) != truth(ast[2], state)
    raise ValueError(op)

# ---------------------------------------------------------------- table

DEFAULT_LEXICON = {"or": "or", "and": "and", "xor": "xor",
                   "not": "not", "some": "some", "xsome": "xsome",
                   "all": "all"}

def build_table(messages, states, lexicon=None):
    """table[si][mj] = P(message mj | state si).

    1 if the state satisfies the message, else 0.
    Each state ROW is normalized evenly to sum to 1.
    lexicon: optional mapping of operator tokens to operators
    (e.g. {"or": "xor"}); defaults to the standard interpretation.
    """
    lex = DEFAULT_LEXICON if lexicon is None else lexicon
    asts = [P([lex.get(t, t) for t in tokenize(m)]).parse() for m in messages]
    table = []
    for s in states:
        row = [1.0 if truth(ast, s) else 0.0 for ast in asts]
        total = sum(row)
        if total > 0:
            row = [v / total for v in row]
        table.append(row)
    return table

# ---------------------------------------------------------------- printing

COLORS = ["\033[32m", "\033[92m",   # iter 1: identified, ruled out
          "\033[34m", "\033[94m",   # iter 2
          "\033[35m", "\033[95m",   # iter 3
          "\033[36m", "\033[96m",   # iter 4
          "\033[33m", "\033[93m"]   # iter 5
RESET = "\033[0m"
BOLD = "\033[1m"

def color_for(kind, round):
    """iter k: identified -> COLORS[2k-2], ruled out -> COLORS[2k-1]."""
    idx = (round - 1) * 2 + (0 if kind == "id" else 1)
    return COLORS[idx % len(COLORS)]

def print_table(rows, cols, table, color="", marks=None,
                row_idx=None, col_idx=None):
    """rows = states, cols = messages; table[i][j] = P(message j | state i).

    marks: optional dict (state_idx, msg_idx) -> (kind, round); colored cells.
    row_idx/col_idx: global indices of the displayed rows/cols.
    """
    if row_idx is None:
        row_idx = list(range(len(rows)))
    if col_idx is None:
        col_idx = list(range(len(cols)))
    w = max(8, max(len(c) for c in cols) + 2)
    print(" " * 6 + "".join(color + c.rjust(w) + RESET for c in cols))
    for ri, (r, row) in enumerate(zip(rows, table)):
        gi = row_idx[ri]
        cells = []
        for cj, (c, v) in enumerate(zip(cols, row)):
            gj = col_idx[cj]
            star, cell = " ", color
            if marks is not None and (gi, gj) in marks:
                kind, rnd = marks[(gi, gj)]
                star = "*" if kind == "id" else " "
                cell = color_for(kind, rnd) if kind == "id" else color_for("out", rnd)
            cells.append(cell + f"{v:>{w-1}.2f}{star}" + RESET)
        print(color + r.ljust(6) + RESET + "".join(cells))
    print()

# ---------------------------------------------------------------- matching

def match(messages, states, table, verbose=True):
    """Iteratively identify state<->message pairs.

    Returns (identifications, marks):
      identifications: list of (round, state, message, prob)
      marks: dict (state_idx, msg_idx) -> (kind, round) for final coloring;
             kind is 'id' for the identified cell, 'out' for the other
             cells in that round's identified rows/columns.
    """
    identifications = []
    marks = {}
    used_m, used_s = set(), set()
    round = 0
    while True:
        round += 1
        color = color_for("id", round)
        active_m = [j for j in range(len(messages)) if j not in used_m]
        active_s = [i for i in range(len(states)) if i not in used_s]
        if not active_m or not active_s:
            break
        if verbose:
            print(BOLD + color + f"--- iteration {round} ---" + RESET)
            print_table([states[i] for i in active_s],
                        [messages[j] for j in active_m],
                        [[table[i][j] for j in active_m] for i in active_s],
                        color=color)

        pairs = {}   # msg_index -> (prob, state_index)
        for j in active_m:
            best = max(table[i][j] for i in active_s)
            winners = [i for i in active_s if table[i][j] == best]
            if best > 0 and len(winners) == 1:   # unique max, else no ID
                pairs[j] = (best, winners[0])

        # if two columns claim the same state, the higher prob wins
        claims = {}
        for j, (p, i) in sorted(pairs.items(), key=lambda kv: -kv[1][0]):
            claims.setdefault(i, (j, p))
        pairs = {j: (p, i) for i, (j, p) in claims.items()}

        if not pairs:
            break

        id_s, id_m = set(), set()
        for j, (p, i) in pairs.items():
            identifications.append((round, states[i], messages[j], p))
            id_s.add(i); id_m.add(j)
            if verbose:
                print(color + f"  identified: {messages[j]!r} <-> state {states[i]} (p={p:.2f})" + RESET)
        # mark exact matched cells, and the rest of their rows/columns as ruled out
        for j, (p, i) in pairs.items():
            marks[(i, j)] = ("id", round)
        for i in id_s:
            for j in range(len(messages)):
                marks.setdefault((i, j), ("out", round))
        for j in id_m:
            for i in range(len(states)):
                marks.setdefault((i, j), ("out", round))
        used_m |= id_m
        used_s |= id_s
    return identifications, marks

# ---------------------------------------------------------------- main

def main(states, messages):
    table = build_table(messages, states)

    print(BOLD + "Full probability table (rows=states, cols=messages):" + RESET)
    print_table(states, messages, table)

    ids, marks = match(messages, states, table)

    print(BOLD + "Final table with identifications marked:" + RESET)
    print_table(states, messages, table, marks=marks)

    print(BOLD + "All identifications:" + RESET)
    for round, s, m, p in ids:
        print(f"  iter {round}: {m!r} <-> state {s} (p={p:.2f})")
    if not ids:
        print("  (none)")

def main_lu(states, messages, lexica):
    """IRM with lexical uncertainty: build a table per lexicon, average
    them cell-wise, then run the usual peeling on the averaged table."""
    tables = []
    for k, lex in enumerate(lexica, 1):
        t = build_table(messages, states, lex)
        tables.append(t)
        print(BOLD + f"Lexicon L{k}: {lex}" + RESET)
        print_table(states, messages, t)

    avg = [[sum(t[i][j] for t in tables) / len(tables)
            for j in range(len(messages))]
           for i in range(len(states))]
    print(BOLD + "Averaged probability table over lexica:" + RESET)
    print_table(states, messages, avg)

    ids, marks = match(messages, states, avg)

    print(BOLD + "Final table with identifications marked:" + RESET)
    print_table(states, messages, avg, marks=marks)

    print(BOLD + "All identifications:" + RESET)
    for round, s, m, p in ids:
        print(f"  iter {round}: {m!r} <-> state {s} (p={p:.2f})")
    if not ids:
        print("  (none)")

# ---------------------------------------------------------------- tests

def dis2():
    letters = ["A", "B"]
    states = gen_states(letters)
    messages = ["A", "B", "A or B", "A and B"]
    return states, messages

def crd2():
    letters = ["A", "B"]
    states = gen_states(letters)
    messages = ["A", "B", "A or B"]
    return states, messages 

def dis2_la():
    letters = ["A", "B"]
    states = gen_states(letters)
    messages = ["A", "B", "A or B", "A xor B", "A and B"]
    return states, messages 

def crd2_la():
    letters = ["A", "B"]
    states = gen_states(letters)
    messages = ["A", "B", "A or B", "A xor B"]
    return states, messages

def dis3():
    letters = ["A", "B", "C"]
    states = gen_states(letters)
    messages = ["A", "B", "C",
    "A or B", "A and B", "A or C", "A and C", "B or C", "B and C",
    "A or (B or C)", "A or (B and C)", "A and (B or C)", "A and (B and C)"]
    return states, messages

def dis3_la():
    letters = ["A", "B", "C"]
    states = gen_states(letters)
    messages = ["A", "B", "C",
    "A or B", "A and B", "A xor B",
    "A or C", "A and C", "A xor C",
    "B or C", "B and C", "B xor C",
    "A or (B or C)", "A xor (B or C)", "A or (B xor C)", "A xor (B xor C)",
    "A or (B and C)", "A xor (B and C)",
    "A and (B or C)", "A and (B xor C)",
    "A and (B and C)"]
    return states, messages

def crd3():
    letters = ["A", "B", "C"]
    states = gen_states(letters)
    messages = ["A", "B", "C", "A or B", "A or C", "B or C", "A or B or C"]
    return states, messages

def crd3_la():
    letters = ["A", "B", "C"]
    states = gen_states(letters)
    messages = ["A", "B", "C",
    "A or B", "A xor B",
    "A or C", "A xor C",
    "B or C", "B xor C",
    "A or B or C", "A xor (B or C)", "A or (B xor C)", "A xor (B xor C)"]
    return states, messages

def q1():
    states = gen_states_q(1)
    messages = ["P1 hit some", "P1 hit all"]
    return states, messages

def q1_la():
    states = gen_states_q(1)
    messages = ["P1 hit some", "P1 hit all", "P1 hit xsome"]
    return states, messages

def q1_lu():
    states, messages = q1()
    lexica = [{"some": "some", "all": "all"},   # L1: some = some
              {"some": "xsome", "all": "all"}]   # L2: some = xsome
    return states, messages, lexica

def q2():
    states = gen_states_q(2)
    messages = ["P1 hit some", "P1 hit all", "P2 hit some", "P2 hit all"]
    return states, messages

def crd2_lu():
    """crd2 with lexical uncertainty over 'or'."""
    states, messages = crd2()
    lexica = [{"or": "or", "and": "and"},   # L1: or = or
              {"or": "xor", "and": "and"}]  # L2: or = xor
    return states, messages, lexica

def crd3_lu():
    states, messages = crd3()
    lexica = [{"or": "or", "and": "and"},   # L1: or = or
              {"or": "xor", "and": "and"}]  # L2: or = xor
    return states, messages, lexica

if __name__ == "__main__":
    # states, messages = q1_la()
    # main(states, messages)
    states, messages, lexica = q1_lu()
    main_lu(states, messages, lexica)
