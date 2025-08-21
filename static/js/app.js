// Food Wastage Management System - Main JavaScript

// Global variables
let currentUser = null;
let refreshInterval = null;

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    startAutoRefresh();
});

// Application initialization
function initializeApp() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Set up navbar active state
    setActiveNavItem();
    
    // Initialize charts if on analytics page
    if (document.getElementById('foodCategoriesChart')) {
        initializeCharts();
    }
    
    // Initialize real-time updates
    if (document.querySelector('.dashboard-stats')) {
        updateDashboardStats();
    }
}

// Set up event listeners
function setupEventListeners() {
    // Search functionality
    const searchInputs = document.querySelectorAll('.search-input');
    searchInputs.forEach(input => {
        input.addEventListener('input', debounce(handleSearch, 300));
    });
    
    // Filter functionality
    const filterSelects = document.querySelectorAll('.filter-select');
    filterSelects.forEach(select => {
        select.addEventListener('change', handleFilter);
    });
    
    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', handleFormSubmission);
    });
    
    // Dynamic form fields
    setupDynamicFields();
    
    // Keyboard shortcuts
    document.addEventListener('keydown', handleKeyboardShortcuts);
}

// Set active navigation item
function setActiveNavItem() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href && currentPath.includes(href) && href !== '/') {
            link.classList.add('active');
            link.parentElement.classList.add('active');
        } else if (href === '/' && currentPath === '/') {
            link.classList.add('active');
            link.parentElement.classList.add('active');
        } else {
            link.classList.remove('active');
            link.parentElement.classList.remove('active');
        }
    });
}

// Search functionality
function handleSearch(event) {
    const searchTerm = event.target.value.toLowerCase();
    const searchableItems = document.querySelectorAll('.searchable-item');
    
    searchableItems.forEach(item => {
        const searchText = item.textContent.toLowerCase();
        if (searchText.includes(searchTerm)) {
            item.style.display = '';
            item.classList.remove('d-none');
        } else {
            item.style.display = 'none';
            item.classList.add('d-none');
        }
    });
    
    // Update results count
    const visibleItems = document.querySelectorAll('.searchable-item:not(.d-none)');
    const resultsCount = document.querySelector('.results-count');
    if (resultsCount) {
        resultsCount.textContent = `${visibleItems.length} results found`;
    }
}

// Filter functionality
function handleFilter(event) {
    const filterValue = event.target.value;
    const filterType = event.target.dataset.filterType;
    const filterableItems = document.querySelectorAll(`[data-${filterType}]`);
    
    filterableItems.forEach(item => {
        const itemValue = item.dataset[filterType];
        if (!filterValue || itemValue === filterValue) {
            item.style.display = '';
            item.classList.remove('d-none');
        } else {
            item.style.display = 'none';
            item.classList.add('d-none');
        }
    });
}

// Form submission handling
function handleFormSubmission(event) {
    event.preventDefault();
    event.stopPropagation();
    
    const form = event.target;
    
    if (form.checkValidity()) {
        showLoading();
        submitFormData(form);
    }
    
    form.classList.add('was-validated');
}

// Submit form data via AJAX
function submitFormData(form) {
    const formData = new FormData(form);
    const url = form.action || window.location.href;
    
    fetch(url, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        handleResponse(data);
    })
    .catch(error => {
        hideLoading();
        console.error('Error:', error);
        showAlert('danger', 'An error occurred. Please try again.');
    });
}

// Handle server response
function handleResponse(data) {
    if (data.success) {
        showAlert('success', data.message || 'Operation completed successfully!');
        if (data.redirect) {
            setTimeout(() => {
                window.location.href = data.redirect;
            }, 2000);
        } else if (data.reload) {
            setTimeout(() => {
                window.location.reload();
            }, 2000);
        }
    } else {
        showAlert('danger', data.message || 'Operation failed. Please try again.');
    }
}

// Dynamic form fields
function setupDynamicFields() {
    // Phone number formatting
    const phoneInputs = document.querySelectorAll('input[type="tel"]');
    phoneInputs.forEach(input => {
        input.addEventListener('input', formatPhoneNumber);
    });
    
    // Date restrictions
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(input => {
        if (input.hasAttribute('data-min-today')) {
            const today = new Date().toISOString().split('T')[0];
            input.min = today;
        }
    });
    
    // Auto-resize textareas
    const textareas = document.querySelectorAll('textarea[data-auto-resize]');
    textareas.forEach(textarea => {
        textarea.addEventListener('input', autoResizeTextarea);
    });
}

// Format phone number
function formatPhoneNumber(event) {
    let value = event.target.value.replace(/\D/g, '');
    if (value.length >= 10) {
        value = value.replace(/(\d{3})(\d{3})(\d{4})/, '($1) $2-$3');
    } else if (value.length >= 6) {
        value = value.replace(/(\d{3})(\d{3})/, '($1) $2-');
    } else if (value.length >= 3) {
        value = value.replace(/(\d{3})/, '($1) ');
    }
    event.target.value = value;
}

