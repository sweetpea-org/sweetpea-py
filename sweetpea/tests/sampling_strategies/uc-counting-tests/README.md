Uniform Combinatoric Counting Tests
===================================

This directory is expected to contain multiple `*.py` files, each defining a single SweetPea experiment. Each file must produce a variable named `block` which contains the result of `fully_cross_block` used to construct the design.

Each file must also contain a comment of this form:

```python
# ASSERT COUNT = 42
```

Where `42` is the expected number of solutions to the design. The unit test will load each of these files, count the number of solutions to each design, and assert that it matches the value in the comment.
