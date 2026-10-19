import asyncio

from backend.tests.intelligence.test_reasoning import services


def test_expanded_operator_lead_cannot_abort_clear_research(context, interpretation):
    value = interpretation.model_dump(mode="json")
    value["leads"] = ["University of Bern", "ARTORG", "Invented Institute"]
    service, model = services(value)
    result = asyncio.run(service.interpret("Find biosensors at UniBE and ARTORG in Bern.", {}, context))
    assert result.leads == ["ARTORG"]
    assert result.needs == interpretation.needs
    assert result.bern_intents == interpretation.bern_intents
    assert len(model.calls) == 1
