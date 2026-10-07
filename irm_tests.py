#!/usr/bin/env python3
"""Test fixtures for the IRM prototype.

Each fixture returns (states, messages) or (states, messages, lexica).
Run the demo with: python3 irm_tests.py
"""

from irm import gen_states, gen_states_q, main, main_lu
from latex import to_latex

# basic inference: some but not all

def q1():
    # irm succeeds
    states = gen_states_q(1)
    messages = ["P1 hit some", "P1 hit all"]
    return states, messages

def q1_lu():
    # irm-lu succeeds
    states, messages = q1()
    lexica = [{"some": "some", "all": "all"},
              {"some": "xsome", "all": "all"},
              {"some": "all", "all": "all"}]
            #   last lexicon cannot express the some-but-not-all state,
            #   so it drops out of that row automatically
    return states, messages, lexica

# conjuctive reading of disjunctions

def crd2():
    # irm succeeds
    letters = ["A", "B"]
    states = gen_states(letters)
    messages = ["A", "B", "A or B"]
    return states, messages

def crd2_la():
    # irm-la fails
    letters = ["A", "B"]
    states = gen_states(letters)
    messages = ["A", "B", "A or B", "A xor B"]
    return states, messages

def crd2_lu():
    # irm-lu succeeds
    states, messages = crd2()
    lexica = [{"or": "or", "and": "and"},
              {"or": "xor", "and": "and"},
              {"or": "and", "and": "and"}]
    return states, messages, lexica

def crd3():
    # irm fails
    letters = ["A", "B", "C"]
    states = gen_states(letters)
    messages = ["A", "B", "C", "A or B", "A or C", "B or C", "A or B or C"]
    return states, messages

def crd3_lu():
    # irm-lu succeeds! but only if we include last lexicon
    states, messages = crd3()
    lexica = [{"or": "or", "and": "and"},
              {"or": "xor", "and": "and"},
              {"or": "and", "and": "and"}]
    return states, messages, lexica

# suspension

def suspension_lu():
    states, messages = q1()
    messages = ["P1 hit some", "P1 hit all", "P1 hit some and P1 hit all", "P1 hit some or P1 hit all"]
    lexica = [{"some": "some", "all": "all"},
              {"some": "xsome", "all": "all"},
              {"some": "all", "all": "all"}]
    return states, messages, lexica

# negation

def neg_q1():
    states, messages = q1()
    # messages = ["P1 hit some", "P1 hit all", "not (P1 hit some)", "not (P1 hit all)"]
    messages = ["not (P1 hit some)", "not (P1 hit all)"]
    return states, messages

def neg_q1_lu():
    states, messages = neg_q1()
    lexica = [{"some": "some", "all": "all"},
              {"some": "xsome", "all": "all"},
              {"some": "all", "all": "all"}]
    return states, messages, lexica

def neg_dis():
    # irm works; however comaring to frischoff there might be a bug here
    states = ["~A^~B", "A^~B", "B^~A", "(A^~B)|(B^~A)"]
    messages = ["not A", "not B", "not (A or B)", "not (A and B)"]
    return states, messages

def neg_dis_lu():
    # irm-lu succeeds
    states, messages = neg_dis()
    lexica = [{"or": "or", "and": "and"},
              {"or": "xor", "and": "and"},
              {"or": "and", "and": "and"}]
    return states, messages, lexica

def neg_fc_lu():
    # irm-lu succeeds for n=2
    states = ["~A^~B", "A^~B", "B^~A"]
    messages = ["not A", "not B", "not (A and B)"]
    lexica = [{"or": "or", "and": "and"},
              {"or": "xor", "and": "and"},
              {"or": "and", "and": "and"}]
    return states, messages, lexica

def neg_fc3():
    # irm fails
    letters = ["A", "B", "C"]
    states = gen_states(letters)
    messages = ["not A", "not B", 'not C',
    "not (A and B)", "not (A and C)", "not (B and C)",
    "not (A and B and C)"]
    return states, messages

def neg_fc3_lu():
    # irm-lu fails
    letters = ["A", "B", "C"]
    states = gen_states(letters)
    messages = ["not A", "not B", 'not C',
    "not (A and B)", "not (A and C)", "not (B and C)",
    "not (A and B and C)"]
    lexica = [{"or": "or", "and": "and"},
              {"or": "xor", "and": "and"},
              {"or": "and", "and": "and"}]
    return states, messages, lexica

# 2 upper bound

