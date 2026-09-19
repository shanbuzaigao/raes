# S7 Data preparation (optional)

Goal: for a paper that comes with data files or needs matched comparison data, a short per-paper summary computed by code, so that the coding model reads a summary instead of a long raw file. A paper whose statistics are all in the text skips this stage.

## Ask

- Does the paper report all the statistics in its text? If yes, skip.
- What data exist: reported statistics, supplements, repositories.
- Which conditions are eligible, from the main text. Conditions that appear only in a repository are not included automatically.
- The hierarchy for comparison data (for example: the same paper, then a source the paper names, then a project-wide bank of baselines). Finding no match is allowed; the row is kept and its effect size is left uncomputed.
- The aggregation rule: aggregate within independent units; repeated rounds are not independent observations.

## If there is no usable data

Record what is missing, draft the data request for the researcher to send, mark the paper as waiting, and move on. The paper stays in the coding queue.

When the authors answer: data files are processed in this stage like any other data. A single corrected value, or a published erratum, enters through the reconciliation record of the coding audit (S9), with its source.

## Write

- `papers/<id>/data_summary.csv`, produced by a processing script kept with the paper, with the sources of every number.
- `papers/TRACKER.csv` with four states kept apart: materials reviewed, data available, preparation complete, coding run.

## An AI may assist

For example by reading a repository's documentation or writing the processing script. It must be given the eligibility criteria word for word, the same file as every other stage.

## Check before moving on

Counts, sample sizes and matches verified independently. Prepared does not mean coded.
