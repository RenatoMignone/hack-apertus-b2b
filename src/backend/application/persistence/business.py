"""Manual company plans bound to immutable input revisions and report approval."""
from uuid import uuid4
from sqlalchemy import insert, select, text
from backend.contracts.business import BusinessContext
from backend.contracts.services import ServiceUnavailable, StaleRevision
from backend.data import schema as t


class Business:
    def rich_outputs_available(self, connection=None):
        if not self.settings.rich_outputs_enabled:
            return False
        if connection is None:
            with self.engine.connect() as c:
                return self.rich_outputs_available(c)
        return bool(connection.execute(text("SELECT to_regclass('cases.business_contexts') IS NOT NULL")).scalar_one())

    def business_context(self, access, case_id, input_id=None):
        with self.session(access) as c:
            case = self.case(c, access, case_id)
            if not self.rich_outputs_available(c):
                return {}
            return c.execute(select(t.business_contexts.c.payload).where(t.business_contexts.c.case_id == case_id,
                t.business_contexts.c.input_id == (input_id or case['current_input_id']))).scalar_one_or_none() or {}

    def copy_business_context(self, c, access, case_id, old_input, new_input):
        if not self.rich_outputs_available(c) or old_input == new_input:
            return
        previous = c.execute(select(t.business_contexts.c.payload).where(t.business_contexts.c.case_id == case_id,
            t.business_contexts.c.input_id == old_input)).scalar_one_or_none()
        if previous is not None:
            c.execute(insert(t.business_contexts).values(context_id=uuid4(), case_id=case_id,
                input_id=new_input, entered_by=access.principal_id, payload=previous))

    def set_business_context(self, access, key, case_id, body, request_id):
        if not body['permitted_context_confirmed']:
            raise ValueError('permitted operator context confirmation required')
        values = BusinessContext.model_validate(body['values']).model_dump(mode='json', exclude_none=True)
        def callback(c):
            case = self.case(c, access, case_id)
            if not self.rich_outputs_available(c):
                raise ServiceUnavailable()
            if case['revision'] != body['expected_revision']:
                raise StaleRevision()
            change = self.repositories(c)[0].edit(access, case_id, expected_revision=case['revision'],
                instruction='Operator updated manually entered business plans.', kind='focus')
            c.execute(insert(t.business_contexts).values(context_id=uuid4(), case_id=case_id,
                input_id=change['input_id'], entered_by=access.principal_id, payload=values))
            profile = self.settings.default_profile_id
            if not profile:
                raise ServiceUnavailable()
            return self.start(c, access, case_id, change['input_id'], profile, request_id)
        return self.command(access, key, f'business:{case_id}', body, callback)
