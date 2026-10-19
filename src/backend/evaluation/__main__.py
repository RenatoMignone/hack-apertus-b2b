"""Read-only benchmark on an existing authorized run/capture. Never creates cases."""
import argparse
import json
import os
from pathlib import Path
from uuid import UUID

from backend.application.factories import ConfiguredEmbedding, ConfiguredReranker
from backend.application.persistence.store import RuntimeStore
from backend.config.runtime import RuntimeSettings
from backend.contracts.data import ModelConfiguration
from backend.data.cli import load_environment
from backend.data.database import engine_for
from backend.data.repositories.catalog import CatalogRepository
from backend.data.retrieval.hybrid import HybridSearch
from backend.evaluation.retrieval import QuerySuite, measure


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file', default='.env')
    parser.add_argument('--run-id', required=True, type=UUID)
    parser.add_argument('--suite', required=True, type=Path)
    parser.add_argument('--output', type=Path, default=Path('.local/retrieval-evaluation.json'))
    parser.add_argument('--repeats', type=int, default=1, choices=range(1, 6))
    parser.add_argument('--strategies', nargs='+', choices=['lexical', 'dense', 'rrf', 'reranked'], default=['lexical', 'dense', 'rrf'])
    args = parser.parse_args()
    load_environment(args.env_file)
    settings = RuntimeSettings.from_env()
    if len(settings.bindings) != 1:
        parser.error('use a dedicated single-operator environment')
    binding = settings.bindings[0]
    engine = engine_for(os.environ[binding.database_url_env])
    try:
        context = RuntimeStore(engine, settings, None).context(binding.access, args.run_id)
        embedder = ConfiguredEmbedding(settings)
        reranker = None
        if 'reranked' in args.strategies:
            configuration = ModelConfiguration.model_validate_json(Path(settings.reranker_configuration).read_text())
            reranker = ConfiguredReranker(configuration, settings.reranker_model_path, settings.model_device)
        searches = {kind: HybridSearch(engine, embedder, reranker=reranker, strategy=kind) for kind in dict.fromkeys(args.strategies)}
        report = measure(searches, CatalogRepository(engine), binding.access, context,
            QuerySuite.model_validate_json(args.suite.read_text()), args.repeats)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2), encoding='utf-8')
        args.output.chmod(0o600)
        print(json.dumps(report['summary'], indent=2))
    finally:
        engine.dispose()


if __name__ == '__main__':
    main()
