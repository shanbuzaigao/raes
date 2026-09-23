# S3 Title and abstract screening, S4 Full-text screening

Goal: rule-based screens written from the criteria. Every record receives a decision and a reason; at full text, every criterion receives its own evidence. The criterion-level record is what the screening audit uses to find near misses.

## Ask

- For each criterion in `codebook/eligibility.json`: can it be decided from terms? Which terms or patterns support it, which terms block it, and is it checked at the title-and-abstract phase, the full-text phase or both?
- Which criteria cannot be decided from terms (for example whether a prompt steered the behaviour). They are left to the full-text reading, or to a model that screens under the criteria.
- How strict the title-and-abstract screen may be. The clarifications written in S0 decide it. "A record is kept when the abstract does not show ..." is the right default for recall, but a term screen can then exclude only explicit failures, and most records go on to the full text. Put the choice to the researcher with its cost: a lenient term screen and many full texts to retrieve; a stricter term screen, with its recall measured on known includes; or a model that screens under the criteria.
- Which tool extracts text from the PDFs, and its version. One tool for the whole project.
- Which papers the researcher already knows should be included. They are the first test of the rules.

## Write

- `screening/screening_rules.md` from `assets/screening/screening_rules.md`: one row per criterion, the decision logic of each phase, the checks before a run, the version log.
- The `CRITERIA` table at the top of `screening/screen_rules_template.py` (copied from `assets/screening/`): one entry per criterion with the same IDs as the eligibility file. The program's example entries are only an illustration; replace them.

## Writing the rules

- Besides whole-word terms, the program takes patterns (`any_of_regex`, `none_of_regex`), blocking terms that count only in the title (`title_none_of`, for example "systematic review"), and a check on a field of the record (`field` with `field_any_of`, for example the language). A record without an abstract is kept for the full text.
- The first failed criterion is the reason the PRISMA flow reports. Put the criteria about the type of report first, and treat the reason of every exclusion as an output that must be right, not only the decision.
- Full-text rules written from the criteria alone are usually wrong, because a full text also talks about other studies: "randomized" for a cited trial, depression in the discussion, an age range from a background sentence. Give the full-text phase its own table (`CRITERIA_FT`) and tie each term to the report's own study: its entry criteria, its allocation, its outcome measures. The table lists every criterion, and the program checks the IDs; a criterion the full text does not check keeps an entry whose `check_at` leaves out `ft`.
- Text extracted from PDFs splits words at line breaks ("ran- domized") and ends "sentences" at the period of "et al."; allow for both in the patterns.
- Write the full-text rules on a set of papers that were read, and check them there. After every revision, read the exclusions whose reason changed; that finds rule errors the decisions alone do not show.

## Run

- Title and abstract: `python screening/screen_rules_template.py ta records.csv --output <new folder>`. The records file is the export from S2, with the columns `record_id`, `title`, `abstract`.
- Full text: `python screening/screen_rules_template.py ft records.csv --after-ta <ta folder>/decisions.csv --texts <folder of record_id.txt files> --output <new folder>`. It screens the records kept at the first phase, checks that the first phase covered exactly this records file (every `record_id`, and the input hash in the run's `summary.json`), and stops if any record lacks its text. Records that the title-and-abstract audit confirmed enter from a frozen list passed with `--after-ta-audit`; the title-and-abstract decisions stay as they are. A record whose full text truly cannot be obtained is listed, one identifier per line, in a file passed with `--not-retrieved`; the program skips it and lists it in `summary.json`, so that it is reported as not retrieved, not as excluded.

## Retrieving the full texts

- Decide before retrieval starts how far it goes: every kept record, or a cap the researcher sets, or a model-based pre-screen that lowers the number. Run a small pilot first and report the yield and the time per record.
- Routes, in this order: an open-access interface meant for programs (for example the REST interface of Europe PMC, which returns open-access full texts as XML); the researcher's library access, by DOI; then one web search per remaining record for a legitimate copy (a repository, the publisher's open version). Website links that are meant for readers often refuse programs.
- A script stops at the first refusal from a server. It does not send the remaining requests.
- Keep a retrieval log: the record, the route, the source address, the file's SHA-256, or the reason for failure. Records that stay without a full text go into the not-retrieved list.
- In a browser driven by a model, the researcher signs in, never the model; a download dialog of the operating system cannot be closed by the model, so save files through the page where possible; after every reconnection of the browser, check that it is still the researcher's intended browser before opening anything.

## Check before moving on

- The known relevant papers are all kept.
- Title-and-abstract phase: the goal is recall; a record is excluded only when a criterion checked at that phase clearly fails. Full-text phase: every criterion must be supported.
- Every record has a decision and a reason; the rules file and the program carry the same version; any change to a term list is a new version.

## When a decision turns out wrong

- Before coding, look at the papers the full-text screen kept, at least when terms cannot decide every criterion. The audit in S5 asks only whether exclusions were wrong; nothing else checks the inclusions before coding. For each kept paper, put the matched passage of every criterion on an evidence sheet and record the reading of the criteria that terms cannot decide. Record who read them; a reading by the model that helped write the rules is not independent of the rules. If this check is skipped, give the coding codebook a field that confirms eligibility, so that a paper found ineligible during coding is recorded and not silently dropped.
- No record enters or leaves the included set by hand. A wrong full-text decision, an inclusion as much as an exclusion, wherever it surfaces (this reading, the screening audit, coding, the coding audit), changes the full-text rules: the smallest general revision, a new version, a full rerun. If the criterion itself was unclear, revise the clarifications in the eligibility file too.
- The title-and-abstract rules stay frozen once the full-text stage has started, because changing them changes the input of every later stage. A record that the title-and-abstract audit confirms goes onto a frozen list that the full-text screen reads as additional input (`--after-ta-audit` in the template program).
- When testing a revised rule, do not require that earlier exclusions stay excluded. An exclusion that nobody has read is not known to be right.

## If a model screens instead of code

Prepare it as an AI step (`ai-step-order.md`): the eligibility file is the codebook, and the prompts in `assets/validation/screening/` are a starting point for the screening prompts. The audit in S5 is the same in both cases.

## Watch for

- Removals by document type belong to S2, not to the screening program.
- A missing full text is a preparation problem, not a screening decision.
