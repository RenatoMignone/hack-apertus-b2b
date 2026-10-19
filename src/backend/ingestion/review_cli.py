"""Export review candidates or validate/apply an explicit corpus-owner manifest."""
import argparse
import json
from pathlib import Path
from uuid import UUID

from backend.config.settings import Settings
from backend.contracts.data import AccessContext
from backend.data.cli import load_environment
from backend.data.database import engine_for, check_schema
from backend.ingestion.review import CorpusReview


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file', default='.env')
    parser.add_argument('--principal', type=UUID, required=True)
    parser.add_argument('--namespace', required=True)
    parser.add_argument('--scope', type=UUID, required=True)
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--limit', type=int, default=50)
    parser.add_argument('--output', type=Path, default=Path('.local/corpus-review.json'))
    args = parser.parse_args()
    if args.apply and not args.manifest:
        parser.error('--apply requires an explicit reviewed manifest')
    load_environment(args.env_file)
    engine = engine_for(Settings.from_env().database_url)
    try:
        check_schema(engine)
        access = AccessContext(principal_id=args.principal, namespace=args.namespace)
        repository = CorpusReview(engine)
        if args.manifest:
            manifest = json.loads(args.manifest.read_text())
            if manifest.get('scope_id') != str(args.scope):
                parser.error('manifest and selected scope differ')
            result = repository.review(access, manifest, apply=args.apply)
        else:
            result = repository.candidates(access, args.scope, args.limit)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, default=str))
        args.output.chmod(0o600)
        print(json.dumps({'applied': result.get('applied', False), 'output_written': True}))
    finally:
        engine.dispose()


if __name__ == '__main__':
    main()
