# Earley Parser

### Computational Psycholinguistics Assignment 5

A probabilistic Earley parser for context-free grammars, implemented in Python. This assignment is adapted from Prof. Jason Eisner's NLP course at Johns Hopkins University.

## Repository Structure

```
.
├── docs/
│   ├── Assignment.pdf      # Original assignment specification
│   └── Report.pdf          # Submission report (Q1–Q4)
├── arith.gr                # Arithmetic grammar (JHU test)
├── arith.sen               # Arithmetic sentences (JHU test)
├── papa.gr                 # Papa grammar (JHU Earley animation test)
├── papa.sen                # Papa sentences
├── parse.py                # Main parser implementation
├── permissive.gr           # Permissive grammar (JHU sanity check)
├── permissive.sen          # Permissive sentences
├── README.md               # This file
├── soldier.gr              # Grammar for Q3 sentence
├── soldier.sen             # Q3 sentence: "the man shot the soldier with a gun"
├── timeflies.gr            # Grammar from Figure 1 (Q1 & Q2)
├── timeflies.sen           # Q1 sentence: "time flies like an arrow"
└── venv/                   # Python virtual environment
```

## Requirements

- Python 3.7+
- No external dependencies (standard library only)

## Setup

```bash
python3 -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate
```

## Usage

```bash
python3 parse.py foo.gr foo.sen [--best-only]
```

| Flag          | Effect                                                        |
| ------------- | ------------------------------------------------------------- |
| _(none)_      | Print chart + all parse trees with probabilities              |
| `--best-only` | Print chart + best parse weight only (use for large grammars) |

### File Formats

**Grammar file (`.gr`)** - one rule per line:

```
probability   LHS   RHS_1   RHS_2 ...
```

- Probabilities for rules sharing the same LHS must sum to 1
- Epsilon rules are not supported
- Files are case-sensitive

**Sentence file (`.sen`)** - one sentence per line; blank lines are skipped.

## Running the Assignment Questions

```bash
# Q1 & Q2: chart and parse trees for "time flies like an arrow"
python3 parse.py timeflies.gr timeflies.sen

# Q3: chart and parse trees for "the man shot the soldier with a gun"
python3 parse.py soldier.gr soldier.sen
```

## Running the JHU Test Files

Use `--best-only` for all JHU test grammars. They are large and tree enumeration would not terminate in reasonable time.

```bash
python3 parse.py permissive.gr permissive.sen --best-only

python3 parse.py papa.gr papa.sen --best-only

python3 parse.py arith.gr arith.sen --best-only

python3 parse.py wallstreet.gr wallstreet.sen --best-only
```

## Implementation Notes

### Data structures

| Structure      | Purpose                                                                                               |
| -------------- | ----------------------------------------------------------------------------------------------------- |
| `chart[i]`     | `dict {key -> Item}`: one entry per `(rule, dot, start, end)`; used for O(1) duplicate detection only |
| `all_items[i]` | `list` of every `Item` ever pushed; preserves all derivation chains for parse enumeration             |
| `agenda[i]`    | FIFO queue of items to process in column `i`                                                          |

### Complexity

| Property | Bound | Reason                                                                   |
| -------- | ----- | ------------------------------------------------------------------------ |
| Space    | O(n²) | At most one chart entry per `(rule, dot, start, end)` across n+1 columns |
| Time     | O(n³) | Each unique key is enqueued and processed exactly once                   |
| Push     | O(1)  | Single hash lookup; duplicate keys are never re-queued                   |

## References

- Eisner, J. JHU NLP course: [Earley slides](https://www.cs.jhu.edu/~jason/465/PowerPoint/lect10-earley.ppt) · [hw-parse notes](https://www.cs.jhu.edu/~jason/465/hw-parse/hw-parse.pdf)
