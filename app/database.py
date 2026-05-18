"""
AstraDB connection management and repository access.
"""

import logging
from typing import Optional, List, Dict, Any
from astrapy import DataAPIClient
from astrapy.exceptions import DataAPIException

from app.config import settings

logger = logging.getLogger(__name__)


class AstraConnectionManager:
    """Create and manage Astra client/database/collection access."""

    def __init__(self) -> None:
        self.client = None
        self.database = None
        self._connected = False

    def connect(self) -> bool:
        """Initialize the Astra client and database handle."""
        try:
            self.client = DataAPIClient(settings.astra_db_application_token)
            self.database = self.client.get_database(
                settings.astra_db_api_endpoint,
                keyspace=settings.astra_db_keyspace
            )
            self._connected = True
            logger.info("Successfully connected to AstraDB")
            return True
        except DataAPIException as e:
            logger.error(f"Failed to connect to AstraDB: {str(e)}")
            self._connected = False
            self.client = None
            self.database = None
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to AstraDB: {str(e)}")
            self._connected = False
            self.client = None
            self.database = None
            return False

    def is_connected(self) -> bool:
        """Check if the database handle has been initialized."""
        return self._connected and self.database is not None

    def _ensure_database(self):
        """Return the active database or raise if not connected."""
        if self.database is None:
            raise RuntimeError("AstraDB database is not initialized")
        return self.database

    def get_collection(self, collection_name: str):
        """Return a collection handle for the provided collection name."""
        database = self._ensure_database()
        return database.get_collection(collection_name)

    def ensure_collection(self, collection_name: str):
        """
        Ensure a collection exists and return its handle.

        This is intentionally idempotent: if creation fails because the
        collection already exists, the existing collection handle is returned.
        """
        database = self._ensure_database()

        try:
            collection = database.get_collection(collection_name)
            if collection is not None:
                return collection
        except DataAPIException as e:
            logger.debug(f"Initial get_collection failed for {collection_name}: {str(e)}")

        try:
            collection = database.create_collection(collection_name)
            logger.info(f"Created AstraDB collection: {collection_name}")
            return collection
        except DataAPIException as e:
            logger.warning(
                f"Collection creation for {collection_name} did not complete cleanly, "
                f"attempting to fetch existing collection: {str(e)}"
            )
            return database.get_collection(collection_name)


