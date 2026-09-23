/**
 * main.js — Campus Placement Analytics System
 * Global JavaScript utilities shared across all pages.
 */

/**
 * Toggle the visibility of an inline sub-form (skills, certs, etc.)
 * Called from student_profile.html buttons.
 */
function toggleSubForm(id) {
    const el = document.getElementById(id);
    if (el) {
        el.classList.toggle('hidden');
        // Scroll into view if being shown
        if (!el.classList.contains('hidden')) {
            el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }
}

/**
 * Delete confirmation modal for the student list page.
 */
function openDeleteModal(studentId, studentName) {
    const modal = document.getElementById('deleteModal');
    const nameEl = document.getElementById('deleteStudentName');
    const idEl = document.getElementById('deleteStudentID');
    const form = document.getElementById('deleteStudentForm');

    if (!modal) return;
    nameEl.textContent = studentName;
    idEl.textContent = studentId;
    form.action = '/students/' + studentId + '/delete';
    modal.style.display = 'flex';
}

function closeDeleteModal() {
    const modal = document.getElementById('deleteModal');
    if (modal) modal.style.display = 'none';
}

/**
 * Delete confirmation modal for the company list page.
 */
function openCompanyDeleteModal(companyId, companyName) {
    const modal = document.getElementById('companyDeleteModal');
    const nameEl = document.getElementById('deleteCompanyName');
    const idEl = document.getElementById('deleteCompanyID');
    const form = document.getElementById('deleteCompanyForm');

    if (!modal) return;
    nameEl.textContent = companyName;
    idEl.textContent = companyId;
    form.action = '/companies/' + companyId + '/delete';
    modal.style.display = 'flex';
}

function closeCompanyDeleteModal() {
    const modal = document.getElementById('companyDeleteModal');
    if (modal) modal.style.display = 'none';
}

// Close modal on backdrop click or ESC key
document.addEventListener('DOMContentLoaded', function () {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            alert.style.transition = 'opacity 0.5s ease';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 500);
        }, 4000);
    });

    // Confirm delete for any form with data-confirm attribute
    const confirmForms = document.querySelectorAll('form[data-confirm]');
    confirmForms.forEach(function (form) {
        form.addEventListener('submit', function (e) {
            const message = form.getAttribute('data-confirm');
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });

    // Close delete modals when clicking the backdrop overlay
    const deleteModal = document.getElementById('deleteModal');
    if (deleteModal) {
        deleteModal.addEventListener('click', function (e) {
            if (e.target === deleteModal) closeDeleteModal();
        });
    }

    const companyDeleteModal = document.getElementById('companyDeleteModal');
    if (companyDeleteModal) {
        companyDeleteModal.addEventListener('click', function (e) {
            if (e.target === companyDeleteModal) closeCompanyDeleteModal();
        });
    }

    // Close delete modal on ESC key
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            closeDeleteModal();
            closeCompanyDeleteModal();
        }
    });
});
