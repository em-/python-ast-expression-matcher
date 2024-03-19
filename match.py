# ExpressionMatcher - check if a collection matches a boolean expression
#
# SPDX-FileCopyrightText: © 2024 Emanuele Aina
#
# SPDX-License-Identifier: MIT

import ast
import sys


class ExpressionMatcher:
    class Transformer(ast.NodeTransformer):
        def __init__(self, expression: str | None) -> None:
            self.expression = expression

        def error(self, msg: str, lineno: int, col_offset: int):
            raise SyntaxError(
                msg,
                (None, lineno, col_offset + 1, self.expression),
            )

        def generic_visit(self, node: ast.AST) -> ast.AST:
            items_var = "items"

            match node:
                case ast.Name(id=id, ctx=ast.Load()):
                    return ast.Compare(
                        left=ast.Constant(value=id),
                        ops=[ast.In()],
                        comparators=[ast.Name(id=items_var, ctx=ast.Load())],
                    )
                case ast.Constant(value=value):
                    return ast.Compare(
                        left=ast.Constant(value=str(value)),
                        ops=[ast.In()],
                        comparators=[ast.Name(id=items_var, ctx=ast.Load())],
                    )
                case ast.Call(func=ast.Name(id="empty"), args=[], keywords=[]):
                    return ast.UnaryOp(
                        op=ast.Not(),
                        operand=ast.Name(id=items_var, ctx=ast.Load()),
                    )
                case ast.Call(func=ast.Name(id="anything"), args=[], keywords=[]):
                    return ast.Constant(value=True)
                case (
                    ast.Expression()
                    | ast.BoolOp(op=ast.Or() | ast.And())
                    | ast.Or()
                    | ast.And()
                    | ast.UnaryOp(op=ast.Not())
                    | ast.Not()
                ):
                    pass
                case ast.Call(func=ast.Name(id="empty" | "anything" as func)):
                    # point the error to the argument list
                    self.error(
                        f"invalid syntax, {func}() does not accept any argument",
                        node.func.end_lineno or node.lineno,
                        node.func.end_col_offset or node.col_offset,
                    )
                case ast.Call(func=ast.Name()):
                    self.error(
                        "invalid syntax, unknown function",
                        node.lineno,
                        node.col_offset,
                    )
                case ast.BinOp(left=ast.Name()):
                    # point the error to the operator
                    self.error(
                        "invalid syntax, unsupported operation",
                        node.left.end_lineno or node.lineno,
                        node.left.end_col_offset or node.col_offset,
                    )
                case _:
                    self.error("invalid syntax", node.lineno, node.col_offset + 1)
            return super().generic_visit(node)

    def __init__(self, expression: str | None) -> None:
        """Inizialize the ExpressionMatcher

        >>> ast.unparse(ExpressionMatcher("foo and bar").ast)
        "'foo' in items and 'bar' in items"
        >>> ast.unparse(ExpressionMatcher("foo or empty()").ast)
        "'foo' in items or not items"
        >>> ast.unparse(ExpressionMatcher(None).ast)
        'True'
        >>> ExpressionMatcher("foo + 1")
        Traceback (most recent call last):
          ...
          File "<string>", line 1
            foo + 1
               ^
        SyntaxError: invalid syntax, unsupported operation
        >>> ExpressionMatcher("foo()")
        Traceback (most recent call last):
          ...
          File "<string>", line 1
            foo()
            ^
        SyntaxError: invalid syntax, unknown function
        >>> ExpressionMatcher("empty(1)")
        Traceback (most recent call last):
          ...
          File "<string>", line 1
            empty(1)
                 ^
        SyntaxError: invalid syntax, empty() does not accept any argument
        """
        if not expression:
            expression = "anything()"
        parsed = ast.parse(expression, mode="eval")
        transformed = self.Transformer(expression).visit(parsed)
        ast.fix_missing_locations(transformed)
        compiled = compile(transformed, filename="<ast>", mode="eval")

        def matches(items):
            match = eval(compiled, {}, {"items": items})
            return match

        self.expression = expression
        self.ast = transformed
        self.matches = matches

    def __call__(self, items) -> bool:
        """Test if the expression matches when applied on the `items` collection

        >>> matches = ExpressionMatcher("foo and bar")
        >>> matches([])
        False
        >>> matches({"foo"})
        False
        >>> matches(["foo", "bar"])
        True
        >>> matches("foobarbaz")
        True
        >>> matches = ExpressionMatcher("foo or empty()")
        >>> matches({"foo"})
        True
        >>> matches([])
        True
        >>> matches(["bar"])
        False
        """
        return self.matches(items)

    def __repr__(self) -> str:
        """String representation

        >>> repr(ExpressionMatcher("foo and bar"))
        "ExpressionMatcher('foo and bar')"
        >>> repr(ExpressionMatcher(""))
        "ExpressionMatcher('anything()')"
        >>> repr(ExpressionMatcher(None))
        "ExpressionMatcher('anything()')"
        """
        return f"{self.__class__.__qualname__}('{self.expression}')"


if __name__ == "__main__":
    matches = ExpressionMatcher(sys.argv[1])
    is_match = matches(sys.argv[2:])
    print("✅" if is_match else "❌")
    sys.exit(0 if is_match else 1)
