"""Opt-in HTTP acceptance against the isolated smoke harness; synthetic inputs only.

Never point at a shared deployment. Start smoke on loopback first. Output files
contain fictional case data and should be kept in an ignored local directory.
"""
import argparse
import hashlib
import json
from pathlib import Path
from time import monotonic, sleep
from uuid import uuid4

import httpx


SCENARIOS = {
    'match': 'Fictional evaluation only: a fictional glucose sensor company seeks research collaboration in Bern. '
        'Use the fictional B2B Sensor Laboratory test corpus as evidence only within this fictional exercise. '
        'Find documented glucose biosensor development and prototype signal evaluation capabilities. '
        'Do not assume clinical approval, facility availability or willingness to collaborate.',
    'clarify': 'Fictional evaluation only: our company makes devices and wants help in Bern, but '
        'we have not specified which technical capability we need. Ask us to clarify the capability.',
    'no_match': 'Fictional evaluation only: a satellite company wants propulsion research collaboration in Bern. '
        'Identify documented expertise in satellite ion propulsion. Exclude medical sensors and biosensing. '
        'Return no match when the supplied fictional sources have no propulsion expertise.',
}


def run(base, output, scenarios):
    if base not in {'http://127.0.0.1:8012', 'http://localhost:8012'}:
        raise ValueError('Acceptance requires the isolated loopback smoke server on port 8012')
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    with httpx.Client(base_url=base, headers={'Authorization': 'Bearer synthetic-browser-smoke'},
                      timeout=30, trust_env=False) as client:
        def request(method, url, body=None):
            response = client.request(method, url, json=body, headers={'Idempotency-Key': uuid4().hex})
            response.raise_for_status()
            return response

        def poll(url, *, answer=False):
            deadline = monotonic() + 600
            questions = 0
            while monotonic() < deadline:
                state = request('GET', url).json()
                if state['status'] in {'succeeded', 'committed', 'failed', 'cancelled'}:
                    return state, questions
                if state['status'] == 'waiting_for_input':
                    if not answer:
                        raise AssertionError('Unexpected clarification on clear request')
                    for question in state['questions']:
                        if question['status'] != 'open':
                            continue
                        request('POST', url + '/answers', {'input_id': state['input_id'],
                            'question_id': question['id'], 'answer': SCENARIOS['match']})
                        questions += 1
                sleep(.5)
            raise TimeoutError('Acceptance polling budget exhausted')

        for scenario in scenarios:
            started = monotonic()
            row = {'scenario': scenario, 'synthetic_sources': True, 'actual_model': True}
            try:
                created = request('POST', '/api/v1/cases', {'prompt': SCENARIOS[scenario]}).json()
                row['case_id'] = created['case_id']
                state, questions = poll(created['status_url'], answer=scenario == 'clarify')
                row.update(status=state['status'], error_code=state.get('error_code'), questions=questions)
                if state['status'] != 'succeeded':
                    raise AssertionError('Case did not complete')
                url = '/api/v1/cases/' + created['case_id']
                detail = request('GET', url).json()
                revision = next(r for r in detail['revisions'] if r['id'] == detail['currentRevisionId'])
                (output / (scenario + '-case.json')).write_text(json.dumps(detail, indent=2))
                row['reasons'] = len(revision['reasons'])
                assert (not revision['reasons']) if scenario == 'no_match' else bool(revision['reasons'])
                if scenario == 'clarify':
                    assert questions > 0
                if revision['reasons']:
                    report = url + '/reports/' + revision['id']
                    review_body = {'decision': 'accepted', 'expected_result_hash': revision['resultHash'],
                        'expected_selection_hash': detail['selectionHash']}
                    blocked = client.post(report + '/reviews', json=review_body,
                        headers={'Idempotency-Key': uuid4().hex})
                    assert blocked.status_code == 409
                    for i, reason in enumerate(revision['reasons']):
                        selection = request('PUT', report + '/reasons/' + reason['id'] + '/selection',
                            {'selection': 'kept' if i == 0 else 'rejected',
                             'expected_result_hash': revision['resultHash']}).json()
                    review_body['expected_selection_hash'] = selection['selection_hash']
                    review = request('POST', report + '/reviews', review_body).json()
                    exported = request('POST', url + '/exports', {'result_id': revision['id'],
                        'review_id': review['review_id'], 'expected_result_hash': revision['resultHash'],
                        'expected_selection_hash': selection['selection_hash'], 'format': 'pdf'}).json()
                    operation, _ = poll(exported['status_url'])
                    assert operation['status'] == 'committed'
                    pdf = request('GET', operation['download_url']).content
                    assert pdf.startswith(b'%PDF-')
                    (output / (scenario + '.pdf')).write_bytes(pdf)
                    row['pdf_sha256'] = hashlib.sha256(pdf).hexdigest()
                    changed = request('POST', url + '/messages', {'text': 'Use shorter sentences, preserving all claims and caveats.',
                        'kind': 'formatting', 'expected_revision': detail['revision']}).json()
                    edited, _ = poll(changed['status_url'])
                    assert edited['status'] == 'succeeded'
                    assert client.get(operation['download_url']).status_code == 409
                    row['stale_download_blocked'] = True
                row['passed'] = True
            except (AssertionError, httpx.HTTPError, TimeoutError) as error:
                row.update(passed=False, failure=type(error).__name__)
            row['seconds'] = round(monotonic() - started, 3)
            rows.append(row)
            (output / 'acceptance.json').write_text(json.dumps(rows, indent=2))
            print(json.dumps(row), flush=True)
    return all(row['passed'] for row in rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default='http://127.0.0.1:8012')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--scenarios', nargs='+', choices=SCENARIOS, default=list(SCENARIOS))
    args = parser.parse_args()
    raise SystemExit(0 if run(args.base_url, args.output, args.scenarios) else 1)


if __name__ == '__main__':
    main()
