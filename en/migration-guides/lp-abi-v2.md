# LP Mailbox ABI Version 2

Version 2 extends the original READY/PING/STATUS exchange with a shared
sleep-control structure and PREPARE, ARM, ABORT, QUERY, and RECLAIM commands.

Version-1 consumers must not write the version-2 control block. Version-2
consumers validate magic, version, size, sequence, and CRC before using result
fields. Firmware advertises supported capabilities; hosts reject unsupported
wake or power-state requests rather than assuming a fallback.
