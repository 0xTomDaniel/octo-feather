# The split's refusals of a moved function reading the hub's identity (review r1, unvalidated-codemod-input)

Scratch copies of f7f16367 (git archive f7f16367 scripts pyproject.toml justfile), each with one line added to the
hub's q(), after its docstring: `_ = __doc__`, `_ = sys.argv[0]`, `_ = __file__`. Then, per copy:

    uv run --locked --offline python evidence/gh1274-split/split.py --tree COPY --no-baselines --meta COPY.json
    PYTHONHASHSEED=0 uv run --locked --offline python evidence/gh1274-split/probe.py base COPY   (check.py's names check, independent)

## doc: 2050:    _ = __doc__

split.py: exit 1
    split: refused: q reads __doc__ and is not in the table (tables.py DOC_READERS)
    files written: none (no scripts/lane_cli.py; the hub unchanged: 1 COMMANDS table of functions)
probe.py base: readers ['q'], which check.py reports as `names: FAIL: q reads __file__, __doc__ or sys.argv and is not in the tables`

## argv: 2050:    _ = sys.argv[0]

split.py: exit 1
    split: refused: q reads sys.argv and is not in the table
    files written: none (no scripts/lane_cli.py; the hub unchanged: 1 COMMANDS table of functions)
probe.py base: readers ['q'], which check.py reports as `names: FAIL: q reads __file__, __doc__ or sys.argv and is not in the tables`

## file: 2050:    _ = __file__

split.py: exit 1
    split: refused: q reads __file__ and is not in the table (tables.py LAUNCH, DIR_READERS)
    files written: none (no scripts/lane_cli.py; the hub unchanged: 1 COMMANDS table of functions)
probe.py base: readers ['q'], which check.py reports as `names: FAIL: q reads __file__, __doc__ or sys.argv and is not in the tables`

The clean copy (no line added) splits to files byte-identical to this branch's scripts/.
