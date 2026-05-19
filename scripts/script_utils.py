import json
from pathlib import Path
from typing import Any

from astrapy.data_types import DataAPIDate
from astrapy.info import CollectionDefinition, CollectionVectorOptions, VectorServiceOptions
from astrapy.constants import VectorMetric

from app.config import settings
from app.database import get_connected_database


def get_database():
    """Return a connected AstraDB database handle."""
    return get_connected_database()


def get_collection(name: str | None = None):
    """Return a collection handle using the configured default if not provided."""
    database = get_database()
    return database.get_collection(name or settings.collection_name)


def build_collection_definition() -> CollectionDefinition:
    """Build the vector-enabled collection definition from shared settings."""
    return CollectionDefinition(
        vector=CollectionVectorOptions(
            metric=VectorMetric.COSINE,
            service=VectorServiceOptions(
                provider=settings.embedding_provider,
                model_name=settings.embedding_model_name,
            ),
        ),
    )


def get_data_file_path(filename: str = "quickstart_dataset.json") -> Path:
    """Return a path under the repository data directory."""
    return Path(__file__).resolve().parent.parent / "data" / filename


def load_json_file(path: Path) -> list[dict[str, Any]]:
    """Load a JSON array from disk."""
    with open(path, "r", encoding="utf8") as file:
        return json.load(file)


def build_vectorized_documents(json_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert raw seed data into Astra-ready documents."""
    return [
        {
            **data,
            "due_date": (
                DataAPIDate.from_string(data["due_date"])
                if data.get("due_date")
                else None
            ),
            "$vectorize": (
                f"title: {data['title']} | summary: {data['summary']} | genres: {', '.join(data['genres'])}"
            ),
        }
        for data in json_data
    ]

# Made with Bob
