from types import SimpleNamespace

import pytest

from backend.contracts.services import ServiceUnavailable
from backend.models.reranking.local import LocalReranker


class CharacterTokenizer:
    def encode(self, text, paired='', **kwargs):
        assert kwargs.get('truncation') is False
        return list(range(len(text) + len(paired) + 3))
    def __call__(self, text, **kwargs):
        return {'offset_mapping':[(i,i+1) for i in range(len(text))]}


def test_windows_cover_literal_passage_without_truncating_query():
    pairs = []
    def predict(values, **kwargs):
        pairs.extend(values)
        return [float('glucose' in passage) for _,passage in values]
    reranker = LocalReranker(SimpleNamespace(predict=predict), CharacterTokenizer(), input_limit=30,config_hash='test')
    passage = 'A glucose sensor laboratory. '+ 'Signal processing research. '*2
    row = reranker.score_with_details('sensors', [passage])[0]
    windows = row['windows']
    assert len(windows) > 1 and row['score'] == 1
    assert ''.join(passage[w['char_start']:w['char_end']] for w in windows) == passage
    assert all(q == 'sensors' for q,_ in pairs)
    assert all(w['pair_tokens'] <= 30 for w in windows)


def test_original_query_over_budget_never_reaches_model():
    def forbidden(*args, **kwargs):
        pytest.fail('Original query must not be silently truncated')
    reranker = LocalReranker(SimpleNamespace(predict=forbidden),CharacterTokenizer(),input_limit=10,config_hash='test')
    with pytest.raises(ServiceUnavailable):
        reranker.score('x'*20,['glucose'])


def test_too_many_windows_falls_back_without_partial_scores():
    reranker = LocalReranker(SimpleNamespace(predict=lambda *a,**k:pytest.fail('budget')),
                            CharacterTokenizer(),input_limit=10,config_hash='test')
    with pytest.raises(ServiceUnavailable):
        reranker.score('q',['x'*300])


def test_asset_manifest_detects_changed_weights_before_loading(tmp_path):
    import hashlib
    import json
    from backend.models.reranking.local import verify_assets
    files = {'config.json':b'{}','model.safetensors':b'synthetic-weights','tokenizer.json':b'{}'}
    for name, data in files.items():
        (tmp_path/name).write_bytes(data)
    (tmp_path/'navigator-model-manifest.json').write_text(json.dumps({'artifact':'fixture',
        'revision':'fixture-revision','config_hash':'fixture-hash',
        'files':{name:hashlib.sha256(data).hexdigest() for name,data in files.items()}}))
    config = SimpleNamespace(artifact='fixture',revision='fixture-revision',config_hash='fixture-hash')
    verify_assets(tmp_path,config)
    (tmp_path/'model.safetensors').write_bytes(b'changed')
    with pytest.raises(ValueError,match='integrity'):
        verify_assets(tmp_path,config)
