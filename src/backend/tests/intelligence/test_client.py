import asyncio
import json

import httpx
import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from backend.contracts.services import BudgetExceeded, InvalidModelOutput, ServiceUnavailable
from backend.models.reasoning import KeeraChatModel, ModelSettings, StructuredTasks


def invoke(model, context, **kwargs):
    return asyncio.run(model.ainvoke([HumanMessage(content="Synthetic public test")],
                                    context=context, **kwargs))


def response(content='{"ok":true}', **extra):
    return {"choices": [{"message": {"role": "assistant", "content": content, **extra},
                          "finish_reason": "stop"}], "usage": {"prompt_tokens": 10, "completion_tokens": 5}}


def client(handler, **settings):
    return KeeraChatModel(settings=ModelSettings(api_key="synthetic-key", **settings),
                          transport=httpx.MockTransport(handler))


def test_exact_alias_bearer_and_no_native_schema_assumption(context):
    def handler(req):
        body = json.loads(req.content)
        assert str(req.url) == "https://gateway.keera.ch/api/v1/chat/completions"
        assert req.headers["Authorization"] == "Bearer synthetic-key"
        assert body["model"] == "apertus-v1-5-70b" and not body["stream"]
        assert "response_format" not in body and "tools" not in body
        return httpx.Response(200, json=response())
    result = invoke(client(handler, model_name="apertus-v1-5-70b"), context)
    assert result.response_metadata["usage"]["completion_tokens"] == 5


def test_missing_configuration_and_offline_do_not_contact_gateway(context):
    def forbidden(req):
        pytest.fail("Unexpected HTTP call")
    with pytest.raises(ServiceUnavailable):
        invoke(KeeraChatModel(settings=ModelSettings(), transport=httpx.MockTransport(forbidden)), context)
    with pytest.raises(ServiceUnavailable):
        invoke(client(forbidden), context.model_copy(update={"mode": "offline"}))


def test_explicit_loopback_local_model_allowed_offline(context):
    model = KeeraChatModel(settings=ModelSettings(base_url="http://127.0.0.1:9999/v1", local=True,
        model_name="explicit-local-model"), transport=httpx.MockTransport(lambda req:httpx.Response(200,json=response())))
    assert invoke(model, context.model_copy(update={"mode":"offline"})).content


@pytest.mark.parametrize("status", [401, 403, 404, 500])
def test_safe_errors_do_not_leak_provider_body_or_key(context, status):
    calls = []
    def handler(req):
        calls.append(req)
        return httpx.Response(status, text="secret-provider-body synthetic-key")
    with pytest.raises(ServiceUnavailable) as error:
        invoke(client(handler), context)
    assert "synthetic-key" not in str(error.value) and "secret-provider-body" not in str(error.value)
    assert len(calls) == 1


def test_transient_retry_is_bounded(context):
    calls=[]
    def handler(req):
        calls.append(req)
        return httpx.Response(429, headers={"retry-after":"0"}) if len(calls)==1 else httpx.Response(200,json=response())
    assert invoke(client(handler),context).content
    assert len(calls)==2


def test_timeout_and_cancellation(context):
    calls=[]
    def timeout(req):
        calls.append(req)
        raise httpx.ReadTimeout("private-provider-detail")
    with pytest.raises(ServiceUnavailable):
        invoke(client(timeout),context)
    assert len(calls)==2
    def cancel(req):
        raise asyncio.CancelledError()
    with pytest.raises(asyncio.CancelledError):
        invoke(client(cancel),context)


def test_thinking_tools_rejected_before_http(context):
    def forbidden(req):
        pytest.fail("Thinking model must not receive tools")
    with pytest.raises(InvalidModelOutput):
        invoke(client(forbidden,model_name="apertus-v1-5-8b-thinking"),context,
               tools=[{"type":"function","function":{"name":"lookup","parameters":{"type":"object"}}}])


