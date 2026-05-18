/**
 * Book Details Modal Component
 * Displays full book information in a modal when a book card is clicked
 */

let currentModal = null;

// Helper functions for unified score handling
function getVectorSimilarity(book) {
    if (book.$similarity !== undefined && book.$similarity !== null) {
        return book.$similarity;
    }
    if (book.scores && book.scores.$vector !== undefined && book.scores.$vector !== null) {
        return book.scores.$vector;
    }
    return null;
}

function formatSimilarityPercent(similarity) {
    if (similarity === null || similarity === undefined) return null;
    return Math.round(similarity * 100);
}

function renderStarRating(rating) {
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 >= 0.5;
    const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);
    
    let stars = '★'.repeat(fullStars);
    if (hasHalfStar) stars += '⯨';
    stars += '☆'.repeat(emptyStars);
    
    return `<span class="book-rating-large" title="${rating.toFixed(1)} out of 5">${stars} ${rating.toFixed(1)}</span>`;
}

function renderGenres(genres) {
    if (!genres || genres.length === 0) return '<p class="detail-empty">No genres specified</p>';
    
    return genres
        .map(genre => `<span class="genre-badge-large">${genre}</span>`)
        .join('');
}

function renderCheckoutStatus(book) {
    if (book.is_checked_out) {
        const dueDate = book.due_date ? new Date(book.due_date).toLocaleDateString() : 'Unknown';
        const borrower = book.borrower || 'Unknown';
        return `
            <div class="checkout-info checked-out">
                <div class="checkout-status">
                    <span class="status-icon">⊗</span>
                    <span class="status-text">Checked Out</span>
                </div>
                <div class="checkout-details">
                    <p><strong>Borrower:</strong> ${borrower}</p>
                    <p><strong>Due Date:</strong> ${dueDate}</p>
                </div>
            </div>
        `;
    }
    return `
        <div class="checkout-info available">
            <span class="status-icon">✓</span>
            <span class="status-text">Available</span>
        </div>
    `;
}

function renderSearchRelevance(book) {
    const similarity = getVectorSimilarity(book);
    const scores = book.scores;
    
    if (!similarity && !scores) return '';
    
    let html = '<div class="detail-section"><h3>Search Relevance</h3>';
    
    // Semantic search: Show vector similarity with progress bar
    if (similarity !== null && !scores) {
        const percent = formatSimilarityPercent(similarity);
        html += `
            <div class="score-detail">
                <div class="score-label">Vector Similarity</div>
                <div class="similarity-bar">
                    <div class="similarity-fill" style="width: ${percent}%"></div>
                </div>
                <p class="similarity-text">${percent}% match</p>
            </div>
        `;
    }
    
    // Lexical or Hybrid search: Show rerank score
    if (scores && scores.$rerank !== undefined && scores.$rerank !== null) {
        html += `
            <div class="score-detail">
                <div class="score-label">Rerank Score</div>
                <div class="score-value" title="Final relevance adjustment">${scores.$rerank.toFixed(4)}</div>
                <p class="score-description">Final relevance adjustment (lower is better)</p>
            </div>
        `;
    }
    
    // Hybrid search only: Show RRF score
    if (scores && scores.$rrf !== undefined && scores.$rrf !== null) {
        html += `
            <div class="score-detail">
                <div class="score-label">RRF Score <span class="info-icon" title="Reciprocal Rank Fusion combines multiple ranking signals">ⓘ</span></div>
                <div class="score-value">${scores.$rrf.toFixed(6)}</div>
                <p class="score-description">Reciprocal Rank Fusion score (lower is better)</p>
            </div>
        `;
    }
    
    html += '</div>';
    return html;
}

function createBookDetailsModal(book) {
    const modal = document.createElement('div');
    modal.className = 'book-details-modal';
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-labelledby', 'book-details-title');
    modal.setAttribute('aria-modal', 'true');
    
    modal.innerHTML = `
        <div class="book-details-backdrop"></div>
        <div class="book-details-container">
            <div class="book-details-header">
                <h2 id="book-details-title" class="book-details-title">${book.title}</h2>
                <button class="book-details-close" aria-label="Close book details">
                    <span>✕</span>
                </button>
            </div>
            
            <div class="book-details-content">
                <div class="book-details-main">
                    <div class="detail-section">
                        <h3>Author</h3>
                        <p class="detail-author">${book.author}</p>
                    </div>
                    
                    <div class="detail-section">
                        <h3>Summary</h3>
                        <p class="detail-summary">${book.summary || 'No summary available'}</p>
                    </div>
                    
                    <div class="detail-section">
                        <h3>Genres</h3>
                        <div class="detail-genres">
                            ${renderGenres(book.genres)}
                        </div>
                    </div>
                </div>
                
                <div class="book-details-sidebar">
                    <div class="detail-section">
                        <h3>Rating</h3>
                        ${renderStarRating(book.rating)}
                    </div>
                    
                    <div class="detail-section">
                        <h3>Publication Info</h3>
                        <div class="detail-info-grid">
                            <div class="info-item">
                                <span class="info-label">Year:</span>
                                <span class="info-value">${book.publication_year}</span>
                            </div>
                            <div class="info-item">
                                <span class="info-label">Pages:</span>
                                <span class="info-value">${book.number_of_pages}</span>
                            </div>
                            ${book.isbn ? `
                                <div class="info-item">
                                    <span class="info-label">ISBN:</span>
                                    <span class="info-value">${book.isbn}</span>
                                </div>
                            ` : ''}
                            ${book.language ? `
                                <div class="info-item">
                                    <span class="info-label">Language:</span>
                                    <span class="info-value">${book.language}</span>
                                </div>
                            ` : ''}
                            ${book.edition ? `
                                <div class="info-item">
                                    <span class="info-label">Edition:</span>
                                    <span class="info-value">${book.edition}</span>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                    
                    <div class="detail-section">
                        <h3>Availability</h3>
                        ${renderCheckoutStatus(book)}
                    </div>
                    
                    ${renderSearchRelevance(book)}
                    
                    ${book._id ? `
                        <div class="detail-section">
                            <h3>Book ID</h3>
                            <p class="detail-id">${book._id}</p>
                        </div>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
    
    return modal;
}

export function showBookDetails(book) {
    // Remove existing modal if any
    closeBookDetails();
    
    // Create and show new modal
    const modal = createBookDetailsModal(book);
    document.body.appendChild(modal);
    currentModal = modal;
    
    // Prevent body scroll
    document.body.style.overflow = 'hidden';
    
    // Setup close handlers
    const closeBtn = modal.querySelector('.book-details-close');
    const backdrop = modal.querySelector('.book-details-backdrop');
    
    closeBtn.addEventListener('click', closeBookDetails);
    backdrop.addEventListener('click', closeBookDetails);
    
    // Close on Escape key
    const handleEscape = (e) => {
        if (e.key === 'Escape') {
            closeBookDetails();
            document.removeEventListener('keydown', handleEscape);
        }
    };
    document.addEventListener('keydown', handleEscape);
    
    // Animate in
    requestAnimationFrame(() => {
        modal.classList.add('active');
    });
    
    // Focus the close button for accessibility
    closeBtn.focus();
}

export function closeBookDetails() {
    if (!currentModal) return;
    
    currentModal.classList.remove('active');
    
    setTimeout(() => {
        if (currentModal && currentModal.parentNode) {
            currentModal.parentNode.removeChild(currentModal);
        }
        currentModal = null;
        document.body.style.overflow = '';
    }, 300);
}

export function init() {
    // This function can be called to initialize any global listeners if needed
    console.log('Book Details Modal component initialized');
}

// Made with Bob
