---
name: repo-worktree
description: >-
  Mandates and mechanizes task isolation in ptr727/ProjectTemplate fleet repos: every task,
  including a continuation of a prior session's task, creates its own git worktree on its own
  feature branch before its first file edit, based on the branch work starts on (develop on both
  fleet workflow models unless the task is explicitly about main-only content, never whichever
  branch a tool defaulted to), with a standalone-clone fallback when an executor cannot write
  both the standard worktree and its Git metadata. Also wraps the mechanics:
  creating a worktree with git worktree add, the fleet layout convention, listing what is in
  flight, preparing Husky.Net or Python pre-commit hooks in the new tree, and removing a
  worktree and its branch after merge. Use this whenever about to create or edit files in a
  fleet repo, whenever starting or resuming a task, whenever the task's branch is already
  checked out in a shared checkout, and whenever creating, listing, or removing a worktree.
  Triggers even when the session was launched in the primary checkout or the change looks like
  a one-line fix, because the primary checkout is the maintainer's own surface and the incident
  this guards against was two sessions sharing one checkout, each session's blanket add
  committing the other's uncommitted files.
---

# Repo Worktree

## Why This Exists

Two agent sessions once ran concurrently in the same primary checkout, on the same feature
branch, neither knowing the other was in the tree. One session's commits swept in the other
session's uncommitted files, so two commits landed carrying work their subjects never mention,
committed by a task that never saw it. No rule fired at the moment it was violated, which is the
first file edit: the commit-time and review-time skills all run after a sweep has already
happened. This skill is that missing task-start surface. `GOVERNANCE.md` "Repository Boundaries
and Write Safety" keeps the isolation law and wins on any disagreement, and the mechanics below
are this skill's own content.

## The Mandate

- **Every task isolates into its own worktree before its first file edit.** All new work begins
  by creating a unique worktree (or clone) on its own feature branch. The primary checkout is
  the maintainer's own surface, so a session launched there isolates before writing rather than
  after noticing contention.
- **A continuation re-isolates.** A session resuming prior work finds its branch already checked
  out somewhere and naturally resumes there, and that instinct is the hazard: a branch sitting
  checked out in a shared tree is exactly how two sessions end up in one checkout. Create a
  fresh worktree for the continuation and check the branch out there.
- **The moment is the first file edit, not the commit.** By commit time another task's
  uncommitted work can already be swept into the staging area, so isolating late protects
  nothing. Reading anywhere is fine, and the worktree exists before the first write.
- **Someone else's tree stays theirs.** A branch that changes when nothing you did changed it,
  or an edit of yours reverted with no conflict, means another task is live in that tree, and
  the response is to stop rather than to re-apply the edit, per `GOVERNANCE.md` "Repository
  Boundaries and Write Safety".

## The Base Branch

Base the worktree on the branch work starts on for the repository's model, not on whichever
branch a tool defaulted to. GitHub's own "default branch" setting reads `main`, but on both
fleet workflow models work starts on `develop`, so a worktree defaulted to "the default branch"
lands on `main` and silently misses everything merged to `develop` but not yet promoted. Branch
from `develop` unless the task is explicitly about `main`-only content, per `GOVERNANCE.md`
"Branching Model". Fetch immediately before creating and base on the remote ref, because a clone
is whatever it last fetched rather than the branch it names.

## Creating a Worktree

The fleet layout convention keeps every base clone and every in-flight task visible in one
place:

```text
~/repos/<Repo>                          base clone, on its default/working branch
~/repos/worktrees/<Repo>-<task-slug>    one worktree per in-flight task, own branch
~/repos/upstream/<owner>-<repo>         clone of a repo under another owner, not a fork
```

The top level carries no owner segment because everything in it is the fleet owner's own, an
original repo and a fork alike. A fork is named `<upstream-owner>-<upstream-repo>` at fork time,
so a fork of `acme/core` is `acme-core`, and its name identifies the upstream project and stays
unique in the flat namespace without an owner segment of its own. A repository adopted as the
owner's own work rather than kept as a fork is detached from its parent and keeps a plain name,
`widget` rather than `initech-widget`, since it no longer tracks anything upstream.

A clone of a repository under another owner is neither of those, and flattening one collides
rather than merely reading oddly: `acme/core` joined the way a fork is joined **is** the fork's
name, `acme-core`, while reduced to a bare `core` it names no project and collides with the next
`core` cloned from any other owner. Those clones live one level down under `upstream/`, named by
that same join, so `upstream/acme-core` sits beside the fork it would otherwise land on. The
segment states the relationship rather than the owner, so a reference checkout is told from a
working repo without a `git remote` call, and the names under it never compete with the flat
namespace above. The join is ambiguous in the abstract, since a hyphen in either half means
`acme-labs/core` and `acme/labs-core` produce one name, and it is kept anyway because it is the
fork convention's own join: the ambiguity is inherited from the flat namespace above rather than
introduced here, and it surfaces at clone time as a directory that already exists, where the
second clone takes a hand-picked name. A worktree off one of them keeps the flat worktrees path
under the same name, `~/repos/worktrees/<owner>-<repo>-<task-slug>`. Contributing a change from
such a clone is never a push out of it: fork the upstream first, per the
`upstream-contribution-workflow` skill, and that fork's own clone then belongs in the flat
namespace above, under the name this one already has.

