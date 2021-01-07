# TODOs for the new Python version of SweetPea Core

  * [ ] Refactor Haskell library implementations.
      * The goal is to remove this sub-library entirely and render its
        implementation more Pythonic.
      * [ ] Replace Control.Monad.Trans.State with custom state-keeping
            mechanism (or else just pass values through functions).
      * [ ] Remove Data.Maybe by implementing reasonable default values and
            checking these in the tops of functions.
      * [ ] Remove Data.Ord by using subtypes for parser.py::Request.
      * [ ] Data.List stuff might be fine? Look over them.
      * [ ] Text.Read maybe is removable, or at least can be factored into a
            local function in testers.py.
  * [ ] Provide simple interface for use in non-core Python code.
  * [ ] Provide scripted interface for running core code separate from anything
        else.
  * [ ] Implement test suite.
  * [ ] Document everything.
  * [ ] I think a lot of the lists can be replaced with iterators, if handled
        correctly. Certainly more list comprehensions can be used.
  * [ ] Move sweetpea_core to sweetpea/core.
  * [ ] Normalize types. Various type aliases for `int` appear to be used
        inconsistently, which leads to the need for calls to `typing.cast` that
        really should not be used in these cases.
