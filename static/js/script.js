/**
 * Automated Exam Grading and Cheating Detection
 * Custom JavaScript functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all tooltips
    initTooltips();
    
    // Initialize all popovers
    initPopovers();
    
    // Add file upload visual enhancements
    enhanceFileUploads();
    
    // Enable dynamic form elements (sliders, etc.)
    initDynamicFormElements();
    
    // Initialize help elements
    initHelpElements();
    
    // Initialize interactive "How It Works" section
    initHowItWorks();
});

/**
 * Initialize Bootstrap tooltips with enhanced styling
 */
function initTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl, {
            delay: { show: 300, hide: 100 },
            animation: true
        });
    });
}

/**
 * Initialize Bootstrap popovers for help content
 */
function initPopovers() {
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl, {
            html: true,
            trigger: 'focus',
            placement: 'auto'
        });
    });
}

/**
 * Enhance file upload inputs with better UX
 */
function enhanceFileUploads() {
    // Get all custom file inputs
    const fileInputs = document.querySelectorAll('.custom-file-input');
    
    fileInputs.forEach(input => {
        // Handle the change event
        input.addEventListener('change', function(e) {
            // Get the label associated with this input
            const label = this.nextElementSibling;
            
            if (label && this.files.length > 0) {
                if (this.files.length > 1) {
                    // Show number of files selected
                    label.textContent = `${this.files.length} files selected`;
                } else {
                    // Show the file name
                    label.textContent = this.files[0].name;
                }
                
                // Update the file list if it exists
                updateFileList(this);
            } else if (label) {
                // Reset the label
                label.textContent = 'Choose file...';
            }
        });
    });
}

/**
 * Update file list display with selected files
 * @param {HTMLElement} input - File input element
 */
