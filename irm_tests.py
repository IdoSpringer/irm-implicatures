#!/usr/bin/env python3
"""Test fixtures for the IRM prototype.

Each fixture returns (states, messages) or (states, messages, lexica).
Run the demo with: python3 irm_tests.py
"""

from irm import gen_states, gen_states_q, main, main_lu
from latex import to_latex

# ---------------------------------------------------------------- tests

# deriving exclusive or

def dis2_naive():
    # irm fails
    letters = ["A", "B"]
    states = gen_states(letters)
    messages = ["A", "B", "A or B", "A and B"]
    return states, messages

def dis2():
    # irm succeeds
    letters = ["A", "B"]
    states = ["A^~B", "B^~A", "A^B", "(A^~B)|(B^~A)"]
    messages = ["A", "B", "A or B", "A and B"]
    return states, messages

def dis3():
    # irm succeeds
    letters = ["A", "B", "C"]
    states = ["A^~B^~C", "B^~A^~C", "C^~A^~B",
            "A^B^~C", "A^C^~B", "B^C^~A",
            "A^B^C",
            "(A^~B^~C)|(B^~A^~C)|(C^~A^~B)"]
    messages = ["A", "B", "C",
    "A or B", "A and B", "A or C", "A and C", "B or C", "B and C",
    "A or (B or C)", "A or (B and C)", "A and (B or C)", "A and (B and C)"]
    return states, messages

def dis2_la():
    # irm-la fails? both or and xor identify the same
    states, messages = dis2()
    messages += ["A xor B"]
    return states, messages

def dis2_lu():
    # irm-lu succeeds
    states, messages = dis2()
    lexica = [{"or": "or", "and": "and"},
              {"or": "xor", "and": "and"}]
    return states, messages, lexica

def dis3_la():
    states, messages = dis3()
    messages += ["A xor B", "A xor C", "B xor C",
                 "A xor (B or C)", "A or (B xor C)", "A xor (B xor C)",
                 "A xor (B and C)", "A and (B xor C)"]
    return states, messages

def dis3_lu():
    states, messages = dis3()
    lexica = [{"or": "or", "and": "and"},
              {"or": "xor", "and": "and"}]
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
    lexica = [{"or": "or", "and": "and"},   # L1: or = or
              {"or": "xor", "and": "and"}]  # L2: or = xor
    return states, messages, lexica

def crd3():
    # irm fails
    letters = ["A", "B", "C"]
    states = gen_states(letters)
    messages = ["A", "B", "C", "A or B", "A or C", "B or C", "A or B or C"]
    return states, messages

def crd3_la():
    # irm-la fails
    letters = ["A", "B", "C"]
    states = gen_states(letters)
    messages = ["A", "B", "C",
    "A or B", "A xor B",
    "A or C", "A xor C",
    "B or C", "B xor C",
    "A or B or C", "A xor (B or C)", "A or (B xor C)", "A xor (B xor C)"]
    return states, messages

def crd3_lu():
    # irm-lu fails
    states, messages = crd3()
    lexica = [{"or": "or", "and": "and"},   # L1: or = or
              {"or": "xor", "and": "and"}]  # L2: or = xor
    return states, messages, lexica

# some but not all

def q1():
    # irm succeeds
    states = gen_states_q(1)
    messages = ["P1 hit some", "P1 hit all"]
    return states, messages

def q1_la():
    # irm-la suceeds (but in a different way than q1)
    states = gen_states_q(1)
    messages = ["P1 hit some", "P1 hit all", "P1 hit xsome"]
    return states, messages

def q1_lu():
    # irm-lu succeeds
    states, messages = q1()
    lexica = [{"some": "some", "all": "all"},
              {"some": "xsome", "all": "all"}]
            #   last lexicon has 0 proba
            #   {"some": "all", "all": "all"}]
    return states, messages, lexica

def q2():
    states = gen_states_q(2)
    messages = ["P1 hit some", "P1 hit all", "P2 hit some", "P2 hit all"]
    return states, messages

def q2_lu():
    states, messages = q2()
    lexica = [{"some": "some", "all": "all"},
              {"some": "xsome", "all": "all"}]
    return states, messages, lexica

# disjuction under negation

def neg_dis():
    # irm works; however comaring to frischoff there might be a bug here
    states = ["~A^~B", "A^~B", "B^~A", "(A^~B)|(B^~A)"]
    messages = ["not A", "not B", "not (A or B)", "not (A and B)"]
    return states, messages

def neg_dis_la():
    # again we have the same double identification problem
    states, messages = neg_dis()
    messages += ["not (A xor B)"]
    return states, messages

def neg_dis_lu():
    states, messages = neg_dis()
    lexica = [{"or": "or", "and": "and"},
              {"or": "xor", "and": "and"},
              {"or": "and", "and": "and"}]
    return states, messages, lexica

# elipsis

def elipsis():
    states = gen_states_q(2)
    # we need lexical identity foe elipsis
    # regular irm works however not sure we have all messages to create probability equality in column
    messages = ["P1 hit some", "P1 hit all",
                "not (P2 hit some)", "P2 hit some", "not (P2 hit all)", "P2 hit all",
                "P1 hit some and P2 hit some", "P1 hit all and P2 hit all",
                "P1 hit some or P2 hit some", "P1 hit all or P2 hit all",
                "P1 hit some or not (P2 hit some)", "P1 hit all or not (P2 hit all)",
                "P1 hit some and not (P2 hit some)", "P1 hit all and not (P2 hit all)"]
    return states, messages

def elipsis_lu():
    states, messages = elipsis()
    lexica = [{"some": "some", "all": "all"},
              {"some": "xsome", "all": "all"}]
    return states, messages, lexica


def logical_exp_order():
    # 1 non-probablistic irm, some-but-not-all
    # 1 probablistic irm, some-but-not-all
    states, messages = q1()
    main(states, messages)
    # irm-lu, some-but-not-all
    states, messages, lexica = q1_lu()
    main_lu(states, messages, lexica)

# suspension

def suspension_lu():
    states, messages = q1()
    messages = ["P1 hit some", "P1 hit all", "P1 hit some and P1 hit all"]
    lexica = [{"some": "some", "all": "all"},
              {"some": "xsome", "all": "all"}]
            #   {"some": "all", "all": "all"}]
    return states, messages, lexica

# negation

def neg_q1():
    states, messages = q1()
    messages = ["P1 hit some", "P1 hit all", "not (P1 hit some)", "not (P1 hit all)"]
    return states, messages


def neg_q1_lu():
    states, messages = q1()
    messages = ["P1 hit some", "P1 hit all", "not (P1 hit some)", "not (P1 hit all)"]
    lexica = [{"some": "some", "all": "all"},
              {"some": "xsome", "all": "all"}]
            #   {"some": "all", "all": "all"}]
    return states, messages, lexica

def dump_latex():                                                                                                                                                                                        
      to_latex(q1(), out_path='q1.tex')                 

if __name__ == "__main__":
    # states, messages = neg_dis()
    # states, messages = neg_q1()
    # main(states, messages)
    
    # states, messages, lexica = q1_lu()
    # states, messages, lexica = suspension_lu()
    states, messages, lexica = neg_q1_lu()
    # states, messages, lexica = neg_dis_lu()
    main_lu(states, messages, lexica)
    # logical_exp_order()
    
    # dump_latex()
