"""Fair, explicit evidence limits at the web-registration/read boundary."""
from itertools import zip_longest


def bounded_evidence(groups, *, limit):
    """Round-robin existing ordered spans, retaining IDs unchanged and each source.

    Duplicates do not consume budget. The flag makes omitted support visible;
    callers must not imply that every registered passage was assessed.
    """
    unique = list(dict.fromkeys(key for row in zip_longest(*groups) for key in row if key is not None))
    return unique[:limit], len(unique) > limit