// Auto-resize textarea
function autoResizeTextarea(event) {
    const textarea = event.target;
    textarea.style.height = 'auto';
    textarea.style.height = (textarea.scrollHeight) + 'px';
}

// Keyboard shortcuts
function handleKeyboardShortcuts(event) {
    // Ctrl/Cmd + S to save forms
    if ((event.ctrlKey || event.metaKey) && event.key === 's') {
        event.preventDefault();
        const form = document.querySelector('form');
        if (form) {
            form.requestSubmit();
        }
    }
    
    // Escape to close modals
    if (event.key === 'Escape') {
        const openModal = document.querySelector('.modal.show');
        if (openModal) {
            const modal = bootstrap.Modal.getInstance(openModal);
            modal.hide();
        }
    }
    
    // Ctrl/Cmd + K for search
    if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
        event.preventDefault();
        const searchInput = document.querySelector('.search-input');
        if (searchInput) {
            searchInput.focus();
        }
    }
}

// Update dashboard statistics
function updateDashboardStats() {
    fetch('/api/dashboard-stats', {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateStatsDisplay(data.stats);
        }
    })
    .catch(error => {
        console.error('Error updating stats:', error);
    });
}

// Update statistics display
function updateStatsDisplay(stats) {
    Object.keys(stats).forEach(key => {
        const element = document.querySelector(`[data-stat="${key}"]`);
        if (element) {
            animateNumber(element, parseInt(element.textContent) || 0, stats[key]);
        }
    });
}

// Animate number changes
function animateNumber(element, start, end) {
    const duration = 1000;
    const increment = (end - start) / (duration / 16);
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
            current = end;
            clearInterval(timer);
        }
        element.textContent = Math.round(current);
    }, 16);
}

// Auto-refresh functionality
function startAutoRefresh() {
    // Refresh dashboard every 30 seconds
    if (document.querySelector('.dashboard-stats')) {
        refreshInterval = setInterval(updateDashboardStats, 30000);
    }
    
    // Refresh urgent alerts every 60 seconds
    if (document.querySelector('.urgent-alerts')) {
        setInterval(updateUrgentAlerts, 60000);
    }
}

// Update urgent alerts
function updateUrgentAlerts() {
    fetch('/api/urgent-alerts', {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateAlertsDisplay(data.alerts);
        }
    })
    .catch(error => {
        console.error('Error updating alerts:', error);
    });
}

// Update alerts display
function updateAlertsDisplay(alerts) {
    const alertsContainer = document.querySelector('.urgent-alerts');
    if (alertsContainer) {
        alertsContainer.innerHTML = '';
        alerts.forEach(alert => {
            const alertElement = createAlertElement(alert);
            alertsContainer.appendChild(alertElement);
        });
    }
}

// Create alert element
function createAlertElement(alert) {
    const div = document.createElement('div');
    div.className = 'alert alert-warning urgent-alert';
    div.innerHTML = `
        <i class="fas fa-exclamation-triangle"></i>
        <strong>${alert.title}</strong> - ${alert.message}
        <span class="badge bg-danger ms-2">${alert.urgency}</span>
    `;
    return div;
}

// Initialize charts for analytics page
function initializeCharts() {
    // This function will be called if Chart.js is available
    if (typeof Chart !== 'undefined') {
        createFoodCategoriesChart();
        createProviderTypesChart();
        createMonthlyTrendChart();
        createWastageReductionChart();
    }
}

// Utility functions
function showLoading() {
    const spinner = document.createElement('div');
    spinner.className = 'spinner-overlay';
    spinner.innerHTML = `
        <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
    `;
    document.body.appendChild(spinner);
}

function hideLoading() {
    const spinner = document.querySelector('.spinner-overlay');
    if (spinner) {
        spinner.remove();
    }
}

function showAlert(type, message, duration = 5000) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 1050; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto-dismiss
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, duration);
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function formatTime(timeString) {
    const time = new Date(`2000-01-01T${timeString}`);
    return time.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

function calculateDaysUntilExpiry(expiryDate) {
    const today = new Date();
    const expiry = new Date(expiryDate);
    const diffTime = expiry - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
}

// Export functions for global use
window.FoodWastageApp = {
    showAlert,
    showLoading,
    hideLoading,
    formatDate,
    formatTime,
    calculateDaysUntilExpiry,
    updateDashboardStats,
    updateUrgentAlerts
};

// Service Worker registration for offline support
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/js/sw.js')
            .then(registration => {
                console.log('SW registered: ', registration);
            })
            .catch(registrationError => {
                console.log('SW registration failed: ', registrationError);
            });
    });
}
