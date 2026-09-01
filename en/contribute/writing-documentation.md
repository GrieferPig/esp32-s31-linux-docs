# Writing Documentation

Write in English and keep one topic per file. Document interfaces, state
machines, resource ownership, limits, errors, and implementation boundaries.
Link to the owning source rather than copying volatile implementation detail.

Do not include test chronology, full logs, benchmark snapshots, commit hashes,
host paths, credentials, MAC addresses, serial numbers, or personal device
names. HIL pages define protocols and pass conditions, not previous runs.

Every new page must appear in a toctree. After a broad update, build the site,
check links, run the privacy and CJK scans, and provide one representative
excerpt from every changed Markdown file for review. Preserve referenced binary
assets unless repository-wide reference search proves they are unused.
