# S1 Search and S2 Remove duplicates

Goal: fixed search terms; a dated snapshot for every search; one table of deduplicated records that the screening program reads, with a reason for every record that did not reach it.

## Ask

- Which databases. The search terms, fixed before the first search: the same terms in every database, adapted only to each database's syntax, and the same terms in every later update, where only the date range changes.
- Which papers the researcher already knows should be found. Five known papers are too few to test a search: take the full list of included studies of one or two earlier reviews and check that the terms find them, before the formal search. Gaps found this way are general (for example an age given only as a number, or an allocation described without the word "random").
- The date range of this search, and how each source exports its results. A source without an export function needs a small script; record it.
- How duplicates are removed: in a reference manager, or with the skill's script (below).
- Whether records are removed by document type before screening (for example reviews, protocols, surveys). If so, by which rule; every such removal is logged and reported under "records removed before screening" in the PRISMA flow diagram. The screening program does not repeat these removals.

## If the model runs the search for the researcher

The protocol has the researcher run the search. When the researcher asks the assisting model to do it, the same record is kept, and: the model never signs in anywhere and never enters credentials; it asks before every download and says how many files and how large; it moves the downloaded files unchanged into `search/raw/<snapshot>/` and records their SHA-256; it pastes the query from `search/SEARCH_LOG.md` and checks that the database received exactly that text; and it searches all databases on the same date, because the snapshot carries one date.

## S2 without a reference manager

S2 is defined by its outputs, not by a tool: `records.csv` with the columns `record_id`, `title` and `abstract`; a ledger that gives the reason for every removal; and the check that records identified equals records removed plus records passed to screening. A reference manager produces them by hand. Every new project has its own copy of the deduplication script and of its rules in `search/` (from `assets/search/`), so that a rerun does not depend on the installed skill. Run in the project folder, `python search/dedupe_records.py --inputs search/raw/<snapshot>/* --rules search/dedup_rules.json --output search/dedup/<new folder>` produces them from exports in PubMed (MEDLINE) format, Web of Science plain text or RIS; name the files explicitly, or let the shell expand `*`. Exports may overlap, for example two search strings of one database: a record that occurs again gets a running suffix, the rules merge the occurrences, the ledger keeps every occurrence with its file, and `summary.json` lists every input file with its hash and record count. The same file given twice is refused. It matches by PubMed ID, then DOI, then normalized title and year, never merges records whose identifiers conflict, and lists uncertain pairs in `review_pairs.csv` for the researcher, whose decisions it reads back from a decisions file. The rules are in `search/dedup_rules.json`; a change is a new version. A preprint and its journal version are two reports of one study, not duplicates: two records with the same title and year of which exactly one carries a preprint label (`report_version_labels` in the rules) are an uncertain pair (rule R4), the answer in S2 is `not_duplicate`, and the same-study check (S6) links them and chooses the representative by its written rule. A `not_duplicate` decision keeps the pair apart even when another rule, or a chain of duplicates, would join them; the script reports the contradiction instead of merging, and the run stays provisional until it is resolved.

## Removing records by document type

- Test the rule on the exported labels before approving it, and read a sample of what it removes.
- PubMed puts "Journal Article" on nearly every record and often adds "Research Support, ...". A rule that removes a record only when every label is listed then removes almost nothing, unless such labels are declared neutral.
- Web of Science labels some primary studies "Review" by their number of references. A record that also carries a trial label should stay.

## Write

`search/SEARCH_LOG.md` with: the snapshot identifier (for example `search_through_2026-04-30`); for each source, the exact query string, the date range and the number of records; the duplicates removed; the document-type removals and their rule; the name and SHA-256 of the records file.

## Check before moving on

- Records identified = records removed + records passed to screening.
- The raw exports are saved unchanged, and the counts per source can be regenerated from them.
- The search terms are identical across sources and across updates.
- Every uncertain pair has a decision by the researcher.

## Watch for

- Queries retyped from memory instead of copied.
- Spreadsheets that silently truncate a long abstract. The records file is the source from here on; spreadsheets are for viewing.
- An update to the search is a new snapshot with its own audit record.