```sh
git -C ~/repos/<Repo> fetch origin develop
git -C ~/repos/<Repo> worktree add ~/repos/worktrees/<Repo>-<task-slug> -b <task-branch> origin/develop
```

Before choosing that path, inspect the executor's active write boundaries. A linked worktree
requires write access to both of these locations:

- the intended `~/repos/worktrees/<Repo>-<task-slug>` worktree directory
- the base clone's `.git/worktrees/` administrative directory, which holds the index and locks

A writable worktree directory does not make the administrative directory writable.

Use the standard layout when both locations are writable. When either location is outside the
write boundary, create a standalone clone under a writable temporary root. Name it
`<temporary-root>/<Repo>-<task-slug>`, fetch immediately, and create the task branch from
`origin/develop`. A standalone clone keeps its worktree and Git administrative directory under
the same writable root. It therefore supports edits, explicit-path staging, commits, and branch
updates without sharing the base clone's index.

```sh
TASK_ORIGIN="$(git -C <base-clone> remote get-url origin)"
git clone --no-checkout "$TASK_ORIGIN" <temporary-root>/<Repo>-<task-slug>
git -C <temporary-root>/<Repo>-<task-slug> fetch origin develop
git -C <temporary-root>/<Repo>-<task-slug> switch -c <task-branch> origin/develop
```

Do not use a linked worktree under the temporary root when the base clone's Git metadata is
read-only. If an existing linked worktree must be kept, index operations require the executor's
scoped approval for that administrative path. Prefer the standalone clone so ordinary Git work
does not require repeated approval.

A continuation attaches the task's existing branch rather than forking a fresh one:

```sh
git -C ~/repos/<Repo> fetch origin <task-branch>
git -C ~/repos/<Repo> worktree add ~/repos/worktrees/<Repo>-<task-slug> <task-branch>
```

When the base clone holds only the remote-tracking ref, the same command creates the local
branch tracking `origin/<task-branch>` through git's ordinary checkout guessing, so a fresh
clone needs no separate branch setup. Git refuses to attach a branch that is already checked
out somewhere else, and that refusal is the mandate working, since the branch sitting checked
out in a shared tree is the hazard the continuation rule exists for. Return that checkout to
its own working branch first when its tree is clean, and stop when it is not, because a dirty
tree there may be another task's uncommitted work.

A machine not yet migrated to this layout still isolates exactly the same way, since the mandate
is the isolation rather than the path: create the worktree beside whatever layout the machine
has, and note that the base clone may live elsewhere than `~/repos/<Repo>`.

Claude Code's own `EnterWorktree` tool acts only on an explicit instruction from the user or the
project instructions, which is why the carried rules state this mandate in so many words. Given
a `name`, it creates the worktree under `.claude/worktrees/` inside the repo and bases it on the
GitHub default branch, which is the wrong path and the wrong base here. Create the worktree with
`git worktree add` as above, then attach with `EnterWorktree` `path:`, not `name:`.

## Preparing Git Hooks

A new worktree holds tracked hook configuration but not every generated hook runtime. Prepare
the hooks immediately after creating or attaching the worktree, before the first commit. A
shared `core.hooksPath` value does not make generated files such as `.husky/_/husky.sh` appear
in the new tree.

- **Husky.Net:** When `.husky/pre-commit` sources `.husky/_/husky.sh` and the local .NET tool
  manifest declares Husky.Net, run `dotnet tool restore`, then `dotnet husky install` from the
  worktree root.
- **Python pre-commit:** When `.pre-commit-config.yaml` exists, install the repository's declared
  Python environment, then run `pre-commit install` through that environment. A uv project runs
  `uv sync --frozen`, then `uv run pre-commit install`.
- **Repository override:** Follow a repository's explicit hook-setup instructions when they
  differ from these standard cases. Do not infer a replacement command from the language alone.

Treat hook preparation as worktree setup, not as recovery after a rejected commit. If setup
fails, report that boundary and fix the setup. Never bypass the hook to make the commit succeed.

## Listing and Cleanup

- `git worktree list`, run in any checkout of a repo, names that repo's base clone and every
  worktree with its branch. On the convention layout, one `ls ~/repos/worktrees/` reads what is
  in flight across the whole fleet.
- After the task's pull request merges, remove the worktree and its branch from the base clone:
  `git worktree remove ~/repos/worktrees/<Repo>-<task-slug>`, then `git branch -d <task-branch>`.
- After the task's pull request merges, remove a temporary standalone clone at its exact
  `<temporary-root>/<Repo>-<task-slug>` path. The remote branch follows the repository's normal
  pull request cleanup policy.
- A worktree that refuses removal is dirty, and force is not the fix: look at what is
  uncommitted in it first, since discarding uncommitted work runs only on explicit instruction,
  per the `git-commit-conventions` skill.
