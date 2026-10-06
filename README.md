# tutorial-ci

Monthly checks of the [EIC tutorials](https://github.com/eic/?q=tutorial) against the newest stable eic-shell.

- `check_paths.py` checks that every `root://` path, `xrdfs` path and `epic:` DID quoted in a tutorial
  is still available. A DID needs at least one open-access replica.
- `run_blocks.py` runs the code blocks marked with the `ci` class, in order
  (`learners/setup.md`, then `episodes/*.md`), in one working directory:

  ````markdown
  ```{.bash .ci}
  xrdcp root://... ./
  ```

  ```{.cpp .ci file="Test.C"}
  void Test() { ... }
  ```
  ````

  `.bash` and `.python` blocks are run, a block with `file=` is written to that file.

## Workflows

- `monthly.yml` runs both checks for every tutorial on the 5th of each month, and on demand
  (Actions → monthly → Run workflow, optionally with an eic-shell release).
- `check.yml` is reusable. To check a tutorial on its own pull requests, add to the tutorial:

  ```yaml
  on: [pull_request, workflow_dispatch]
  jobs:
    check:
      uses: eic/tutorial-ci/.github/workflows/check.yml@main
  ```

## Running locally

Inside eic-shell, from a directory containing the tutorial clone:

```bash
python3 tutorial-ci/check_paths.py tutorial-analysis
python3 tutorial-ci/run_blocks.py tutorial-analysis work
```
