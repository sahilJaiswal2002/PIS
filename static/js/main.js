// Main JavaScript file for IITB SCAN

// Auto-hide flash messages after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelectorAll('.flash');
    flashMessages.forEach(function(flash) {
        setTimeout(function() {
            flash.style.opacity = '0';
            flash.style.transform = 'translateX(100%)';
            setTimeout(function() {
                flash.remove();
            }, 300);
        }, 5000);
    });
});

// Close modal when clicking outside
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal')) {
        e.target.style.display = 'none';
    }
});

// Prevent form double submission
document.querySelectorAll('form').forEach(function(form) {
    form.addEventListener('submit', function() {
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Processing...';
        }
    });
});

console.log('IITB SCAN - Patient Data Collection System Loaded');
