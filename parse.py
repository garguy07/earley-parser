#!/usr/bin/env python3
"""
Earley Parser Implementation
Usage: ./parse.py foo.gr foo.sen

Design notes (for Q4 of the assignment):

Correctness
-----------
- chart[i]     : dict {key -> Item}  One entry per (rule, dot, start, end).
                 Used ONLY for O(1) duplicate detection and agenda gating.
                 Never updated in-place — the first Item's back-pointer is
                 preserved intact so derivation chains are never overwritten.
- all_items[i] : list of ALL Items ever pushed to column i, including multiple
                 Items with the same key but different back-pointers (i.e.
                 different derivations). Used exclusively for tree enumeration.
- When a completed item triggers the Completer, every waiting candidate in
  chart[completed.start] is advanced. The resulting new item is appended to
  all_items unconditionally, but only added to the agenda if its key is new.
- enum_trees() recursively walks all_items to yield every distinct parse tree.

Efficiency
----------
- O(n^2) space: at most one entry per (rule, dot, start, end) in each of the
  n+1 columns of the chart dict. Hash lookup + insert is O(1).
- O(n^3) time: each unique key is pushed to the agenda exactly once, so each
  item is processed (popped) exactly once. The Completer iterates chart[k]
  for some k, producing one new item per (candidate, completed) pair — that
  loop is bounded by the number of chart entries, keeping the overall work
  within O(n^3).
- Agenda push is O(1): we check chart[pos] first; if the key exists we do NOT
  re-add to the agenda. This is essential — re-queuing would cause exponential
  reprocessing and break the complexity bound.
"""

import sys
import math
from collections import defaultdict


# ──────────────────────────────────────────────
# Data structures
# ──────────────────────────────────────────────


class Rule:
    """A weighted CFG rule: lhs -> rhs with log-probability weight."""

    __slots__ = ("lhs", "rhs", "log_prob")

    def __init__(self, lhs, rhs, prob):
        self.lhs = lhs
        self.rhs = tuple(rhs)
        self.log_prob = math.log(prob) if prob > 0 else float("-inf")

    def __repr__(self):
        return f"{self.lhs} -> {' '.join(self.rhs)}  [{math.exp(self.log_prob):.4f}]"


class Item:
    """
    An Earley chart item: lhs -> α • β  spanning [start, end]

    log_weight : total log-prob of THIS particular derivation
    back       : (completed_item, parent_item) for tree reconstruction,
                 or None for seed/terminal items
    """

    __slots__ = ("rule", "dot", "start", "end", "log_weight", "back")

    def __init__(self, rule, dot, start, end, log_weight=0.0, back=None):
        self.rule = rule
        self.dot = dot
        self.start = start
        self.end = end
        self.log_weight = log_weight
        self.back = back

    def key(self):
        """Identity key — ignores weight and back-pointer."""
        return (self.rule, self.dot, self.start, self.end)

    def is_complete(self):
        return self.dot == len(self.rule.rhs)

    def next_symbol(self):
        if self.dot < len(self.rule.rhs):
            return self.rule.rhs[self.dot]
        return None

    def __repr__(self):
        rhs = list(self.rule.rhs)
        rhs.insert(self.dot, "•")
        return (
            f"[{self.start},{self.end}] "
            f"{self.rule.lhs} -> {' '.join(rhs)}  "
            f"w={self.log_weight:.4f}"
        )


# ──────────────────────────────────────────────
# Grammar loading
# ──────────────────────────────────────────────


def load_grammar(filename):
    """
    Parse a .gr file. Each non-blank, non-comment line:
        prob  LHS  RHS_1  RHS_2 ...
    Returns dict: lhs -> list[Rule]
    """
    rules = defaultdict(list)
    with open(filename) as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            prob = float(parts[0])
            lhs = parts[1]
            rhs = parts[2:]
            if not rhs:
                continue  # epsilon rules not supported
            rules[lhs].append(Rule(lhs, rhs, prob))
    return rules


# ──────────────────────────────────────────────
# Earley parser
# ──────────────────────────────────────────────


