"""Small snapshot metadata projection for authorization and run pins."""
from backend.data import schema as t


def snapshot_metadata():
    # Large per-chunk membership manifests stay server-side. The owner check needs
    # only its case ID; no authorization condition or hash is dropped.
    return [column for column in t.snapshots.c if column.name != 'manifest'] + [
        t.snapshots.c.manifest['runtime_case_id'].astext.label('runtime_case_id')]
