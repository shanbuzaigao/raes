# S1 Search and S2 Remove duplicates

Goal: fixed search terms; a dated snapshot for every search; one deduplicated library exported as a text file that the screening program reads.

## Ask

- Which databases. The search terms, fixed before the first search: the same terms in every database, adapted only to each database's syntax, and the same terms in every later update, where only the date range changes.
- The date range of this search, and how each source exports its results. A source without an export function needs a small script; record it.
- Which reference manager removes the duplicates, and what the deduplicated library is exported as.
- Whether records are removed by document type before screening (for example reviews, protocols, surveys). If so, by which rule; every such removal is logged and reported under "records removed before screening" in the PRISMA flow diagram. The screening program does not repeat these removals.

## Write

`search/SEARCH_LOG.md` with: the snapshot identifier (for example `search_through_2026-04-30`); for each source, the exact query string, the date range and the number of records; the duplicates removed; the document-type removals and their rule; the name and SHA-256 of the exported text file.

## Check before moving on

- Records identified = records removed + records passed to screening.
- The raw exports are saved unchanged, and the counts per source can be regenerated from them.
- The search terms are identical across sources and across updates.

## Watch for

- Queries retyped from memory instead of copied.
- Spreadsheets that silently truncate a long abstract. The exported text file is the source from here on; spreadsheets are for viewing.
- An update to the search is a new snapshot with its own audit record.
