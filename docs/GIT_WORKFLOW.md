# Git workflow

The default branch contains the stable project history. Develop changes on a
short-lived feature branch and rebase it before opening or updating a pull
request.

## Start a change

```powershell
git switch main
git pull --ff-only
git switch -c feature/short-description
```

Make the change, run the tests, and create a focused commit:

```powershell
python -m pytest -q
git status
git add .
git diff --cached
git commit -m "Describe the change"
```

## Rebase before pushing

```powershell
git fetch origin
git rebase origin/main
git push -u origin feature/short-description
```

If a conflict occurs, edit the marked files, stage each resolution, and
continue:

```powershell
git add <resolved-file>
git rebase --continue
```

Use `git rebase --abort` to return to the pre-rebase state if the resolution
needs to be restarted. After rebasing a branch that has already been published,
use `git push --force-with-lease`; never use an unrestricted force push.

## Pre-push checklist

- Run the complete test suite.
- Ensure `data/`, SQLite databases, caches, and virtual environments are not
  tracked.
- Review `git diff --cached` before committing.
- Document API, schema, or normalisation changes.
- Confirm that no downloaded personal or confidential data has been added.
