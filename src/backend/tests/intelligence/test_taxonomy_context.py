import copy
import json

import pytest
from uuid import uuid4

from backend.evidence import create_reasoning_services
from backend.evidence.taxonomy_context import interpretation_taxonomy
from backend.models.reasoning.fixtures import FixtureChatModel


def test_compact_taxonomy_preserves_meaning_ids_aliases_and_edge_direction():
    first, second = str(uuid4()), str(uuid4())
    taxonomy = {'concepts': [{'concept_id':first,'code':'C01','definition':'Diabetes',
        'facet':'subcategory','created_at':'metadata','taxonomy_version_id':'version',
        'notes':{'reviewer':'provenance','scope':'Do not equate devices with diseases'}},
        {'concept_id':second,'definition':'Devices'}],
        'labels':[{'concept_id':first,'label_id':'metadata','created_at':'metadata','language':'en',
            'label':'Diabetes','preferred':True,'ambiguity':{'exclude':'diabetes insipidus'}}],
        'relations':[{'subject_id':first,'kind':'related','object_id':second}],
        'version':{'taxonomy_version_id':'version','created_at':'metadata'},
        'limitations':['related is not equivalent']}
    before = copy.deepcopy(taxonomy)
    result, mapping = interpretation_taxonomy(taxonomy)
    assert taxonomy == before
    assert mapping['C01'] == first
    assert result['concepts']['C01']['labels'][0][3] == {'exclude':'diabetes insipidus'}
    assert result['concepts']['C01']['notes'] == {'scope':'Do not equate devices with diseases'}
    assert result['relation_columns'] == ['subject','kind','object']
    assert result['relations'] == [['C01','related','@1']]
    assert result['version'] == {'taxonomy_version_id':'version'}
    assert result['limitations'] == taxonomy['limitations']


@pytest.mark.asyncio
async def test_large_database_taxonomy_fits_interpretation_without_dropping_concepts(context, interpretation):
    ids = [str(uuid4()) for _ in range(132)]
    taxonomy = {'concepts':[{'concept_id':key,'definition':'Medical research',
        'facet':'category','code':key[-8:],'created_at':'x'*200,'taxonomy_version_id':str(uuid4()),
        'notes':{'reviewer':'operator provenance '*20}} for key in ids],
        'labels':[{'concept_id':key,'label_id':str(uuid4()),'label':'Medical research',
            'language':'en','preferred':True,'ambiguity':{},'created_at':'x'*200} for key in ids],
        'relations':[{'subject_id':ids[i%132],'kind':'broader','object_id':ids[(i+1)%132]} for i in range(230)]}
    assert len(json.dumps(taxonomy)) > 80000
    response = interpretation.model_copy(update={'concepts':[ids[-1][-8:]]})
    model = FixtureChatModel(responses=[response.model_dump(mode='json')])
    service = create_reasoning_services(model=model)
    result = await service.interpret('Find glucose sensor R&D in Bern', taxonomy, context)
    sent = json.loads(model.calls[0][1].content)['taxonomy']
    assert result.concepts == [ids[-1]]
    assert len(sent['concepts']) == 132
    assert len(sent['relations']) == 230
    assert len(model.calls[0][1].content) < 80000
    assert sum(len(m.content) for m in model.calls[0]) < 80000


@pytest.mark.asyncio
async def test_activity_label_repair_identifies_field_instead_of_root(context, interpretation):
    bad = interpretation.model_dump(mode='json')
    bad['activity_label'] = 'continuous glucose monitoring sensors'
    model = FixtureChatModel(responses=[bad, interpretation.model_dump(mode='json')])
    service = create_reasoning_services(model=model)
    result = await service.interpret('Find glucose sensors research in Bern', {}, context)
    assert result.activity_label == interpretation.activity_label
    assert len(model.calls) == 2
    assert 'activity_label' in model.calls[1][-1].content
    assert 'too_long' in model.calls[1][-1].content
