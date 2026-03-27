# Earley Parser

### Computational Linguistics Assignment

A probabilistic Earley parser for context-free grammars, implemented in Python. This assignment is adapted from Prof. Jason Eisner's NLP course at Johns Hopkins University.

## Repository Structure

```
.
├── earley-parser.pdf   # Assignment specification
├── parse.py            # Main parser implementation
├── README.md           # This file
├── soldier.gr          # Grammar for Q3 sentence
├── soldier.sen         # Sentence file for Q3
├── timeflies.gr        # Grammar from Figure 1 (Q1 & Q2)
├── timeflies.sen       # Sentence file for Q1 & Q2
└── venv/               # Python virtual environment
```

## Requirements

- Python 3.7+
- No external dependencies (uses only the standard library)

## Setup

```bash
# Create and activate virtual environment (optional)
python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

## Usage

```bash
./parse.py foo.gr foo.sen
```

Or explicitly with Python:

```bash
python3 parse.py foo.gr foo.sen
```

### File Formats

**Grammar file (`.gr`)** — each non-blank, non-comment line has the form:

```
probability   LHS   RHS_1   RHS_2 ...
```

Example:

```
1.0   S    NP VP
0.35  NP   N
0.25  NP   N N
0.5   V    flies
```

- Probabilities for rules sharing the same LHS must sum to 1.
- Epsilon rules (`X →`) are not supported.
- Files are case-sensitive.

**Sentence file (`.sen`)** — one sentence per line; blank lines are skipped.

## Running the Assignment Questions

**Q1 & Q2 — Chart and probabilities for "time flies like an arrow":**

```bash
python3 parse.py timeflies.gr timeflies.sen
```

**Q3 — Chart and parse trees for "the man shot the soldier with a gun":**

```bash
python3 parse.py soldier.gr soldier.sen
```

## Output Format

For each sentence the parser prints:

1. **The chart** — one column per word boundary (0 through n), showing all complete items in the form:

   ```
   [start,end] LHS -> RHS •   w=log_weight
   ```

2. **All parse trees** — ranked by probability, printed as indented trees with log-probability and probability values:
   ```
   --- Parse #1  log_prob=-5.408132  prob=4.480000e-03 ---
   (S -> NP VP
     (NP -> N
       (N -> time))
     ...)
   ```

## Implementation Notes

### Data structures

| Structure      | Purpose                                                                                               |
| -------------- | ----------------------------------------------------------------------------------------------------- |
| `chart[i]`     | `dict {key → Item}` — one entry per `(rule, dot, start, end)`; used for O(1) duplicate detection only |
| `all_items[i]` | `list` of every `Item` ever pushed; preserves all derivation chains for parse enumeration             |
| `agenda[i]`    | FIFO queue of items to process in column `i`                                                          |

### Complexity

- **Time:** O(n³) for a fixed grammar — each unique chart key is enqueued and processed exactly once.
- **Space:** O(n²) — at most one entry per `(rule, dot, start, end)` across n+1 columns.
- **Push:** O(1) — a single hash lookup determines whether the key is new; duplicate items are never re-queued.

### Correctness design

The `chart` dict and `all_items` list serve distinct purposes. The chart provides O(1) deduplication; `all_items` preserves every derivation's back-pointer independently. The chart is never updated in-place — doing so would overwrite the first derivation's back-pointer and make it unrecoverable. `enum_trees()` recursively walks `all_items` to enumerate all parse trees.

## References

- Eisner, J. JHU NLP course materials: [Earley algorithm slides](https://www.cs.jhu.edu/~jason/465/PowerPoint/lect10-earley.ppt) and [hw-parse notes](https://www.cs.jhu.edu/~jason/465/hw-parse/hw-parse.pdf).
