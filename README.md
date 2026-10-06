# tutorial-ci

Monthly checks of the [EIC tutorials](https://github.com/eic/?q=tutorial) against the newest stable eic-shell.

- `check_paths.py` checks that every `root://` path, `xrdfs` path and `epic:` DID quoted in a tutorial
  is still available. A DID needs at least one open-access replica.
- `run_blocks.py` collects the code blocks marked with the `ci` class into one script, `tutorial.sh`,
  in the order a learner goes through the tutorial (`learners/setup.md`, `episodes/*.md`, then the other
  `learners/*.md` pages), and runs it in one working directory:

  ````markdown
  ```{.bash .ci}
  xrdcp root://... ./
  ```

  ```{.cpp .ci file="helloroot/src/helloroot.cxx"}
  #include <TH1D.h>
  ...
  ```
  ````

  `.bash` blocks are run as they are, `.python` blocks with `python3`, and a block with `file=` (any
  language: C++, CMake, ...) is written to that file, so a later `.bash` block can run `root -b -q`,
  `cmake` or `make` on it. The check fails if a block fails or ROOT prints `Error in <...>`.
  `tutorial.sh` is kept as a workflow artifact: the code of the whole tutorial in one file.

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
