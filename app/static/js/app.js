import * as API from './api.js';
import { FilterBuilder } from './components/filterBuilder.js';
import * as SearchResults from './components/searchResults.js';
import * as ComparisonView from './components/comparisonView.js';
import * as AddBookForm from './components/addBookForm.js';
import * as BookDetailsModal from './components/bookDetailsModal.js';

const state = {
    currentMode: 'filter',
    filterBuilders: {},
    lastSearchParams: null
};

function init() {
    console.log('Initializing Astra Search Demo...');
    
    // Initialize filter builders for each mode
    state.filterBuilders = {
        filter: new FilterBuilder('filter-builder'),
        semantic: new FilterBuilder('semantic-filter-builder'),
        lexical: new FilterBuilder('lexical-filter-builder'),
        hybrid: new FilterBuilder('hybrid-filter-builder')
    };
    
    // Initialize add book form
    AddBookForm.init();
    
    // Initialize book details modal
    BookDetailsModal.init();
    
    // Setup event listeners
    setupModeTabListeners();
    setupSearchButtonListeners();
    setupClearButtonListeners();
    setupBookAddedListener();
    
    // Set initial mode
    switchMode('filter');
    
    console.log('Application initialized successfully');
}

function setupModeTabListeners() {
    const modeTabs = document.querySelectorAll('.mode-tab');
    
    modeTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const mode = tab.dataset.mode;
            switchMode(mode);
        });
    });
}

function switchMode(mode) {
    state.currentMode = mode;
    
    // Update tab states
    document.querySelectorAll('.mode-tab').forEach(tab => {
        if (tab.dataset.mode === mode) {
            tab.classList.add('active');
            tab.setAttribute('aria-selected', 'true');
        } else {
            tab.classList.remove('active');
            tab.setAttribute('aria-selected', 'false');
        }
    });
    
    // Update panel states
    document.querySelectorAll('.search-panel').forEach(panel => {
        if (panel.id === `${mode}-panel`) {
            panel.classList.add('active');
        } else {
            panel.classList.remove('active');
        }
    });
    
    // Clear results when switching modes (except comparison)
    if (mode !== 'comparison') {
        SearchResults.clearResults();
    }
}

function setupSearchButtonListeners() {
    document.getElementById('filter-search-btn')?.addEventListener('click', () => {
        handleFilterSearch();
    });
    
    document.getElementById('semantic-search-btn')?.addEventListener('click', () => {
        handleSemanticSearch();
    });
    
    document.getElementById('lexical-search-btn')?.addEventListener('click', () => {
        handleLexicalSearch();
    });
    
    document.getElementById('hybrid-search-btn')?.addEventListener('click', () => {
        handleHybridSearch();
    });
    
    document.getElementById('comparison-search-btn')?.addEventListener('click', () => {
        handleComparisonSearch();
    });
}

function setupClearButtonListeners() {
    document.getElementById('filter-clear-btn')?.addEventListener('click', () => {
        state.filterBuilders.filter.clearFilters();
        SearchResults.clearResults();
    });
    
    document.getElementById('semantic-clear-btn')?.addEventListener('click', () => {
        document.getElementById('semantic-query').value = '';
        state.filterBuilders.semantic.clearFilters();
        SearchResults.clearResults();
    });
    
    document.getElementById('lexical-clear-btn')?.addEventListener('click', () => {
        document.getElementById('lexical-keywords').value = '';
        state.filterBuilders.lexical.clearFilters();
        SearchResults.clearResults();
    });
    
    document.getElementById('hybrid-clear-btn')?.addEventListener('click', () => {
        document.getElementById('hybrid-query').value = '';
        document.getElementById('hybrid-keywords').value = '';
        state.filterBuilders.hybrid.clearFilters();
        SearchResults.clearResults();
    });
    
    document.getElementById('comparison-clear-btn')?.addEventListener('click', () => {
        document.getElementById('comparison-query').value = '';
        document.getElementById('comparison-keywords').value = '';
        ComparisonView.clearComparisonResults();
        SearchResults.showEmptyState();
    });
}

async function handleFilterSearch() {
    const filterBuilder = state.filterBuilders.filter;
    const filter = filterBuilder.getFilterPredicates();
    const limit = parseInt(document.getElementById('filter-results-limit')?.value) || 15;
    
    if (!filterBuilder.hasFilters()) {
        alert('Please add at least one filter');
        return;
    }
    
    try {
        SearchResults.showLoading();
        SearchResults.showResults();
        
        const result = await API.filterSearch(filter, 0, limit);
        
        const resultsGrid = document.getElementById('results-grid');
        SearchResults.renderResults(
            resultsGrid,
            result.library_books,
            result.total,
            result.responseTime,
            BookDetailsModal.showBookDetails
        );
        
        SearchResults.hideLoading();
        SearchResults.scrollToResults();
        
        state.lastSearchParams = { mode: 'filter', filter, limit };
    } catch (error) {
        SearchResults.hideLoading();
        SearchResults.showError(error.message || 'Search failed. Please try again.');
        console.error('Filter search error:', error);
    }
}

async function handleSemanticSearch() {
    const query = document.getElementById('semantic-query')?.value.trim();
    const filterBuilder = state.filterBuilders.semantic;
    const filter = filterBuilder.hasFilters() ? filterBuilder.getFilterPredicates() : null;
    const limit = parseInt(document.getElementById('semantic-results-limit')?.value) || 15;
    
    if (!query) {
        alert('Please enter a search query');
        return;
    }
    
    try {
        SearchResults.showLoading();
        SearchResults.showResults();
        
        const result = await API.semanticSearch(query, filter, 0, limit);
        
        const resultsGrid = document.getElementById('results-grid');
        SearchResults.renderResults(
            resultsGrid,
            result.library_books,
            result.total,
            result.responseTime,
            BookDetailsModal.showBookDetails
        );
        
        SearchResults.hideLoading();
        SearchResults.scrollToResults();
        
        state.lastSearchParams = { mode: 'semantic', query, filter, limit };
    } catch (error) {
        SearchResults.hideLoading();
        SearchResults.showError(error.message || 'Search failed. Please try again.');
        console.error('Semantic search error:', error);
    }
}

