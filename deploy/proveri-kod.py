"""Static checks that catch the mistakes a live modification tends to introduce.

    python deploy/proveri-kod.py

Three of them, all of which have cost somebody points before:

- a duplicated route or view function, which Flask rejects at import with
  "View function mapping is overwriting an existing endpoint function";
- a `$` in front of a field name used as a key, where it belongs only in front
  of an operator or a field reference inside an expression;
- a set literal written where a dict was meant, `{"roi", -1}` instead of
  `{"roi": -1}`, which PyMongo cannot encode.
"""

import ast
import re
import sys
from pathlib import Path

SOURCE = Path(__file__).resolve().parent.parent / "src"

OPERATORS = {
    "$abs",
    "$add",
    "$and",
    "$avg",
    "$cond",
    "$count",
    "$dateToString",
    "$divide",
    "$eq",
    "$exists",
    "$expr",
    "$first",
    "$group",
    "$gt",
    "$gte",
    "$ifNull",
    "$in",
    "$limit",
    "$lookup",
    "$lt",
    "$lte",
    "$match",
    "$max",
    "$min",
    "$multiply",
    "$ne",
    "$nin",
    "$not",
    "$or",
    "$project",
    "$push",
    "$regex",
    "$set",
    "$skip",
    "$sort",
    "$subtract",
    "$sum",
    "$type",
    "$unwind",
    "$year",
}

# A set literal of strings and numbers where a dict was almost certainly meant.
SET_LITERAL = re.compile(r"\{\s*\"[^\"]+\"\s*,\s*-?\d")

failures = []


def report(path, message):
    failures.append(f"{path.name}: {message}")


def check_duplicates(path, tree):
    routes, functions = [], []

    # Only module level definitions: methods of two different model classes are
    # both allowed to be called __init__, and neither is a view.
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue

        functions.append(node.name)

        for decorator in node.decorator_list:
            if (
                isinstance(decorator, ast.Call)
                and getattr(decorator.func, "attr", None) == "route"
                and decorator.args
                and isinstance(decorator.args[0], ast.Constant)
            ):
                routes.append(decorator.args[0].value)

    for name, seen in (("route", routes), ("view function", functions)):
        for value in sorted({v for v in seen if seen.count(v) > 1}):
            report(path, f"duplicate {name} {value!r}")


def check_dollars(path, tree):
    """A key starting with $ has to be a known operator."""

    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue

        for key in node.keys:
            if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
                continue

            name = key.value

            if name.startswith("$") and name not in OPERATORS:
                report(path, f"line {key.lineno}: {name!r} is not a known operator")


def check_set_literals(path, text):
    for number, line in enumerate(text.splitlines(), start=1):
        if SET_LITERAL.search(line):
            report(path, f"line {number}: looks like a set literal, not a dict: {line.strip()}")


def main():
    for path in sorted(SOURCE.glob("*.py")):
        text = path.read_text()

        try:
            tree = ast.parse(text, filename=str(path))
        except SyntaxError as error:
            report(path, f"syntax error on line {error.lineno}: {error.msg}")
            continue

        check_duplicates(path, tree)
        check_dollars(path, tree)
        check_set_literals(path, text)

    if failures:
        print("FAIL")
        for failure in failures:
            print(" ", failure)
        return 1

    print(
        f"OK  {len(list(SOURCE.glob('*.py')))} modula, bez duplikata i bez gresaka u pipeline-ima"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
