// Main JavaScript functions for the research assistant

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Activate tab based on URL hash
    const hash = window.location.hash;
    if (hash) {
        const tab = document.querySelector(`a[href="${hash}"]`);
        if (tab) {
            new bootstrap.Tab(tab).show();
        }
    }
    
    // Update URL hash when tab changes
    const tabEls = document.querySelectorAll('a[data-bs-toggle="tab"]');
    tabEls.forEach(tabEl => {
        tabEl.addEventListener('shown.bs.tab', function(event) {
            history.pushState(null, null, event.target.getAttribute('href'));
        });
    });
    
    // Toggle papers read status
    const readStatusCheckboxes = document.querySelectorAll('.read-status');
    if (readStatusCheckboxes) {
        readStatusCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                const paperId = this.getAttribute('data-paper-id');
                updateReadStatus(paperId, this.checked);
            });
        });
    }
    
    // Toggle reminder completion status
    const reminderCheckboxes = document.querySelectorAll('.reminder-status');
    if (reminderCheckboxes) {
        reminderCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                const reminderId = this.getAttribute('data-reminder-id');
                toggleReminderStatus(reminderId);
            });
        });
    }
    
    // Search DOI metadata form
    const doiSearchForm = document.getElementById('doi-search-form');
    if (doiSearchForm) {
        doiSearchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const doi = document.getElementById('doi-input').value.trim();
            fetchDoiMetadata(doi);
        });
    }
    
    // Paper search form
    const paperSearchForm = document.getElementById('paper-search-form');
    if (paperSearchForm) {
        paperSearchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const query = document.getElementById('paper-search-input').value.trim();
            searchPapers(query);
        });
    }
    
    // Patent search form
    const patentSearchForm = document.getElementById('patent-search-form');
    if (patentSearchForm) {
        patentSearchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const query = document.getElementById('patent-search-input').value.trim();
            searchPatents(query);
        });
    }
    
    // Generate citation form
    const citationForm = document.getElementById('citation-form');
    if (citationForm) {
        citationForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const doi = document.getElementById('citation-doi').value.trim();
            const style = document.getElementById('citation-style').value;
            generateCitation(doi, style);
        });
    }
});