function updateFileList(input) {
    // Find the file list container
    const fileListContainerId = input.getAttribute('data-file-list');
    if (!fileListContainerId) return;
    
    const fileListContainer = document.getElementById(fileListContainerId);
    if (!fileListContainer) return;
    
    // Clear existing list
    fileListContainer.innerHTML = '';
    
    // Show warning when more than 15 files are selected
    if (input.files.length > 15) {
        // Clear the file selection and show a modal
        showFileLimitModal();
        
        // Reset the input
        input.value = '';
        const label = input.nextElementSibling;
        if (label) {
            label.textContent = 'Choose file...';
        }
        return;
    }
    
    // Add file items
    Array.from(input.files).forEach((file, index) => {
        // Create file item
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item d-flex align-items-center mb-2 p-2 bg-dark rounded';
        
        // File icon based on type
        const fileIcon = getFileIcon(file.name);
        
        // File size formatting
        const fileSize = formatFileSize(file.size);
        
        // File item inner HTML
        fileItem.innerHTML = `
            <span class="me-2">${fileIcon}</span>
            <div class="flex-grow-1 text-truncate">${file.name}</div>
            <span class="text-muted me-3">${fileSize}</span>
            <button type="button" class="btn btn-sm btn-outline-danger remove-file" data-index="${index}">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        fileListContainer.appendChild(fileItem);
    });
    
    // Add remove file functionality
    addRemoveFileHandlers(input, fileListContainer);
}

/**
 * Add handlers for file removal buttons
 * @param {HTMLElement} input - File input element
 * @param {HTMLElement} container - Container with file items
 */
function addRemoveFileHandlers(input, container) {
    const removeButtons = container.querySelectorAll('.remove-file');
    
    removeButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Since we can't directly modify a FileList, we need to reset the input
            // and recreate it with the files we want to keep
            input.value = '';
            const label = input.nextElementSibling;
            if (label) {
                label.textContent = 'Choose file...';
            }
            
            // Clear file list
            container.innerHTML = '';
        });
    });
}

/**
 * Get appropriate icon for file based on extension
 * @param {string} filename - Name of the file
 * @returns {string} HTML for the appropriate icon
 */
function getFileIcon(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    
    if (['jpg', 'jpeg', 'png', 'gif', 'bmp'].includes(ext)) {
        return '<i class="fas fa-file-image text-info"></i>';
    } else if (['doc', 'docx', 'rtf', 'txt'].includes(ext)) {
        return '<i class="fas fa-file-alt text-primary"></i>';
    } else if (['xls', 'xlsx', 'csv'].includes(ext)) {
        return '<i class="fas fa-file-excel text-success"></i>';
    } else if (['pdf'].includes(ext)) {
        return '<i class="fas fa-file-pdf text-danger"></i>';
    } else {
        return '<i class="fas fa-file text-secondary"></i>';
    }
}

/**
 * Format file size into human-readable format
 * @param {number} bytes - Size in bytes
 * @returns {string} Formatted size
 */
function formatFileSize(bytes) {
    if (bytes < 1024) {
        return bytes + ' B';
    } else if (bytes < 1048576) {
        return (bytes / 1024).toFixed(1) + ' KB';
    } else if (bytes < 1073741824) {
        return (bytes / 1048576).toFixed(1) + ' MB';
    } else {
        return (bytes / 1073741824).toFixed(1) + ' GB';
    }
}

/**
 * Initialize dynamic form elements like sliders
 */
function initDynamicFormElements() {
    // Range sliders with tooltips
    const sliders = document.querySelectorAll('input[type="range"]');
    
    sliders.forEach(slider => {
        // Get or create display element
        let displayEl = document.getElementById(`${slider.id}-value`);
        
        if (!displayEl && slider.parentElement) {
            displayEl = document.createElement('span');
            displayEl.id = `${slider.id}-value`;
            displayEl.className = 'badge bg-primary ms-2';
            slider.parentElement.appendChild(displayEl);
        }
        
        if (displayEl) {
            // Initial update
            const value = parseFloat(slider.value);
            const min = parseFloat(slider.min || 0);
            const max = parseFloat(slider.max || 100);
            
            // Update display
            displayEl.textContent = formatSliderValue(slider, value);
            
            // Position the badge relative to the slider
            updateSliderBadgePosition(slider, displayEl, value, min, max);
            
            // Update on input
            slider.addEventListener('input', function() {
                const newValue = parseFloat(this.value);
                displayEl.textContent = formatSliderValue(this, newValue);
                updateSliderBadgePosition(this, displayEl, newValue, min, max);
            });
        }
    });
}

/**
 * Format slider value based on data attributes
 * @param {HTMLElement} slider - Range input element
 * @param {number} value - Current value
 * @returns {string} Formatted value
 */
function formatSliderValue(slider, value) {
    const suffix = slider.dataset.suffix || '';
    const decimals = parseInt(slider.dataset.decimals || '0', 10);
    
    if (decimals > 0) {
        return value.toFixed(decimals) + suffix;
    }
    
    return value + suffix;
}

/**
 * Update position of slider value badge
 * @param {HTMLElement} slider - Range input element 
 * @param {HTMLElement} badge - Badge element
 * @param {number} value - Current value
 * @param {number} min - Minimum value
 * @param {number} max - Maximum value
 */
function updateSliderBadgePosition(slider, badge, value, min, max) {
    // Position is relative to slider's value position
    const percentage = ((value - min) / (max - min)) * 100;
    
    // Apply positioning via CSS variable
    slider.style.setProperty('--slider-value-position', `${percentage}%`);
}

/**
 * Initialize help elements throughout the app
 */
function initHelpElements() {
    // Get all help buttons/icons
    const helpElements = document.querySelectorAll('.help-icon, [data-help]');
    
    helpElements.forEach(element => {
        element.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Show help modal or tooltip based on data attributes
            const helpType = this.dataset.helpType || 'tooltip';
            const helpContent = this.dataset.help;
            
            if (helpType === 'modal' && helpContent) {
                showHelpModal(helpContent);
            }
        });
    });
    
    // Initialize the help button in the navbar
    const helpButton = document.querySelector('.btn-help');
    if (helpButton) {
        helpButton.addEventListener('click', function() {
            // Determine which help content to show based on the current page
            const currentPath = window.location.pathname;
            
            if (currentPath.includes('mcq_analysis')) {
                showHelpModal('mcq');
            } else if (currentPath.includes('essay_analysis')) {
                showHelpModal('essay');
            } else {
                showHelpModal('main');
            }
        });
    }
}

/**
 * Display a help modal with the specified content
 * @param {string} contentType - Type of help content to show
 */
function showHelpModal(contentType) {
    // Create modal if it doesn't exist
    let modal = document.getElementById('helpModal');
    
    if (!modal) {
        modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'helpModal';
        modal.setAttribute('tabindex', '-1');
        modal.setAttribute('aria-labelledby', 'helpModalLabel');
        modal.setAttribute('aria-hidden', 'true');
        
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="helpModalLabel">Help & Documentation</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <!-- Content will be loaded here -->
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
    }
    
    // Get the modal body
    const modalBody = modal.querySelector('.modal-body');
    
    // Set content based on type
    if (contentType === 'main') {
        modalBody.innerHTML = `
            <h4>Welcome to the Exam Analyzer</h4>
            <p>This application helps you analyze multiple-choice questions and essays for grading and cheating detection.</p>
            
            <h5 class="mt-4">MCQ Analysis</h5>
            <p>Upload a reference answer file and student answer files to compare them. The system will calculate scores and detect potential cheating.</p>
            
            <h5 class="mt-4">Essay Analysis</h5>
            <p>Upload a reference essay and student essays to evaluate similarity. The system will score each essay and flag potential cheating between students.</p>
            
            <h5 class="mt-4">File Format</h5>
            <p>Files should be plain text (.txt) or CSV files. Each line in MCQ files should contain a question number and answer.</p>
            <p>For student files, use the naming format: "Student Name / ID" to help with identification.</p>
            
            <h5 class="mt-4">Need More Help?</h5>
            <p>Click the help icons <i class="fas fa-question-circle"></i> throughout the application for context-specific guidance.</p>
        `;
    } else if (contentType === 'mcq') {
        modalBody.innerHTML = `
            <h4>MCQ Analysis Help</h4>
            <p>This section allows you to analyze multiple-choice questions by comparing student answers to a reference answer key.</p>
            
            <h5 class="mt-4">Steps:</h5>
            <ol>
                <li>Upload a reference answer file containing the correct answers</li>
                <li>Upload student answer files (maximum 15 files per submission)</li>
                <li>Adjust the similarity threshold if needed</li>
                <li>Click "Analyze" to process the files</li>
            </ol>
            
            <h5 class="mt-4">File Format:</h5>
            <p>Both reference and student files should be in one of these formats:</p>
            <pre>
1. A
2. C
3. D
4. B
</pre>
            <p>Or CSV format:</p>
            <pre>
Question,Answer
1,A
2,C
3,D
4,B
</pre>
        `;
    } else if (contentType === 'essay') {
        modalBody.innerHTML = `
            <h4>Essay Analysis Help</h4>
            <p>This section allows you to analyze essays by comparing student submissions to a reference essay and detecting similarities between students.</p>
            
            <h5 class="mt-4">Steps:</h5>
            <ol>
                <li>Upload a reference essay file</li>
                <li>Upload student essay files (maximum 15 files per submission)</li>
                <li>Adjust the similarity threshold if needed</li>
                <li>Click "Analyze" to process the essays</li>
            </ol>
            
            <h5 class="mt-4">File Format:</h5>
            <p>Files should be plain text (.txt) containing the essay content.</p>
            
            <h5 class="mt-4">Threshold Adjustment:</h5>
            <p>The threshold controls how strict the similarity detection is:</p>
            <ul>
                <li>Higher values (closer to 1.0): More strict, requiring higher similarity to flag potential cheating</li>
                <li>Lower values (closer to 0.5): More lenient, flagging more cases as potential cheating</li>
            </ul>
        `;
    } else {
        modalBody.innerHTML = `<p>${contentType}</p>`;
    }
    
    // Show the modal
    const modalInstance = new bootstrap.Modal(modal);
    modalInstance.show();
}

/**
 * Initialize the interactive "How It Works" section
 */
function initHowItWorks() {
    // Handle toggle details buttons
    const toggleButtons = document.querySelectorAll('.toggle-details');
    
    if (!toggleButtons.length) return; // Exit if no toggle buttons found
    
    // Hide all feature details initially
    document.querySelectorAll('.feature-details').forEach(details => {
        details.style.display = 'none';
        details.style.opacity = '0';
        details.style.transform = 'translateY(20px)';
    });
    
    toggleButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.stopPropagation(); // Prevent the event from bubbling up
            
            const step = this.closest('.feature-step');
            const details = step.querySelector('.feature-details');
            
            // Toggle details visibility with animation
            if (details.classList.contains('active')) {
                details.style.opacity = '0';
                details.style.transform = 'translateY(20px)';
                
                setTimeout(() => {
                    details.classList.remove('active');
                    details.style.display = 'none';
                    
                    // Update button text using the main-toggle class
                    const mainButton = step.querySelector('.main-toggle');
                    if (mainButton) {
                        mainButton.textContent = 'Learn More';
                        mainButton.classList.remove('btn-outline-secondary');
                        mainButton.classList.add(getButtonClass(step));
                    }
                }, 300);
            } else {
                details.style.display = 'block';
                
                // Allow the display: block to take effect before animating
                setTimeout(() => {
                    details.classList.add('active');
                    details.style.opacity = '1';
                    details.style.transform = 'translateY(0)';
                    
                    // Update button text using the main-toggle class
                    const mainButton = step.querySelector('.main-toggle');
                    if (mainButton) {
                        mainButton.textContent = 'Show Less';
                        mainButton.classList.remove(getButtonClass(step));
                        mainButton.classList.add('btn-outline-secondary');
                    }
                }, 10);
            }
            
            // Add active class to the step
            step.classList.add('active');
            
            // Remove active class from other steps
            document.querySelectorAll('.feature-step').forEach(otherStep => {
                if (otherStep !== step) {
                    otherStep.classList.remove('active');
                    const otherDetails = otherStep.querySelector('.feature-details');
                    if (otherDetails && otherDetails.classList.contains('active')) {
                        otherDetails.style.opacity = '0';
                        otherDetails.style.transform = 'translateY(20px)';
                        
                        setTimeout(() => {
                            otherDetails.classList.remove('active');
                            otherDetails.style.display = 'none';
                            
                            // Update other buttons
                            const otherButtons = otherStep.querySelectorAll('.toggle-details');
                            otherButtons.forEach(btn => {
                                if (!btn.closest('.feature-details')) {
                                    btn.textContent = 'Learn More';
                                    btn.classList.remove('btn-outline-secondary');
                                    btn.classList.add(getButtonClass(otherStep));
                                }
                            });
                        }, 300);
                    }
                }
            });
        });
    });
    
    // Make the feature steps themselves clickable to show details
    const featureSteps = document.querySelectorAll('.feature-step');
    
    featureSteps.forEach(step => {
        // Add hover animation to the number behind the step
        step.addEventListener('mouseenter', function() {
            this.classList.add('hovered');
        });
        
        step.addEventListener('mouseleave', function() {
            this.classList.remove('hovered');
        });
        
        step.addEventListener('click', function(e) {
            // Don't trigger if clicking on buttons or details
            if (e.target.classList.contains('toggle-details') || 
                e.target.closest('.toggle-details') ||
                e.target.closest('.feature-details') || 
                e.target.closest('.btn')) {
                return;
            }
            
            // Add ripple effect
            addRippleEffect(this, e);
            
            // Find and click the toggle button to show/hide details
            const toggleButton = this.querySelector('.toggle-details:not(.feature-details .toggle-details)');
            if (toggleButton) {
                toggleButton.click();
            }
        });
    });
}

/**
 * Add ripple effect to an element on click
 * @param {HTMLElement} element - The element to add the ripple to
 * @param {Event} event - The click event
 */
function addRippleEffect(element, event) {
    // Create ripple element
    const ripple = document.createElement('span');
    ripple.classList.add('ripple-effect');
    
    // Position the ripple at the click point
    const rect = element.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    
    ripple.style.width = ripple.style.height = `${size}px`;
    ripple.style.left = `${event.clientX - rect.left - size / 2}px`;
    ripple.style.top = `${event.clientY - rect.top - size / 2}px`;
    
    // Add ripple to element
    element.appendChild(ripple);
    
    // Remove ripple after animation
    setTimeout(() => {
        ripple.remove();
    }, 600);
}

/**
 * Get the appropriate button class based on the step number
 * @param {HTMLElement} step - The step element
 * @returns {string} The button class
 */
function getButtonClass(step) {
    const stepNumber = step.getAttribute('data-step');
    
    switch(stepNumber) {
        case '1':
            return 'btn-outline-primary';
        case '2':
            return 'btn-outline-success';
        case '3':
            return 'btn-outline-info';
        default:
            return 'btn-outline-secondary';
    }
}

/**
 * Show a modal explaining the file limit and what to do
 */
function showFileLimitModal() {
    // Create modal if it doesn't exist
    let modal = document.getElementById('fileLimitModal');
    
    if (!modal) {
        modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'fileLimitModal';
        modal.setAttribute('tabindex', '-1');
        modal.setAttribute('aria-labelledby', 'fileLimitModalLabel');
        modal.setAttribute('aria-hidden', 'true');
        
        modal.innerHTML = `
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header bg-warning text-dark">
                        <h5 class="modal-title" id="fileLimitModalLabel">
                            <i class="fas fa-exclamation-triangle me-2"></i>File Limit Reached
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <p>You've selected more than 15 files at once.</p>
                        <p>Please submit the current files first, then upload additional files in a subsequent submission.</p>
                        <p class="mb-0 small text-muted">This limit helps ensure stable processing and analysis.</p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-primary" data-bs-dismiss="modal">I Understand</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
    }
    
    // Show the modal
    const modalInstance = new bootstrap.Modal(modal);
    modalInstance.show();
}