class LibraryBookRepository:
    """CRUD and search operations for the library books collection."""

    def __init__(self, collection) -> None:
        self.collection = collection

    def set_collection(self, collection) -> None:
        """Update the active collection handle."""
        self.collection = collection

    def _ensure_collection(self):
        """Return the active collection or raise if not initialized."""
        if self.collection is None:
            raise RuntimeError("AstraDB collection is not initialized")
        return self.collection

    @staticmethod
    def _normalize_library_book_document(doc: Dict[str, Any]) -> Dict[str, Any]:
        """Map Astra document fields to API response fields."""
        normalized = dict(doc)
        normalized["id"] = str(normalized.pop("_id"))

        if "due_date" in normalized and normalized["due_date"] is not None:
            if hasattr(normalized["due_date"], "to_string"):
                normalized["due_date"] = normalized["due_date"].to_string()
            elif hasattr(normalized["due_date"], "isoformat"):
                normalized["due_date"] = normalized["due_date"].isoformat()

        return normalized

    async def create_library_book(self, library_book_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new library book document in the collection."""
        try:
            collection = self._ensure_collection()
            document = dict(library_book_data)
            
            # Add $vectorize field for embedding generation (same as ingestion flow)
            # Uses summary and genres fields to create embeddings
            if "summary" in document and "genres" in document:
                genres_str = ", ".join(document["genres"]) if isinstance(document["genres"], list) else str(document["genres"])
                document["$vectorize"] = f"summary: {document['summary']} | genres: {genres_str}"
            
            result = collection.insert_one(document)

            created = collection.find_one({"_id": result.inserted_id})
            if created:
                return self._normalize_library_book_document(created)

            document["_id"] = result.inserted_id
            return self._normalize_library_book_document(document)

        except DataAPIException as e:
            logger.error(f"Failed to create library book: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating library book: {str(e)}")
            return None

    async def get_library_book(self, library_book_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a library book document by ID."""
        try:
            collection = self._ensure_collection()
            result = collection.find_one({"_id": library_book_id})

            if result:
                return self._normalize_library_book_document(result)
            return None

        except DataAPIException as e:
            logger.error(f"Failed to get library book {library_book_id}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting library book {library_book_id}: {str(e)}")
            return None

    async def list_library_books(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """List library book documents with pagination."""
        try:
            collection = self._ensure_collection()
            cursor = collection.find({}, limit=skip + limit)
            library_books = []

            for index, doc in enumerate(cursor):
                if index < skip:
                    continue
                library_books.append(self._normalize_library_book_document(doc))
                if len(library_books) >= limit:
                    break

            return library_books

        except DataAPIException as e:
            logger.error(f"Failed to list library books: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error listing library books: {str(e)}")
            return []

    async def update_library_book(self, library_book_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a library book document by ID."""
        try:
            collection = self._ensure_collection()
            
            # If summary or genres are being updated, regenerate $vectorize field
            if "summary" in update_data or "genres" in update_data:
                # Get current document to access fields not being updated
                current_doc = collection.find_one({"_id": library_book_id})
                if current_doc:
                    summary = update_data.get("summary", current_doc.get("summary", ""))
                    genres = update_data.get("genres", current_doc.get("genres", []))
                    
                    if summary and genres:
                        genres_str = ", ".join(genres) if isinstance(genres, list) else str(genres)
                        update_data["$vectorize"] = f"summary: {summary} | genres: {genres_str}"
            
            result = collection.find_one_and_update(
                {"_id": library_book_id},
                {"$set": update_data},
                return_document="after"
            )

            if result:
                return self._normalize_library_book_document(result)
            return None

        except DataAPIException as e:
            logger.error(f"Failed to update library book {library_book_id}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error updating library book {library_book_id}: {str(e)}")
            return None

    async def delete_library_book(self, library_book_id: str) -> bool:
        """Delete a library book document by ID."""
        try:
            collection = self._ensure_collection()
            result = collection.delete_one({"_id": library_book_id})
            return result.deleted_count > 0

        except DataAPIException as e:
            logger.error(f"Failed to delete library book {library_book_id}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting library book {library_book_id}: {str(e)}")
            return False

    async def count_library_books(self) -> int:
        """Count total number of library book documents in the collection."""
        try:
            collection = self._ensure_collection()
            return collection.count_documents({}, upper_bound=1000000)
        except DataAPIException as e:
            logger.error(f"Failed to count library books: {str(e)}")
            return 0
        except Exception as e:
            logger.error(f"Unexpected error counting library books: {str(e)}")
            return 0

    async def search_library_books(
        self,
        filter_predicates: Dict[str, Any],
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Dict[str, Any]], int]:
        """Search library book documents using filter predicates."""
        try:
            collection = self._ensure_collection()

            total = collection.count_documents(filter_predicates, upper_bound=1000000)
            cursor = collection.find(filter_predicates, limit=skip + limit)
            library_books = []

            for index, doc in enumerate(cursor):
                if index < skip:
                    continue
                library_books.append(self._normalize_library_book_document(doc))
                if len(library_books) >= limit:
                    break

            logger.info(f"Search completed: found {total} documents, returning {len(library_books)}")
            return library_books, total

        except DataAPIException as e:
            logger.error(f"Failed to search library books: {str(e)}")
            return [], 0
        except Exception as e:
            logger.error(f"Unexpected error searching library books: {str(e)}")
            return [], 0

    async def semantic_search_library_books(
        self,
        query: str,
        filter_predicates: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Dict[str, Any]], int]:
        """Search library book documents semantically using AstraDB vectorize support."""
        try:
            collection = self._ensure_collection()
            predicates = filter_predicates or {}

            total = collection.count_documents(predicates, upper_bound=1000000)
            cursor = collection.find(
                filter=predicates,
                sort={"$vectorize": query},
                limit=skip + limit,
                include_similarity=True
            )
            library_books = []

            for index, doc in enumerate(cursor):
                if index < skip:
                    continue
                library_books.append(self._normalize_library_book_document(doc))
                if len(library_books) >= limit:
                    break

            logger.info(f"Semantic search completed: found {total} documents, returning {len(library_books)}")
            return library_books, total

        except DataAPIException as e:
            logger.error(f"Failed to perform semantic search for library books: {str(e)}")
            return [], 0
        except Exception as e:
            logger.error(f"Unexpected error performing semantic search for library books: {str(e)}")
            return [], 0

    async def lexical_search_library_books(
        self,
        keywords: str,
        filter_predicates: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Dict[str, Any]], int]:
        """Search library book documents using lexical keyword matching."""
        try:
            collection = self._ensure_collection()
            predicates = filter_predicates or {}

            total = collection.count_documents(predicates, upper_bound=1000000)
            
            # Use find_and_rerank with $hybrid in sort for lexical search
            cursor = collection.find_and_rerank(
                filter=predicates,
                sort={"$hybrid": keywords},  # Use $hybrid with query text for lexical
                limit=skip + limit,
                include_scores=True
            )
            
            library_books = []
            for index, reranked_result in enumerate(cursor):
                if index < skip:
                    continue
                # Extract the document from RerankedResult
                doc = reranked_result.document
                
                # Extract scores if available
                if hasattr(reranked_result, 'scores') and reranked_result.scores:
                    doc['scores'] = reranked_result.scores
                    logger.debug(f"Lexical search result {index}: scores={reranked_result.scores}")
                
                library_books.append(self._normalize_library_book_document(doc))
                if len(library_books) >= limit:
                    break

            logger.info(f"Lexical search completed: found {total} documents, returning {len(library_books)}")
            return library_books, total

        except DataAPIException as e:
            logger.error(f"Failed to perform lexical search for library books: {str(e)}")
            return [], 0
        except Exception as e:
            logger.error(f"Unexpected error performing lexical search for library books: {str(e)}")
            return [], 0

    async def hybrid_search_library_books(
        self,
        query: str,
        keywords: str,
        filter_predicates: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Dict[str, Any]], int]:
        """Search library book documents using hybrid vector + lexical search."""
        try:
            collection = self._ensure_collection()
            predicates = filter_predicates or {}

            total = collection.count_documents(predicates, upper_bound=1000000)
            
            # Use find_and_rerank with $hybrid containing both $vectorize and $lexical
            cursor = collection.find_and_rerank(
                filter=predicates,
                sort={
                    "$hybrid": {
                        "$vectorize": query,
                        "$lexical": keywords
                    }
                },
                limit=skip + limit,
                include_scores=True
            )
            library_books = []

            for index, reranked_result in enumerate(cursor):
                if index < skip:
                    continue
                # Extract the document from RerankedResult
                doc = reranked_result.document
                
                # Extract scores if available
                if hasattr(reranked_result, 'scores') and reranked_result.scores:
                    doc['scores'] = reranked_result.scores
                    logger.debug(f"Hybrid search result {index}: scores={reranked_result.scores}")
                
                library_books.append(self._normalize_library_book_document(doc))
                if len(library_books) >= limit:
                    break

            logger.info(f"Hybrid search completed: found {total} documents, returning {len(library_books)}")
            return library_books, total

        except DataAPIException as e:
            logger.error(f"Failed to perform hybrid search for library books: {str(e)}")
            return [], 0
        except Exception as e:
            logger.error(f"Unexpected error performing hybrid search for library books: {str(e)}")
            return [], 0


astra_connection_manager = AstraConnectionManager()
library_book_repository = LibraryBookRepository(collection=None)


def get_connected_database():
    """Connect to AstraDB and return the active database handle."""
    if not astra_connection_manager.is_connected():
        if not astra_connection_manager.connect():
            raise RuntimeError("Failed to connect to AstraDB")

    database = astra_connection_manager.database
    if database is None:
        raise RuntimeError("AstraDB database is not initialized after connection")

    return database
