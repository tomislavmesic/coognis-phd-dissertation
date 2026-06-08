from __future__ import annotations

import argparse

from app.core.config import settings
from app.services.synapse.artifact_fetcher import (
    SynapseArtifactDownloadError,
    ensure_synapse_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Download required SYNAPSE model artifacts.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Redownload artifacts even if they already exist locally.",
    )
    args = parser.parse_args()

    try:
        downloaded = ensure_synapse_artifacts(
            model_dir=settings.synapse_model_dir,
            base_url=settings.synapse_model_download_base_url,
            force=args.force,
        )
    except SynapseArtifactDownloadError as exc:
        print(str(exc))
        return 1

    if downloaded:
        print(f"Downloaded SYNAPSE artifacts: {', '.join(downloaded)}")
    else:
        print("SYNAPSE artifacts already present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
