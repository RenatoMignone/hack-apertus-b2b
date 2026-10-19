"""Versioned vocabulary from pinned taxonomy profiles; never a retrieval filter."""
from pydantic import Field, field_validator
from backend.contracts.data import Contract

PILOT_FIELDS = {
    'medtech': 'Medtech', 'biotechnology': 'Biotechnology',
    'pharmaceuticals': 'Pharmaceuticals', 'digital_health': 'Digital health',
    'healthcare_services': 'Healthcare services', 'other': 'Other', 'unknown': 'Unknown',
}


class DomainVocabulary(Contract):
    version: str = Field(default='pilot-v1', min_length=1, max_length=100)
    fields: dict[str, str] = Field(default_factory=lambda: dict(PILOT_FIELDS))
    institutions: dict[str, str] = Field(default_factory=lambda: {
        'UniBE': 'University of Bern', 'ARTORG': 'ARTORG', 'DCB': 'Diabetes Center Berne'})

    @field_validator('fields', 'institutions')
    @classmethod
    def valid_labels(cls, values):
        import re
        if len(values) > 200 or any(not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,79}', key)
                or not label.strip() or len(label) > 200 for key, label in values.items()):
            raise ValueError('domain vocabulary requires bounded codes and nonempty labels')
        return values

    @classmethod
    def from_taxonomy(cls, context):
        configuration = context.get('profile', {}).get('configuration', {})
        vocabulary = cls.model_validate(configuration.get('domain', {}))
        # Unknown/unclassified intent is always representable. These labels do
        # not constrain vector search or replace the reviewed topic taxonomy.
        return vocabulary.model_copy(update={'fields': {'unknown': 'Unknown', 'other': 'Other', **vocabulary.fields}})