// Update read status for a paper
function updateReadStatus(paperId, isRead) {
    fetch(`/papers/${paperId}/read`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ read_status: isRead })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update UI if needed
            const paperRow = document.querySelector(`tr[data-paper-id="${paperId}"]`);
            if (paperRow) {
                if (isRead) {
                    paperRow.classList.add('table-success');
                } else {
                    paperRow.classList.remove('table-success');
                }
            }
        } else {
            console.error('Failed to update read status');
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// Toggle reminder status
function toggleReminderStatus(reminderId) {
    fetch(`/reminders/${reminderId}/toggle`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update UI
            const reminderItem = document.querySelector(`li[data-reminder-id="${reminderId}"]`);
            if (reminderItem) {
                if (data.completed) {
                    reminderItem.classList.add('text-muted');
                    reminderItem.querySelector('.reminder-text').style.textDecoration = 'line-through';
                } else {
                    reminderItem.classList.remove('text-muted');
                    reminderItem.querySelector('.reminder-text').style.textDecoration = 'none';
                }
            }
        } else {
            console.error('Failed to update reminder status');
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// Fetch metadata for a DOI
function fetchDoiMetadata(doi) {
    const resultsDiv = document.getElementById('doi-results');
    resultsDiv.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>';
    
    fetch(`/papers/doi/${encodeURIComponent(doi)}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                resultsDiv.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                return;
            }
            
            // Fill the paper form with metadata
            document.getElementById('paper-title').value = data.title || '';
            document.getElementById('paper-authors').value = data.authors || '';
            document.getElementById('paper-publication').value = data.publication || '';
            document.getElementById('paper-year').value = data.year || '';
            document.getElementById('paper-doi').value = data.doi || '';
            document.getElementById('paper-url').value = data.url || '';
            document.getElementById('paper-abstract').value = data.abstract || '';
            document.getElementById('paper-keywords').value = data.keywords || '';
            
            // Show the form
            document.getElementById('add-paper-form').classList.remove('d-none');
            
            // Display metadata
            resultsDiv.innerHTML = `
                <div class="alert alert-success">
                    <h5>${data.title}</h5>
                    <p><strong>Authors:</strong> ${data.authors || 'N/A'}</p>
                    <p><strong>Publication:</strong> ${data.publication || 'N/A'}</p>
                    <p><strong>Year:</strong> ${data.year || 'N/A'}</p>
                </div>
            `;
        })
        .catch(error => {
            console.error('Error:', error);
            resultsDiv.innerHTML = `<div class="alert alert-danger">Error fetching DOI information: ${error.message}</div>`;
        });
}

// Search for papers
function searchPapers(query) {
    const resultsDiv = document.getElementById('paper-search-results');
    resultsDiv.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>';
    
    fetch(`/papers/search?query=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            if (data.length === 0) {
                resultsDiv.innerHTML = '<div class="alert alert-info">No papers found. Try a different search term.</div>';
                return;
            }
            
            let html = '<div class="list-group">';
            data.forEach(paper => {
                html += `
                    <div class="list-group-item list-group-item-action">
                        <div class="d-flex w-100 justify-content-between">
                            <h5 class="mb-1">${paper.title}</h5>
                            <small>${paper.year}</small>
                        </div>
                        <p class="mb-1">${paper.authors || 'N/A'}</p>
                        <small>${paper.publication || 'N/A'}</small>
                        <div class="mt-2">
                            <button class="btn btn-sm btn-outline-primary add-paper-btn" 
                                data-title="${paper.title}" 
                                data-authors="${paper.authors || ''}" 
                                data-publication="${paper.publication || ''}" 
                                data-year="${paper.year || ''}" 
                                data-doi="${paper.doi || ''}" 
                                data-url="${paper.url || ''}">
                                Add to Library
                            </button>
                        </div>
                    </div>
                `;
            });
            html += '</div>';
            
            resultsDiv.innerHTML = html;
            
            // Add event listeners to the "Add to Library" buttons
            document.querySelectorAll('.add-paper-btn').forEach(btn => {
                btn.addEventListener('click', function() {
                    const paperData = {
                        title: this.getAttribute('data-title'),
                        authors: this.getAttribute('data-authors'),
                        publication: this.getAttribute('data-publication'),
                        year: this.getAttribute('data-year'),
                        doi: this.getAttribute('data-doi'),
                        url: this.getAttribute('data-url')
                    };
                    
                    fillPaperForm(paperData);
                });
            });
        })
        .catch(error => {
            console.error('Error:', error);
            resultsDiv.innerHTML = `<div class="alert alert-danger">Error searching papers: ${error.message}</div>`;
        });
}

// Fill paper form with data
function fillPaperForm(paperData) {
    document.getElementById('paper-title').value = paperData.title || '';
    document.getElementById('paper-authors').value = paperData.authors || '';
    document.getElementById('paper-publication').value = paperData.publication || '';
    document.getElementById('paper-year').value = paperData.year || '';
    document.getElementById('paper-doi').value = paperData.doi || '';
    document.getElementById('paper-url').value = paperData.url || '';
    
    // Show the form
    document.getElementById('add-paper-form').classList.remove('d-none');
    
    // Scroll to form
    document.getElementById('add-paper-form').scrollIntoView({ behavior: 'smooth' });
}

// Search for patents
function searchPatents(query) {
    const resultsDiv = document.getElementById('patent-search-results');
    resultsDiv.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>';
    
    fetch(`/patents/search?query=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            if (data.length === 0) {
                resultsDiv.innerHTML = '<div class="alert alert-info">No patents found. Try a different search term.</div>';
                return;
            }
            
            let html = '<div class="list-group">';
            data.forEach(patent => {
                html += `
                    <div class="list-group-item list-group-item-action">
                        <div class="d-flex w-100 justify-content-between">
                            <h5 class="mb-1">${patent.title}</h5>
                            <small>${patent.patent_number}</small>
                        </div>
                        <p class="mb-1">${patent.inventors || 'N/A'}</p>
                        <small>${patent.assignee || 'N/A'} (${patent.issue_date || 'N/A'})</small>
                        <div class="mt-2">
                            <button class="btn btn-sm btn-outline-primary add-patent-btn" 
                                data-title="${patent.title}" 
                                data-number="${patent.patent_number || ''}" 
                                data-inventors="${patent.inventors || ''}" 
                                data-assignee="${patent.assignee || ''}" 
                                data-filing="${patent.filing_date || ''}" 
                                data-issue="${patent.issue_date || ''}" 
                                data-url="${patent.url || ''}">
                                Add to Library
                            </button>
                        </div>
                    </div>
                `;
            });
            html += '</div>';
            
            resultsDiv.innerHTML = html;
            
            // Add event listeners to the "Add to Library" buttons
            document.querySelectorAll('.add-patent-btn').forEach(btn => {
                btn.addEventListener('click', function() {
                    const patentData = {
                        title: this.getAttribute('data-title'),
                        patent_number: this.getAttribute('data-number'),
                        inventors: this.getAttribute('data-inventors'),
                        assignee: this.getAttribute('data-assignee'),
                        filing_date: this.getAttribute('data-filing'),
                        issue_date: this.getAttribute('data-issue'),
                        url: this.getAttribute('data-url')
                    };
                    
                    fillPatentForm(patentData);
                });
            });
        })
        .catch(error => {
            console.error('Error:', error);
            resultsDiv.innerHTML = `<div class="alert alert-danger">Error searching patents: ${error.message}</div>`;
        });
}

// Fill patent form with data
function fillPatentForm(patentData) {
    document.getElementById('patent-title').value = patentData.title || '';
    document.getElementById('patent-number').value = patentData.patent_number || '';
    document.getElementById('patent-inventors').value = patentData.inventors || '';
    document.getElementById('patent-assignee').value = patentData.assignee || '';
    document.getElementById('patent-filing-date').value = patentData.filing_date || '';
    document.getElementById('patent-issue-date').value = patentData.issue_date || '';
    document.getElementById('patent-url').value = patentData.url || '';
    
    // Show the form
    document.getElementById('add-patent-form').classList.remove('d-none');
    
    // Scroll to form
    document.getElementById('add-patent-form').scrollIntoView({ behavior: 'smooth' });
}

// Generate citation
function generateCitation(doi, style) {
    const resultsDiv = document.getElementById('citation-results');
    resultsDiv.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>';
    
    fetch('/papers/citation', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ doi: doi, style: style })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            resultsDiv.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
            return;
        }
        
        resultsDiv.innerHTML = `
            <div class="alert alert-success">
                <h5>Citation (${style.toUpperCase()})</h5>
                <p class="mb-2">${data.citation}</p>
                <button class="btn btn-sm btn-outline-primary" onclick="copyToClipboard('${data.citation.replace(/'/g, "\\'")}')">
                    <i class="fas fa-copy"></i> Copy
                </button>
            </div>
        `;
    })
    .catch(error => {
        console.error('Error:', error);
        resultsDiv.innerHTML = `<div class="alert alert-danger">Error generating citation: ${error.message}</div>`;
    });
}

// Copy text to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        // Show a toast or notification
        const toast = document.createElement('div');
        toast.className = 'position-fixed bottom-0 end-0 p-3';
        toast.style.zIndex = 1050;
        toast.innerHTML = `
            <div id="copyToast" class="toast align-items-center bg-success text-white" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">
                        Copied to clipboard!
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>
        `;
        document.body.appendChild(toast);
        
        const toastElement = new bootstrap.Toast(document.getElementById('copyToast'), { delay: 2000 });
        toastElement.show();
        
        // Remove the toast element after it's hidden
        document.getElementById('copyToast').addEventListener('hidden.bs.toast', () => {
            document.body.removeChild(toast);
        });
    }).catch(err => {
        console.error('Error copying text: ', err);
    });
}

// Delete a research item with confirmation
function confirmDelete(type, id, name) {
    if (confirm(`Are you sure you want to delete "${name}"?`)) {
        document.getElementById(`delete-${type}-${id}`).submit();
    }
}
