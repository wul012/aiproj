from __future__ import annotations

import ast
from pathlib import Path


def function_def(tree: ast.Module, name: str) -> ast.FunctionDef | None:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


def arg_names(function: ast.FunctionDef | None) -> tuple[str, ...]:
    if function is None:
        return ()
    return tuple(arg.arg for arg in [*function.args.args, *function.args.kwonlyargs])


def raises_system_exit_from_main(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Raise):
            continue
        if not isinstance(node.exc, ast.Call):
            continue
        if getattr(node.exc.func, "id", "") != "SystemExit":
            continue
        return any(isinstance(arg, ast.Call) and getattr(arg.func, "id", "") == "main" for arg in node.exc.args)
    return False


def has_direct_script_entrypoint(tree: ast.Module) -> bool:
    return any(isinstance(node, ast.If) and is_dunder_main_check(node.test) for node in tree.body)


def is_dunder_main_check(node: ast.AST) -> bool:
    if not isinstance(node, ast.Compare):
        return False
    if len(node.ops) != 1 or len(node.comparators) != 1:
        return False
    if not isinstance(node.ops[0], ast.Eq):
        return False
    left = node.left
    right = node.comparators[0]
    return (
        isinstance(left, ast.Name)
        and left.id == "__name__"
        and isinstance(right, ast.Constant)
        and right.value == "__main__"
    )


def module_name(relative: str) -> str:
    path = Path(relative)
    return ".".join((*path.with_suffix("").parts,))


__all__ = [
    "arg_names",
    "function_def",
    "has_direct_script_entrypoint",
    "is_dunder_main_check",
    "module_name",
    "raises_system_exit_from_main",
]
