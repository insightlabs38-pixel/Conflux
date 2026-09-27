"""GCON-001/002 regression guard: `select_for_update()` chained with
`select_related(...)` must always pass `of=("self",)`.

PostgreSQL refuses `SELECT ... FOR UPDATE` across a LEFT OUTER JOIN (the
join a nullable FK's `select_related` produces): it raises
`NotSupportedError: FOR UPDATE cannot be applied to the nullable side of
an outer join` -- a real, previously-undetected bug this gate found
because SQLite (the bootstrap-checks default) silently allows the same
query and never surfaces it. This is a static AST check rather than
another DB-backed test so it runs everywhere, with no real database
needed, and catches a new call site the moment it's written rather than
only when someone happens to run the suite against real PostgreSQL.
"""

import ast
import pathlib

SRC = pathlib.Path(__file__).resolve().parents[3] / "src" / "api"


def _chain_calls(node):
    """Every method-call name in the chain `node` is the outermost call
    of, innermost first (e.g. `X.a().b().c()` -> ["a", "b", "c"]).
    """
    names = []
    while isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        names.append(node.func.attr)
        node = node.func.value
    return list(reversed(names))


def _has_of_kwarg(call_node):
    return any(kw.arg == "of" for kw in call_node.keywords)


def _offending_lines():
    offenders = []
    for path in SRC.rglob("*.py"):
        if "migrations" in path.parts:
            continue
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
                continue
            if node.func.attr != "select_for_update" or _has_of_kwarg(node):
                continue
            # Walk every Call node in the file to find one whose chain
            # passes through this exact select_for_update call.
            for outer in ast.walk(tree):
                if not (isinstance(outer, ast.Call) and isinstance(outer.func, ast.Attribute)):
                    continue
                if outer.func.attr != "select_related":
                    continue
                cursor = outer.func.value
                while isinstance(cursor, ast.Call) and isinstance(cursor.func, ast.Attribute):
                    if cursor is node:
                        offenders.append(f"{path.relative_to(SRC.parents[1])}:{node.lineno}")
                        break
                    cursor = cursor.func.value
                else:
                    continue
                break
    return offenders


def test_no_select_for_update_with_select_related_omits_of_self():
    offenders = _offending_lines()
    assert not offenders, (
        "select_for_update() chained with select_related() must pass "
        f'of=("self",) (PostgreSQL rejects locking a nullable outer join): {offenders}'
    )
