// Main JavaScript file for IITB SCAN - Patient Data Collection System

// ===== Auto-Hide Flash Messages =====
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.style.opacity = '0';
            alert.style.transform = 'translateX(100%)';
            setTimeout(function() {
                alert.remove();
            }, 300);
        }, 5000);
    });
});

// ===== Modal Management =====
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal-overlay')) {
        e.target.classList.remove('open');
    }
});

// Close modal button handler
document.querySelectorAll('.modal-close-btn').forEach(function(btn) {
    btn.addEventListener('click', function() {
        this.closest('.modal-overlay').classList.remove('open');
    });
});

// ===== Form Enhancements =====

// Multi-step form progress
function updateFormProgress() {
    const form = document.querySelector('.multi-step-form');
    if (!form) return;
    
    const totalFields = form.querySelectorAll('.form-group').length;
    const filledFields = form.querySelectorAll('.form-group input:valid, .form-group select:not(:has(option:first-child:checked))').length;
    
    const progressPercent = totalFields > 0 ? (filledFields / totalFields) * 100 : 0;
    const progressBar = document.querySelector('.progress-bar-fill');
    
    if (progressBar) {
        progressBar.style.width = progressPercent + '%';
    }
    
    const progressText = document.querySelector('.progress-text');
    if (progressText) {
        progressText.textContent = Math.round(progressPercent) + '%';
    }
}

// Auto-save form drafts to localStorage
function autoSaveDraft() {
    const form = document.querySelector('.multi-step-form');
    if (!form) return;
    
    const formData = new FormData(form);
    const formDataObj = Object.fromEntries(formData);
    const draftKey = 'form_draft_' + (form.dataset.formId || 'unknown');
    
    localStorage.setItem(draftKey, JSON.stringify(formDataObj));
    localStorage.setItem(draftKey + '_timestamp', new Date().toISOString());
}

// Restore form draft from localStorage
function restoreDraft() {
    const form = document.querySelector('.multi-step-form');
    if (!form) return;
    
    const draftKey = 'form_draft_' + (form.dataset.formId || 'unknown');
    const savedDraft = localStorage.getItem(draftKey);
    
    if (savedDraft) {
        const formData = JSON.parse(savedDraft);
        Object.keys(formData).forEach(key => {
            const field = form.querySelector('[name="' + key + '"]');
            if (field) {
                if (field.type === 'checkbox' || field.type === 'radio') {
                    document.querySelector('[name="' + key + '"][value="' + formData[key] + '"]').checked = true;
                } else {
                    field.value = formData[key];
                }
            }
        });
        
        const timestamp = localStorage.getItem(draftKey + '_timestamp');
        if (timestamp) {
            const draftTime = new Date(timestamp);
            console.log('Draft restored from ' + draftTime.toLocaleString());
        }
    }
}

// Clear form draft
function clearDraft() {
    const form = document.querySelector('.multi-step-form');
    if (!form) return;
    
    const draftKey = 'form_draft_' + (form.dataset.formId || 'unknown');
    localStorage.removeItem(draftKey);
    localStorage.removeItem(draftKey + '_timestamp');
}

// Add form change listeners
document.querySelectorAll('.multi-step-form input, .multi-step-form select, .multi-step-form textarea').forEach(function(field) {
    field.addEventListener('change', function() {
        updateFormProgress();
        autoSaveDraft();
    });
    
    field.addEventListener('input', function() {
        updateFormProgress();
    });
});

// Initialize form on page load
document.addEventListener('DOMContentLoaded', function() {
    if (document.querySelector('.multi-step-form')) {
        restoreDraft();
        updateFormProgress();
    }
});

// Form validation
function validateForm(form) {
    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');
    
    requiredFields.forEach(function(field) {
        if (!field.value.trim()) {
            field.parentElement.classList.add('has-error');
            isValid = false;
        } else {
            field.parentElement.classList.remove('has-error');
        }
    });
    
    return isValid;
}

