# Local review and public-only release

This repository does not auto-publish. A release candidate is not a recorded owner
approval. Review the diff, methodological wording and completed checks before a
commit, tag, release or visibility change.

## Verify locally

From the repository root:

```sh
python tools/check_repository.py
```

This checks the public inventory, source syntax, JSON, local Markdown links and
limited credential patterns; runs unit tests; and rebuilds the synthetic example.
The CI configuration runs the same checks, but a locally passing run does not mean
a remote GitHub Actions job has been run. Review its results after the authorized
push. The CI only has `contents: read`; it contains no publishing step.

## Build an upload package

```sh
python tools/package_release.py --output ../raes-public.zip
```

The output name must not already exist and must be outside the repository. Only
files explicitly listed in `PUBLIC_FILES.txt` are included. The tool verifies its
ZIP inventory and prints the SHA-256. It does not contact GitHub or run tests on its
own, so run the checks first and test a freshly extracted public package as well.

When intentionally adding a public file, review it and add its exact relative path
to the sorted allowlist. Do not generate the allowlist by sweeping an actual research
workspace. Private inputs can be text too; a file extension is not a privacy test.

## Internal notes are not protected by their name

`_internal/` and `source_reference/` are ignored and excluded from public packaging.
Git ignore rules do not remove files already tracked, and a browser upload can
still expose files you select. See the [Git documentation](https://git-scm.com/docs/gitignore).
If using a working tree rather than this public ZIP, inspect both the staged file
list and repository history. Never upload a review/handoff archive containing
internal notes. Do not assume `.gitignore` is access control.

## Frozen example changes

Editing a frozen input, expected answer or computational file is a new example
version, not a reproduction. Record why it changed; review numeric expectations
independently; rerun the negative tests; then explicitly create a new manifest.
`tools/freeze.py create` requires an explicit file list and a new manifest path.
Never update hashes merely to bypass a detected discrepancy. Preserve prior releases.

## Check scope before calling a release complete

Owner review, local tests, host installation/use, remote CI and public publication
are different events. Record which occurred. In particular, the first Skill has a
scripted local rehearsal; an actual researcher/host trial remains a separate gate.
No benchmark of live AI accuracy is claimed by this synthetic starter.
