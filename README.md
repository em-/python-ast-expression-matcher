# ExpressionMatcher - check if a collection matches a boolean expression

ExpressionMatcher lets you specify a boolean expression like
`foo or (bar and baz)` and check whether a given collection (a tuple, a list,
a dict or even a string) fulfils it.

## Getting Started

Just pass the expression to be evaluated to `ExpressionMatcher` and use the
resulting callable to test it against any collection that can handle the
`in`/`not in` membership test operators:

```pycon
>>> matches = ExpressionMatcher("foo or (bar and baz)")
>>> matches(["foo"])
True
>>> matches({"bar"})
False
>>> matches("barbbbaz")
True
```

If you instead want to try it on the command line:

```sh
$ ./match.py 'foo or (bar and baz)' bar baz
✅
$ ./match.py 'foo or (bar and baz)' meh
❌
```

## Running the tests

`ExpressionMatcher` uses `doctest`:

```sh
python3 -m doctest -v match.py
```

## Built With

To avoid depending on any parsing library, `ExpressionMatcher` (ab)uses the
[Python AST machinery](https://docs.python.org/3/library/ast.html) to parse
the expression, transform it to the actual membership tests and turn it into
real Python code.

## License

This project is licensed under the [MIT license](LICENSE.md), see
the [LICENSE](LICENSE) file for details.
