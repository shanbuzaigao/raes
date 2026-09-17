# Contributing

Keep changes small and tied to a demonstrated need. Preserve the S0-S12 stage model,
the codebook-first sequence and the distinction between a research protocol and
this deliberately small teaching implementation. Do not add a live API client or
second Skill without discussing scope first.

For a codebook/protocol change, state the affected decision and update the Chinese
mirror. For code, add an example or a regression test. Do not hide a change by
replacing expected outputs or hashes without explaining it. Keep source judgments
and numerical calculations separate; do not imply that a passing fixture measures
accuracy on real papers.

Run `python tools/check_repository.py`. Review any new entry in `PUBLIC_FILES.txt`
for privacy and licensing. No credentials, paper PDFs, author data or raw research
responses should enter this framework repository. Use synthetic minimal failures
in issue reports. Keep installed environments and caches outside the working tree.

I review methodological decisions and decide when something is released. A working memo
or a proposed PR is not a preregistration or an approved change to a frozen study.