async function handleLexicalSearch() {
    const keywords = document.getElementById('lexical-keywords')?.value.trim();
    const filterBuilder = state.filterBuilders.lexical;
    const filter = filterBuilder.hasFilters() ? filterBuilder.getFilterPredicates() : null;
    const limit = parseInt(document.getElementById('lexical-results-limit')?.value) || 15;
    
    if (!keywords) {
        alert('Please enter keywords');
        return;
    }
    
    try {
        SearchResults.showLoading();
        SearchResults.showResults();
        
        const result = await API.lexicalSearch(keywords, filter, 0, limit);
        
        const resultsGrid = document.getElementById('results-grid');
        SearchResults.renderResults(
            resultsGrid,
            result.library_books,
            result.total,
            result.responseTime,
            BookDetailsModal.showBookDetails
        );
        
        SearchResults.hideLoading();
        SearchResults.scrollToResults();
        
        state.lastSearchParams = { mode: 'lexical', keywords, filter, limit };
    } catch (error) {
        SearchResults.hideLoading();
        SearchResults.showError(error.message || 'Search failed. Please try again.');
        console.error('Lexical search error:', error);
    }
}

async function handleHybridSearch() {
    const query = document.getElementById('hybrid-query')?.value.trim();
    const keywords = document.getElementById('hybrid-keywords')?.value.trim();
    const filterBuilder = state.filterBuilders.hybrid;
    const filter = filterBuilder.hasFilters() ? filterBuilder.getFilterPredicates() : null;
    const limit = parseInt(document.getElementById('hybrid-results-limit')?.value) || 15;
    
    if (!query || !keywords) {
        alert('Please enter both a query and keywords for hybrid search');
        return;
    }
    
    try {
        SearchResults.showLoading();
        SearchResults.showResults();
        
        const result = await API.hybridSearch(query, keywords, filter, 0, limit);
        
        const resultsGrid = document.getElementById('results-grid');
        SearchResults.renderResults(
            resultsGrid,
            result.library_books,
            result.total,
            result.responseTime,
            BookDetailsModal.showBookDetails
        );
        
        SearchResults.hideLoading();
        SearchResults.scrollToResults();
        
        state.lastSearchParams = { mode: 'hybrid', query, keywords, filter, limit };
    } catch (error) {
        SearchResults.hideLoading();
        SearchResults.showError(error.message || 'Search failed. Please try again.');
        console.error('Hybrid search error:', error);
    }
}

async function handleComparisonSearch() {
    const query = document.getElementById('comparison-query')?.value.trim();
    const keywords = document.getElementById('comparison-keywords')?.value.trim();
    const limit = parseInt(document.getElementById('comparison-results-limit')?.value) || 15;
    
    if (!query && !keywords) {
        alert('Please enter at least a query or keywords');
        return;
    }
    
    try {
        SearchResults.showLoading();
        SearchResults.showComparisonResults();
        
        const results = await API.comparisonSearch(query, keywords, null, limit);
        
        ComparisonView.renderComparisonResults(results, BookDetailsModal.showBookDetails);
        
        const summary = ComparisonView.generateComparisonSummary(results);
        ComparisonView.displayComparisonSummary(summary);
        
        SearchResults.hideLoading();
        SearchResults.scrollToResults();
        
        state.lastSearchParams = { mode: 'comparison', query, keywords, limit };
    } catch (error) {
        SearchResults.hideLoading();
        SearchResults.showError(error.message || 'Comparison search failed. Please try again.');
        console.error('Comparison search error:', error);
    }
}

function setupBookAddedListener() {
    // Listen for book added event to optionally refresh results
    window.addEventListener('bookAdded', (event) => {
        console.log('Book added:', event.detail);
        
        // Show a success notification
        const notification = document.createElement('div');
        notification.className = 'notification success';
        notification.textContent = `✓ "${event.detail.title}" has been added to the library`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #10b981;
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 0.5rem;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            z-index: 9999;
            animation: slideIn 0.3s ease-out;
        `;
        
        document.body.appendChild(notification);
        
        // Remove notification after 3 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    });
}

function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            
            // Focus the appropriate input based on current mode
            const inputs = {
                filter: null, // Filter mode doesn't have a single input
                semantic: document.getElementById('semantic-query'),
                lexical: document.getElementById('lexical-keywords'),
                hybrid: document.getElementById('hybrid-query'),
                comparison: document.getElementById('comparison-query')
            };
            
            const input = inputs[state.currentMode];
            if (input) {
                input.focus();
            }
        }
        
        if (e.key === 'Escape') {
            SearchResults.clearResults();
        }
    });
}

async function checkAPIHealth() {
    try {
        const health = await API.healthCheck();
        console.log('API Health:', health);
    } catch (error) {
        console.warn('API health check failed:', error);
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        init();
        setupKeyboardShortcuts();
        checkAPIHealth();
    });
} else {
    init();
    setupKeyboardShortcuts();
    checkAPIHealth();
}

window.AstraSearchDemo = {
    state,
    API,
    SearchResults,
    ComparisonView,
    AddBookForm,
    BookDetailsModal
};