// Prevent form double submission
document.querySelectorAll('form').forEach(function(form) {
    form.addEventListener('submit', function(e) {
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn && submitBtn.disabled) {
            e.preventDefault();
            return false;
        }
        
        if (submitBtn) {
            submitBtn.disabled = true;
            const originalText = submitBtn.textContent;
            submitBtn.textContent = '⏳ Processing...';
            
            // Restore button after a timeout if form submission fails
            setTimeout(function() {
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            }, 30000); // 30 second timeout
        }
        
        // Clear draft on successful submission
        if (form.classList.contains('multi-step-form')) {
            // Will be cleared after form submission succeeds
            clearDraft();
        }
    });
});

// ===== Dark Mode Theme =====

function initializeDarkMode() {
    const storedDarkMode = localStorage.getItem('darkMode');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    const isDarkMode = storedDarkMode === 'true' || (storedDarkMode === null && prefersDark);

    if (isDarkMode) {
        document.documentElement.setAttribute('data-theme', 'dark');
    } else {
        document.documentElement.removeAttribute('data-theme');
    }
}

function toggleDarkMode() {
    const isDarkMode = document.documentElement.getAttribute('data-theme') === 'dark';

    if (isDarkMode) {
        document.documentElement.removeAttribute('data-theme');
        localStorage.setItem('darkMode', 'false');
        const btn = document.querySelector('[data-toggle-dark-mode]');
        if (btn) btn.textContent = '☀️ Light Mode';
    } else {
        document.documentElement.setAttribute('data-theme', 'dark');
        localStorage.setItem('darkMode', 'true');
        const btn = document.querySelector('[data-toggle-dark-mode]');
        if (btn) btn.textContent = '🌙 Dark Mode';
    }
}

// Add dark mode toggle button functionality
document.querySelectorAll('[data-toggle-dark-mode]').forEach(function(btn) {
    btn.addEventListener('click', function() {
        toggleDarkMode();
    });
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeDarkMode();
    
    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function() {
        if (localStorage.getItem('darkMode') === null) {
            initializeDarkMode();
        }
    });
});

// ===== Form Search & Filtering =====

function setupSearchFilters() {
    const searchInput = document.querySelector('[data-search-filter]');
    const filterSelects = document.querySelectorAll('[data-filter]');
    
    if (!searchInput && filterSelects.length === 0) return;
    
    const items = document.querySelectorAll('[data-filterable]');
    
    function applyFilters() {
        const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
        const filters = {};
        
        filterSelects.forEach(function(select) {
            const filterKey = select.dataset.filter;
            filters[filterKey] = select.value.toLowerCase();
        });
        
        items.forEach(function(item) {
            let matches = true;
            
            if (searchTerm) {
                const text = item.textContent.toLowerCase();
                matches = text.includes(searchTerm);
            }
            
            Object.keys(filters).forEach(function(key) {
                if (filters[key]) {
                    const itemValue = item.dataset[key] ? item.dataset[key].toLowerCase() : '';
                    if (!itemValue.includes(filters[key])) {
                        matches = false;
                    }
                }
            });
            
            item.style.display = matches ? '' : 'none';
        });
    }
    
    if (searchInput) {
        searchInput.addEventListener('input', applyFilters);
    }
    
    filterSelects.forEach(function(select) {
        select.addEventListener('change', applyFilters);
    });
}

document.addEventListener('DOMContentLoaded', function() {
    setupSearchFilters();
});

// ===== Utility Functions =====

function showNotification(message, type = 'info') {
    const container = document.querySelector('.flash-messages-container') || 
                      document.querySelector('.alert-container') || 
                      document.body;
    
    const alert = document.createElement('div');
    alert.className = 'alert alert-' + type;
    alert.innerHTML = '<span>' + message + '</span><button class="alert-close-btn" onclick="this.parentElement.remove()">&times;</button>';
    
    const alertContainer = document.querySelector('.flash-messages-container') || 
                           document.querySelector('.alert-container');
    
    if (alertContainer) {
        alertContainer.appendChild(alert);
    } else {
        container.insertBefore(alert, container.firstChild);
    }
    
    // Auto-remove after 5 seconds
    setTimeout(function() {
        if (alert.parentElement) {
            alert.style.opacity = '0';
            setTimeout(function() {
                alert.remove();
            }, 300);
        }
    }, 5000);
}

// Initialize application
console.log('IITB SCAN - Patient Data Collection System v2.0 Loaded');
