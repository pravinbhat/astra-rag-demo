"""
Pydantic models for request/response validation.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class LibraryBookBase(BaseModel):
    """Base schema for a library book document."""
    title: str = Field(..., description="Book title", min_length=1, max_length=500)
    author: str = Field(..., description="Book author", min_length=1, max_length=300)
    number_of_pages: int = Field(..., description="Number of pages in the book", gt=0)
    rating: float = Field(..., description="Book rating", ge=0, le=5)
    publication_year: int = Field(..., description="Year the book was published", ge=1000, le=9999)
    summary: str = Field(..., description="Book summary", min_length=1)
    genres: List[str] = Field(..., description="List of book genres")
    metadata: Optional[dict] = Field(None, description="Book metadata (isbn, language, edition)")
    is_checked_out: bool = Field(..., description="Whether the book is currently checked out")
    borrower: Optional[str] = Field(None, description="Name of the borrower if checked out")
    due_date: Optional[str] = Field(None, description="Due date if checked out")
    vectorize_text: Optional[str] = Field(
        None,
        alias="$vectorize",
        description="Text used by AstraDB to generate embeddings (summary and genres)",
        min_length=1
    )

    model_config = ConfigDict(populate_by_name=True)


class LibraryBookCreate(LibraryBookBase):
    """Schema for creating a library book document."""
    pass


class LibraryBookUpdate(BaseModel):
    """Schema for updating a library book document. All fields are optional."""
    title: Optional[str] = Field(None, description="Book title", min_length=1, max_length=500)
    author: Optional[str] = Field(None, description="Book author", min_length=1, max_length=300)
    number_of_pages: Optional[int] = Field(None, description="Number of pages in the book", gt=0)
    rating: Optional[float] = Field(None, description="Book rating", ge=0, le=5)
    publication_year: Optional[int] = Field(None, description="Year the book was published", ge=1000, le=9999)
    summary: Optional[str] = Field(None, description="Book summary", min_length=1)
    genres: Optional[List[str]] = Field(None, description="List of book genres")
    metadata: Optional[dict] = Field(None, description="Book metadata (isbn, language, edition)")
    is_checked_out: Optional[bool] = Field(None, description="Whether the book is currently checked out")
    borrower: Optional[str] = Field(None, description="Name of the borrower if checked out")
    due_date: Optional[str] = Field(None, description="Due date if checked out")
    vectorize_text: Optional[str] = Field(
        None,
        alias="$vectorize",
        description="Text used by AstraDB to generate embeddings (summary and genres)",
        min_length=1
    )

    model_config = ConfigDict(populate_by_name=True)


class LibraryBookResponse(LibraryBookBase):
    """Schema for library book response."""
    id: str = Field(..., description="Unique identifier for the library book")
    similarity: Optional[float] = Field(
        None,
        alias="$similarity",
        description="Similarity score returned by AstraDB for semantic search results"
    )
    scores: Optional[Dict[str, Any]] = Field(
        None,
        description="Score breakdown for lexical and hybrid search results (includes $rerank, $vector, $rrf)"
    )
    embedding: Optional[list[float]] = Field(None, description="Optional embedding payload if stored in the document")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra="ignore")


class LibraryBookListResponse(BaseModel):
    """Schema for list of library book documents."""
    library_books: List[LibraryBookResponse] = Field(..., description="List of library book documents")
    total: int = Field(..., description="Total number of library book documents")


class HealthResponse(BaseModel):
    """Schema for health check response."""
    status: str = Field(..., description="Health status")
    app_name: str = Field(..., description="Application name")
    version: str = Field(..., description="Application version")
    astra_db_connected: bool = Field(..., description="AstraDB connection status")


class LibraryBookSearchRequest(BaseModel):
    """Schema for filter, semantic, lexical, and hybrid search requests."""
    filter: Dict[str, Any] = Field(
        default_factory=dict,
        description="Filter predicates for searching documents (e.g., {'author': 'John Anthony', 'rating': {'$gte': 4.0}})"
    )
    query: Optional[str] = Field(
        None,
        description="Semantic search query used for AstraDB vector search"
    )
    keywords: Optional[str] = Field(
        None,
        description="Lexical search keywords for text matching"
    )
    skip: int = Field(0, ge=0, description="Number of documents to skip")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of documents to return")
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "filter": {"author": "John Anthony"},
                    "skip": 0,
                    "limit": 10
                },
                {
                    "query": "books about resilience and survival",
                    "skip": 0,
                    "limit": 10
                },
                {
                    "keywords": "dystopian survival",
                    "skip": 0,
                    "limit": 10
                },
                {
                    "query": "books about resilience",
                    "keywords": "dystopian survival",
                    "skip": 0,
                    "limit": 10
                },
                {
                    "filter": {"genres": {"$in": ["Science Fiction", "Fantasy"]}},
                    "query": "books about space exploration and adventure",
                    "skip": 0,
                    "limit": 20
                }
            ]
        }
    )


class ErrorResponse(BaseModel):
    """Schema for error response."""
    detail: str = Field(..., description="Error message")

# Made with Bob
