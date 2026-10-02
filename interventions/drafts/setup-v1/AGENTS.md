# Setup and tests

Run commands from `/workspace`. Test dependencies are preinstalled.

Install this checkout's package metadata offline into scratch space:

```sh
cd /workspace
python -m pip install --no-index --no-deps --no-build-isolation --target /tmp/click-site .
```

Put the source directory first so tests use your current edits, with the
installed distribution available for package metadata. For a focused public
check, use a test file such as:

```sh
PYTHONPATH=/workspace/src:/tmp/click-site python -m pytest -q tests/test_basic.py
```

Choose other public test files or `-k` expressions as needed. Before finishing,
run the complete public suite:

```sh
PYTHONPATH=/workspace/src:/tmp/click-site python -m pytest -q tests
```

Keep the public tests and project configuration unchanged.