def test_tool_proposals_validate_allowlist_arguments_and_budget(context):
    tools=[{"type":"function","function":{"name":"lookup","parameters":{
        "type":"object","properties":{"query":{"type":"string"}},"required":["query"],
        "additionalProperties":False}}}]
    def make(name="lookup",args='{"query":"sensors"}'):
        return client(lambda req:httpx.Response(200,json=response("",tool_calls=[{
            "id":"call1","type":"function","function":{"name":name,"arguments":args}}])))
    tasks=StructuredTasks(make())
    proposals=asyncio.run(tasks.propose_tools([HumanMessage(content="Find public sensors")],tools,context))
    assert proposals[0].name=="lookup" and proposals[0].arguments=={"query":"sensors"}
    with pytest.raises(InvalidModelOutput):
        asyncio.run(StructuredTasks(make("shell")).propose_tools([],tools,context))
    with pytest.raises(InvalidModelOutput):
        asyncio.run(StructuredTasks(make(args='{"query":3}')).propose_tools([],tools,context))
    with pytest.raises(BudgetExceeded):
        asyncio.run(tasks.propose_tools([],tools,context.model_copy(update={"max_tool_calls":0})))


def test_oversize_and_truncated_outputs_fail(context):
    with pytest.raises(InvalidModelOutput):
        invoke(client(lambda req:httpx.Response(200,json=response("x"*2000)),max_response_bytes=100),context)
    data=response();data["choices"][0]["finish_reason"]="length"
    with pytest.raises(InvalidModelOutput):
        invoke(client(lambda req:httpx.Response(200,json=data)),context)


def test_verified_token_budget_requires_matching_counter(context):
    settings=ModelSettings(api_key="synthetic-key",input_token_limit=10)
    transport=httpx.MockTransport(lambda req:pytest.fail("Over-budget requests must not be sent"))
    with pytest.raises(ServiceUnavailable):
        invoke(KeeraChatModel(settings=settings,transport=transport),context)
    with pytest.raises(BudgetExceeded):
        invoke(KeeraChatModel(settings=settings,transport=transport,token_counter=lambda messages:11),context)


def test_usage_metadata_drops_unexpected_provider_fields(context):
    data=response();data["usage"]["untrusted_payload"]="must-not-leak"
    result=invoke(client(lambda req:httpx.Response(200,json=data)),context)
    assert result.response_metadata["usage"]=={"prompt_tokens":10,"completion_tokens":5}


def test_tool_history_round_trip_preserves_canonical_calls(context):
    def handler(req):
        wire=json.loads(req.content)["messages"]
        assert wire[1]["tool_calls"][0]["function"]["name"]=="lookup"
        assert wire[2]["tool_call_id"]=="call1"
        return httpx.Response(200,json=response())
    model=client(handler)
    messages=[HumanMessage(content="Find sensors"),AIMessage(content="",tool_calls=[{
        "id":"call1","name":"lookup","args":{"query":"sensors"}}]),
        ToolMessage(content="No results",tool_call_id="call1")]
    assert asyncio.run(model.ainvoke(messages,context=context)).content


def test_malformed_provider_metadata_has_safe_failure(context):
    data=response();data["usage"]="not-a-usage-object"
    with pytest.raises(InvalidModelOutput):
        invoke(client(lambda req:httpx.Response(200,json=data)),context)


def test_private_receipts_count_repairs_without_recording_model_content(context, interpretation):
    from backend.evidence import create_reasoning_services
    from backend.models.reasoning.fixtures import FixtureChatModel
    rows = []
    model = FixtureChatModel(responses=['PRIVATE INVALID RESPONSE', interpretation.model_dump(mode='json')])
    service = create_reasoning_services(model=model, receipt=rows.append)
    asyncio.run(service.interpret('Find sensors in Bern', {}, context))
    assert [r['attempt'] for r in rows if r['kind'] == 'model_call'] == [1, 2]
    assert [r['status'] for r in rows if r['kind'] == 'validation'] == ['repair_required', 'valid']
    assert 'PRIVATE INVALID RESPONSE' not in json.dumps(rows)
