# Writing Documentation

Write in English and keep one topic per file. Document interfaces, state
machines, resource ownership, limits, errors, and implementation boundaries.
Link to the owning source rather than copying volatile implementation detail.

Do not include test chronology, full logs, benchmark snapshots, or run-specific commit hashes,
host paths, credentials, MAC addresses, serial numbers, or personal device
names. HIL pages define protocols and pass conditions, not previous runs.

Every new page must appear in a toctree. After a broad update, build the site,
check links, run the privacy and CJK scans, and provide one representative
excerpt from every changed Markdown file for review. Preserve referenced binary
assets unless repository-wide reference search proves they are unused.

Keep implementation status in the support matrix and test procedures in topic
pages. Keep acceptance summaries locally with source revisions, artifact hashes,
commands, fixture configuration, PASS/FAIL/SKIP outcomes, cleanup results and
known exclusions. Sanitize identifiers and credentials before retaining logs.
A historical result without reproducible identity must be labelled historical;
it cannot certify the current checkout. Refresh the matrix only when the
supported behavior or a known limit changes, not after every individual run.
