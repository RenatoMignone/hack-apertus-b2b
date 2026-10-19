from backend.data.research_budget import bounded_evidence


def test_many_duplicate_page_spans_fit_reader_and_preserve_each_source():
    groups = [[f"page{page}:{span}" for span in range(27)] for page in range(10)]
    selected, omitted = bounded_evidence(groups, limit=100)
    assert len(selected) == 100 and omitted
    assert all(sum(item.startswith(f"page{page}:") for item in selected) == 10 for page in range(10))
    assert selected[:10] == [group[0] for group in groups]


def test_duplicate_spans_do_not_consume_budget_or_hide_complete_coverage():
    assert bounded_evidence([[1, 2], [1, 3]], limit=3) == ([1, 2, 3], False)
    assert bounded_evidence([], limit=100) == ([], False)
