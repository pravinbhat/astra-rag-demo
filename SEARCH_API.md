# Search API

Search endpoint for querying library books using filters, semantic, lexical, or hybrid search. For the web UI, see [UI.md](UI.md).

**Endpoint:** `POST /api/library-books/search`

## Search Modes

| Mode                       | Use Case                                        | Request Fields          | Example                                     |
| ----------------------------| -------------------------------------------------| ------------------------| ---------------------------------------------|
| **Filter Search**          | Query by metadata (author, genre, rating, etc.) | `filter` only           | Find all books by "John Anthony"            |
| **Semantic Search**        | Query by meaning/concepts                       | `query` only            | Find "books about resilience and survival"  |
| **Lexical Search**         | Query by keyword matching                       | `keywords` only         | Find books with "dystopian survival"        |
| **Hybrid Search**          | Combine vector + lexical search                 | `query` + `keywords`    | Find books semantically + keyword match     |
| **Semantic Filter Search** | Combine semantic + metadata constraints         | `filter` + `query`      | Find sci-fi books about "space exploration" |
| **Lexical Filter Search**  | Combine lexical + metadata constraints          | `filter` + `keywords`   | Find sci-fi books with "alien planet"       |
| **Hybrid Filter Search**   | Combine hybrid + metadata constraints           | `filter` + `query` + `keywords` | Find sci-fi books with semantic + lexical |

## Endpoint

**POST** `/api/library-books/search`

## Request Body

```json
{
  "filter": {
    // Optional filter predicates (see examples below)
  },
  "query": "Optional semantic search query",
  "keywords": "Optional lexical search keywords",
  "skip": 0,
  "limit": 100
}
```

### Parameters

- **filter** (optional): Dictionary containing filter predicates for searching documents
- **query** (optional): Semantic search query/prompt used for AstraDB vector search
- **keywords** (optional): Lexical search keywords for text matching
- **skip** (optional): Number of documents to skip for pagination (default: 0, min: 0)
- **limit** (optional): Maximum number of documents to return (default: 15, min: 1, max: 100)

## Filter Operators

### Equality
Match documents where a field equals a specific value.

```json
{
  "filter": {
    "author": "John Anthony"
  }
}
```

### Comparison Operators
- `$eq`: Equal to
- `$ne`: Not equal to
- `$gt`: Greater than
- `$gte`: Greater than or equal to
- `$lt`: Less than
- `$lte`: Less than or equal to

```json
{
  "filter": {
    "rating": {"$gte": 4.0},
    "number_of_pages": {"$lt": 500}
  }
}
```

### Array Operators
- `$in`: Match any value in array
- `$nin`: Match none of the values in array

```json
{
  "filter": {
    "genres": {"$in": ["Science Fiction", "Fantasy"]}
  }
}
```

### Multiple Conditions
Combine multiple filter conditions (implicit AND).

```json
{
  "filter": {
    "author": "John Anthony",
    "is_checked_out": false,
    "rating": {"$gte": 4.0}
  }
}
```

## Response

```json
{
  "library_books": [
    {
      "id": "doc-id-123",
      "title": "Book Title",
      "author": "Author Name",
      "number_of_pages": 350,
      "rating": 4.5,
      "publication_year": 2020,
      "summary": "Book summary...",
      "genres": ["Fiction", "Drama"],
      "metadata": { "isbn": "978-1-234567-89-0", "language": "English" },
      "is_checked_out": false,
      "$similarity": 0.91,
      "scores": {
        "$rerank": -2.5605469,
        "$vector": 0.6520678,
        "$rrf": 0.016393442
      }
    }
  ],
  "total": 1
}
```

### Response Fields

Search results include relevance scores based on the search type:

#### Score Fields by Search Type

| Search Type  | Score Fields                    | Description                                    |
| --------------| ---------------------------------| ------------------------------------------------|
| **Semantic** | `$similarity`                   | Vector similarity (0-1, higher is better)      |
| **Lexical**  | `scores.$rerank`, `scores.$rrf` | Rerank score (primary), RRF score (tiebreaker) |
| **Hybrid**   | `scores.$rerank`, `scores.$rrf` | Rerank + Reciprocal Rank Fusion scores         |

#### Field Descriptions

- **`$similarity`**: Semantic similarity score (0.0 to 1.0). Higher values indicate better matches.
- **`scores`**: Score breakdown for lexical and hybrid search results (only present for these search modes):
  - **`$rerank`**: Final relevance score after reranking. Lower (often negative) values indicate higher relevance. Primary sorting criterion.
  - **`$rrf`**: Reciprocal Rank Fusion score combining multiple ranking signals. Lower values indicate better results. Used as a tiebreaker when `$rerank` scores are equal.
  - **`$vector`**: Vector similarity score (0.0 to 1.0) for lexical/hybrid searches.

#### UI Display

The UI shows simplified scores for clarity:
- **Semantic**: Vector similarity as percentage (e.g., "🎯 85% match")
- **Lexical**: Rerank and RRF scores
- **Hybrid**: Rerank and RRF scores

## Example Requests

### 1. Filter Search by Author

```bash
curl -X POST "http://localhost:8000/api/library-books/search" \
  -H "Content-Type: application/json" \
  -d '{
    "filter": {"author": "John Anthony"},
    "skip": 0,
    "limit": 10
  }'
```

### 2. Semantic Search by Query

```bash
curl -X POST "http://localhost:8000/api/library-books/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "books about resilience and survival",
    "skip": 0,
    "limit": 10
  }'
```

### 3. Lexical Search by Keywords

```bash
curl -X POST "http://localhost:8000/api/library-books/search" \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": "dystopian survival",
    "skip": 0,
    "limit": 10
  }'
```

### 4. Hybrid Search (Vector + Lexical)

```bash
curl -X POST "http://localhost:8000/api/library-books/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "books about resilience and hope",
    "keywords": "dystopian survival",
    "skip": 0,
    "limit": 10
  }'
```

### 5. Hybrid Search with Filter

```bash
curl -X POST "http://localhost:8000/api/library-books/search" \
  -H "Content-Type: application/json" \
  -d '{
    "filter": {
      "genres": {"$in": ["Science Fiction", "Fantasy"]},
      "rating": {"$gte": 4.0},
      "is_checked_out": false
    },
    "query": "space exploration adventure",
    "keywords": "alien planet discovery",
    "skip": 0,
    "limit": 20
  }'
```

## Error Responses

### 500 Internal Server Error
```json
{
  "detail": "Search failed: <error message>"
}
```

## Notes

- All search operations are performed server-side by AstraDB for optimal performance
- Pagination is supported through `skip` and `limit` parameters
- The `total` field in the response indicates the total number of matching documents
- Empty filter `{}` with no query or keywords will return all documents (subject to pagination limits)
