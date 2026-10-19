"""The static publication must preserve its inspected source record."""
import copy
import json
from pathlib import Path
import subprocess
import sys

import pytest

from backend.evaluation.render_proof_of_concept import REPOSITORY, validate_receipt


@pytest.fixture
def receipt():
    return json.loads((REPOSITORY/'docs/proof-of-concept/retrieval-results.json').read_bytes())


def test_recorded_totals_and_selected_references_are_consistent(receipt):
    assert validate_receipt(receipt)['returned_passage_occurrences'] == 120


def test_totals_and_source_mismatches_are_rejected(receipt):
    changed = copy.deepcopy(receipt)
    changed['distinct_documents'] += 1
    with pytest.raises(ValueError, match='totals'):
        validate_receipt(changed)
    receipt['selected_examples'][0]['source_url'] = 'https://fixture.invalid/wrong'
    with pytest.raises(ValueError, match='ranked source'):
        validate_receipt(receipt)


def test_failed_integrity_cannot_render_as_passed(receipt):
    receipt['queries'][0]['hits'][0]['body_sha256_valid'] = False
    receipt['body_hash_checks_passed'] -= 1
    with pytest.raises(ValueError, match='failed passage integrity'):
        validate_receipt(receipt)


def test_quote_offsets_must_match_recorded_span(receipt):
    receipt['selected_examples'][0]['quotes'][0]['char_end'] += 1
    with pytest.raises(ValueError, match='Quote offsets'):
        validate_receipt(receipt)


def test_cli_rebuilds_from_public_record_without_mutating_docs(tmp_path):
    paths = [REPOSITORY/'docs/proof-of-concept'/name for name in ['README.md', 'retrieval-results.json']]
    original = [path.read_bytes() for path in paths]
    output = tmp_path/'presentation.pdf'
    subprocess.run([sys.executable, '-m', 'backend.evaluation.render_proof_of_concept',
                    '--output', str(output)], cwd=tmp_path, check=True, capture_output=True)
    assert output.read_bytes().startswith(b'%PDF-')
    assert [path.read_bytes() for path in paths] == original