class EarleyParser:
    def __init__(self, grammar):
        self.grammar = grammar
        all_lhs = set(grammar.keys())
        all_syms = {s for rs in grammar.values() for r in rs for s in r.rhs}
        self.terminals = all_syms - all_lhs

    def parse(self, words):
        """
        Run the Earley algorithm on `words`.
        Returns (chart, start_symbol).
        After the call, self.all_items[i] holds every Item pushed to column i.
        """
        n = len(words)

        # chart[i]: dict {key -> Item}  — dedup guard, one entry per key
        chart = [dict() for _ in range(n + 1)]

        # all_items[i]: every Item ever pushed, including alternate derivations
        self.all_items = [[] for _ in range(n + 1)]

        # agenda[i]: FIFO of items to process in column i
        agenda = [[] for _ in range(n + 1)]

        start_symbol = self._detect_start_symbol()
        self._predict(start_symbol, 0, chart, agenda)

        for i in range(n + 1):
            j = 0
            while j < len(agenda[i]):
                item = agenda[i][j]
                j += 1

                if item.is_complete():
                    self._complete(item, chart, agenda)
                elif item.next_symbol() not in self.terminals:
                    self._predict_symbol(item.next_symbol(), i, chart, agenda)
                    if i < n:
                        self._scan(item, words[i], i, chart, agenda)
                else:
                    if i < n:
                        self._scan(item, words[i], i, chart, agenda)

        return chart, start_symbol

    # ── Three Earley operations ──────────────────────────────────────

    def _predict(self, lhs, pos, chart, agenda):
        for rule in self.grammar.get(lhs, []):
            self._push(Item(rule, 0, pos, pos, 0.0, None), pos, chart, agenda)

    def _predict_symbol(self, symbol, pos, chart, agenda):
        self._predict(symbol, pos, chart, agenda)

    def _scan(self, item, word, pos, chart, agenda):
        if item.next_symbol() == word:
            self._push(
                Item(
                    item.rule,
                    item.dot + 1,
                    item.start,
                    pos + 1,
                    item.log_weight,
                    item.back,
                ),
                pos + 1,
                chart,
                agenda,
            )

    def _complete(self, completed, chart, agenda):
        for candidate in list(chart[completed.start].values()):
            if (
                not candidate.is_complete()
                and candidate.next_symbol() == completed.rule.lhs
            ):
                new_weight = (
                    candidate.log_weight
                    + completed.rule.log_prob
                    + completed.log_weight
                )
                self._push(
                    Item(
                        candidate.rule,
                        candidate.dot + 1,
                        candidate.start,
                        completed.end,
                        new_weight,
                        back=(completed, candidate),
                    ),
                    completed.end,
                    chart,
                    agenda,
                )

    def _push(self, item, pos, chart, agenda):
        """
        O(1) push with duplicate suppression.

        Always append to all_items — this records every derivation.
        Only add to chart + agenda if the key is new; never re-queue
        an existing key (that would break the O(n^3) time bound).
        Never update the chart entry in-place — doing so would overwrite
        the original back-pointer and lose the first derivation.
        """
        key = item.key()
        self.all_items[pos].append(item)  # record every derivation
        if key not in chart[pos]:
            chart[pos][key] = item
            agenda[pos].append(item)  # O(1) append

    def _detect_start_symbol(self):
        for sym in ("S", "ROOT", "TOP"):
            if sym in self.grammar:
                return sym
        return next(iter(self.grammar))


# ──────────────────────────────────────────────
# All-parses enumeration
# ──────────────────────────────────────────────


def enum_trees(item, all_items):
    """
    Recursively yield every parse tree rooted at `item` as a nested tuple:
        (rule, [child_tree, ...])
    Terminal / seed items (back is None) yield a leaf: (rule, []).
    """
    if item.back is None:
        yield (item.rule, [])
        return

    completed, parent = item.back

    # All Items in all_items with the same key as `completed` or `parent`
    # represent alternate derivations of the same span — we explore all of them.
    comp_cands = [it for it in all_items[completed.end] if it.key() == completed.key()]
    par_cands = [it for it in all_items[parent.end] if it.key() == parent.key()]

    for comp in comp_cands:
        for par in par_cands:
            for ct in enum_trees(comp, all_items):
                for pt in enum_trees(par, all_items):
                    yield (item.rule, pt[1] + [ct])


def tree_log_prob(tree):
    """Sum log-probs of all rules used in a parse tree."""
    rule, children = tree
    return rule.log_prob + sum(tree_log_prob(c) for c in children)


def tree_str(tree, indent=0):
    """Pretty-print a parse tree."""
    rule, children = tree
    label = f"{rule.lhs} -> {' '.join(rule.rhs)}"
    if not children:
        return "  " * indent + f"({label})"
    body = "\n".join(tree_str(c, indent + 1) for c in children)
    return "  " * indent + f"({label}\n{body})"


# ──────────────────────────────────────────────
# Output helpers
# ──────────────────────────────────────────────


def print_chart(chart, n, show_incomplete=False):
    """Print completed (and optionally incomplete) chart items."""
    for i in range(n + 1):
        entries = [
            it for it in chart[i].values() if show_incomplete or it.is_complete()
        ]
        if entries:
            print(f"\n=== Chart column {i} ===")
            for it in sorted(entries, key=lambda x: (x.start, x.dot)):
                print(f"  {it}")


def get_all_parses(all_items, start_symbol, n):
    """
    Collect every complete S-spanning item from all_items[n],
    enumerate all their parse trees, deduplicate, and sort best-first.
    Returns list of (log_prob, tree).
    """
    roots = [
        it
        for it in all_items[n]
        if it.is_complete() and it.rule.lhs == start_symbol and it.start == 0
    ]

    seen, results = set(), []
    for root in roots:
        for tree in enum_trees(root, all_items):
            key = tree_str(tree)
            if key not in seen:
                seen.add(key)
                results.append((tree_log_prob(tree), tree))

    results.sort(key=lambda x: -x[0])
    return results


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────


def main():
    if len(sys.argv) != 3:
        print("Usage: ./parse.py foo.gr foo.sen", file=sys.stderr)
        sys.exit(1)

    grammar = load_grammar(sys.argv[1])
    parser = EarleyParser(grammar)

    with open(sys.argv[2]) as fh:
        sentences = [line.strip() for line in fh if line.strip()]

    for sent in sentences:
        words = sent.split()
        print(f"\n{'='*60}")
        print(f"Sentence: {sent}")
        print(f"{'='*60}")

        chart, start_sym = parser.parse(words)

        # Print the chart (complete items only)
        print_chart(chart, len(words), show_incomplete=False)

        # Enumerate and print all parse trees
        parses = get_all_parses(parser.all_items, start_sym, len(words))

        if not parses:
            print("\n[No parse found]")
        else:
            print(f"\n[{len(parses)} parse(s) found]")
            for rank, (lp, tree) in enumerate(parses, 1):
                print(
                    f"\n--- Parse #{rank}  log_prob={lp:.6f}"
                    f"  prob={math.exp(lp):.6e} ---"
                )
                print(tree_str(tree))


if __name__ == "__main__":
    main()
