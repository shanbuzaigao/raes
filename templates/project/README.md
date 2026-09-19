# New evidence-synthesis project

Start with plans/STAGE_PLAN.md and the exact eligibility criteria in
codebook/eligibility.json. Fill codebook/codebook.json, preserving source-based
choices and making proposals explicit. This directory contains no live runner.

Directories are described by their README files. run_pipeline.py reruns the coded
stages listed in pipeline.json and compares every output with the formal one; add a
stage there when its program and its formal output exist. Freeze each formal stage only
after its codebook, prompts, configuration and input frame are reviewed. Preserve
sources, accepted responses, technical failures, reconciliation and release hashes.
Keep installed environments and disposable caches outside this project, especially
when the working copy is synchronized. Do not upload source papers or private data.
