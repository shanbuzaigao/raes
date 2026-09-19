# S3 Title and abstract screening, S4 Full-text screening

Goal: rule-based screens written from the criteria. Every record receives a decision and a reason; at full text, every criterion receives its own evidence. The criterion-level record is what the screening audit uses to find near misses.

## Ask

- For each criterion in `codebook/eligibility.json`: can it be decided from terms? Which terms or patterns support it, which terms block it, and is it checked at the title-and-abstract phase, the full-text phase or both?
- Which criteria cannot be decided from terms (for example whether a prompt steered the behaviour). They are left to the full-text reading, or to a model that screens under the criteria.
- Which tool extracts text from the PDFs, and its version. One tool for the whole project.
- Which papers the researcher already knows should be included. They are the first test of the rules.

## Write

- `screening/screening_rules.md` from `assets/screening/screening_rules.md`: one row per criterion, the decision logic of each phase, the checks before a run, the version log.
- The `CRITERIA` table at the top of `screening/screen_rules_template.py` (copied from `assets/screening/`): one entry per criterion with the same IDs as the eligibility file. The program's example entries are only an illustration; replace them.

## Run

- Title and abstract: `python screening/screen_rules_template.py ta records.csv --output <new folder>`. The records file is the export from S2, with the columns `record_id`, `title`, `abstract`.
- Full text: `python screening/screen_rules_template.py ft records.csv --after-ta <ta folder>/decisions.csv --texts <folder of record_id.txt files> --output <new folder>`. It screens only the records kept at the first phase and stops if any of them lacks its text. A kept record whose full text truly cannot be obtained is listed, one identifier per line, in a file passed with `--not-retrieved`; the program skips it and lists it in `summary.json`, so that it is reported as not retrieved, not as excluded.

## Check before moving on

- The known relevant papers are all kept.
- Title-and-abstract phase: the goal is recall; a record is excluded only when a criterion checked at that phase clearly fails. Full-text phase: every criterion must be supported.
- Every record has a decision and a reason; the rules file and the program carry the same version; any change to a term list is a new version.

## When a decision turns out wrong

- Before coding, look at the papers the full-text screen kept, at least when terms cannot decide every criterion. Record who read them; a reading by the model that helped write the rules is not independent of the rules.
- No record enters or leaves the included set by hand. A wrong full-text decision, an inclusion as much as an exclusion, wherever it surfaces (this reading, the screening audit, coding, the coding audit), changes the full-text rules: the smallest general revision, a new version, a full rerun. If the criterion itself was unclear, revise the clarifications in the eligibility file too.
- The title-and-abstract rules stay frozen once the full-text stage has started, because changing them changes the input of every later stage. A record that the title-and-abstract audit confirms goes onto a frozen list that the full-text screen reads as additional input.
- When testing a revised rule, do not require that earlier exclusions stay excluded. An exclusion that nobody has read is not known to be right.

## If a model screens instead of code

Prepare it as an AI step (`ai-step-order.md`): the eligibility file is the codebook, and the prompts in `assets/validation/screening/` are a starting point for the screening prompts. The audit in S5 is the same in both cases.

## Watch for

- Removals by document type belong to S2, not to the screening program.
- A missing full text is a preparation problem, not a screening decision.
