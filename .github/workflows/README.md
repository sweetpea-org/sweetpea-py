# GitHub Workflows

These workflows represent our current continuous integration strategy using
GitHub Actions.

A new workflow can be created by generating a new `.yml` file in this directory.
The syntax and directives supported are documented on the GitHub Docs page on
[Workflow syntax for GitHub
Actions](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions).

## Note on Target OSes

We use `macos-latest` as our macOS integration target.

GitHub Actions do not currently offer any Apple Silicon testing hardware. Until
they do, we'll need to test this architecture manually.

### To-dos

  * [ ] Add macOS target for Apple Silicon.

## Note on Target Python Versions

The code was originally written using Python 3.7.9. However, due to the change of libaray requirements for later python versions, therefore, we test with 3.9, as well as the latest version of each stable major release (3.9.x, 3.10.x, 3.11.x).

### To-dos

  * [ ] Add pre-release support (e.g., add 3.12.x alpha tests, if available).