def dis3():
    # irm succeeds?
    letters = ["A", "B", "C"]
    states = ['A', 'B', 'C',
            'A and B', 'A and C', 'B and C',
            'A or B', 'A or C', 'B or C',
            # 'A xor B', 'A xor C', 'B xor C',
            'A and B and C', 'A or B or C',
            # 'A xor B xor C',
            '(A^~B^~C)|(B^~A^~C)|(C^~A^~B)']
    # assumer sauerland alternatives
    messages = ["A", "B", "C",
    "A or B", "A and B", "A or C", "A and C", "B or C", "B and C",
    "A or (B or C)", "A and (B and C)"]
    return states, messages

def dis3_lu():
    states, messages = dis3()
    lexica = [{"or": "or", "and": "and"},
              {"or": "xor", "and": "and"},
              {"or": "and", "and": "and"}]
    return states, messages, lexica

def or_some_fc():
    messages = ["B", "some", "all", "B or some", "B or all"]
    states = ["B and none", "B and xsome", "B and all",
            "(not B) and none", "(not B) and xsome", "(not B) and all"]
    return states, messages

def or_some_fc_lu():
    states, messages = or_some_fc()
    lexica = [{"or": "or", "and": "and", "some": "some", "all": "all"},
              {"or": "xor", "and": "and", "some": "some", "all": "all"},
              {"or": "and", "and": "and", "some": "some", "all": "all"},
              {"or": "or", "and": "and", "some": "xsome", "all": "all"},
              {"or": "xor", "and": "and", "some": "xsome", "all": "all"},
              {"or": "and", "and": "and", "some": "xsome", "all": "all"},
              {"or": "or", "and": "and", "some": "all", "all": "all"},
              {"or": "xor", "and": "and", "some": "all", "all": "all"},
              {"or": "and", "and": "and", "some": "all", "all": "all"}]
    return states, messages, lexica

# elipsis

def ellipsis():
    states = gen_states_q(2)
    # we need lexical identity foe elipsis
    # regular irm works
    # we remove alternatives without semantic identity
    # we remove pos from neg alternatives as in negation to avoid symmetry problem
    messages = ["P1 hit some", "P1 hit all", "not (P2 hit some)", "not (P2 hit all)",
                "P1 hit some and not (P2 hit some)", "P1 hit some or not (P2 hit some)",
                "P1 hit all and not (P2 hit all)", "P1 hit all or not (P2 hit all)"]
    return states, messages

def ellipsis_lu():
    # seems to work.
    states, messages = ellipsis()
    lexica = [{"some": "some", "all": "all"},
              {"some": "xsome", "all": "all"},
              {"some": "all", "all": "all"}]
    return states, messages, lexica
                      

if __name__ == "__main__":
    # states, messages = neg_dis()
    # states, messages = neg_q1()
    # states, messages = neg_fc3()
    # states, messages = dis3()
    # states, messages = or_some_fc()
    # states, messages = crd2_la()
    # states, messages = ellipsis()
    
    # main(states, messages)
    
    # states, messages, lexica = q1_lu()
    # states, messages, lexica = suspension_lu()
    # states, messages, lexica = neg_q1_lu()
    # states, messages, lexica = neg_dis_lu()
    # states, messages, lexica = neg_fc_lu()
    # states, messages, lexica = neg_fc3_lu()
    # states, messages, lexica = dis3_lu()
    # states, messages, lexica = crd2_lu()
    # states, messages, lexica = crd3_lu()
    # states, messages, lexica = or_some_fc_lu()
    # states, messages, lexica = ellipsis_lu()

    # main_lu(states, messages, lexica)
    
    # to_latex(suspension_lu(), out_path='suspension_lu.tex')
    # to_latex(neg_q1_lu(), out_path='neg_q1_lu.tex')
    # to_latex(neg_dis_lu(), out_path='neg_dis_lu.tex')
    # to_latex(neg_fc_lu(), out_path='neg_fc_lu.tex')
    # to_latex(crd2_lu(), out_path='crd2_lu.tex')
    # to_latex(crd3_lu(), out_path='crd3_lu.tex')
    # to_latex(crd2_la(), out_path='crd2_la.tex')
    # to_latex(or_some_fc(), out_path='or_some_fc.tex')
    # to_latex(or_some_fc_lu(), out_path='or_some_fc_lu.tex')
    # to_latex(ellipsis_lu(), out_path='ellipsis_lu.tex')
    pass

