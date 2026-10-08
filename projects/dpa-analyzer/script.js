// DPA Analysis Frontend JavaScript

const API_BASE_URL = 'http://localhost:8000';

// DOM Elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const fileSize = document.getElementById('fileSize');
const analyzeBtn = document.getElementById('analyzeBtn');
const uploadSection = document.getElementById('uploadSection');
const loadingSection = document.getElementById('loadingSection');
const resultsSection = document.getElementById('resultsSection');

// State
let selectedFile = null;
let currentAnalysis = null;

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
    loadPlaybook();
});

function setupEventListeners() {
    // File input change
    fileInput.addEventListener('change', handleFileSelect);
    
    // Drag and drop
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
    uploadArea.addEventListener('click', () => fileInput.click());
    
    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });
}

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function handleDragOver(e) {
    uploadArea.classList.add('dragover');
}

function handleDragLeave(e) {
    uploadArea.classList.remove('dragover');
}

function handleDrop(e) {
    uploadArea.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileSelect({ target: { files } });
    }
}

function handleFileSelect(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    // Validate file type
    const allowedTypes = ['.pdf', '.doc', '.docx', '.txt'];
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!allowedTypes.includes(fileExtension)) {
        alert('Please upload a PDF, DOC, DOCX, or TXT file.');
        return;
    }
    
    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
        alert('File size must be less than 10MB.');
        return;
    }
    
    selectedFile = file;
    displayFileInfo(file);
}

function displayFileInfo(file) {
    fileName.textContent = file.name;
    fileSize.textContent = formatFileSize(file.size);
    fileInfo.style.display = 'flex';
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

async function analyzeDocument() {
    if (!selectedFile) {
        alert('Please select a file first.');
        return;
    }
    
    try {
        // Show loading state
        showSection('loading');
        updateLoadingProgress();
        
        // Prepare form data
        const formData = new FormData();
        formData.append('file', selectedFile);
        
        // Make API call
        const response = await fetch(`${API_BASE_URL}/analyze-dpa`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        currentAnalysis = result.analysis;
        
        // Show results
        setTimeout(() => {
            displayResults(currentAnalysis);
            showSection('results');
        }, 1500); // Small delay for better UX
        
    } catch (error) {
        console.error('Analysis failed:', error);
        alert(`Analysis failed: ${error.message}`);
        showSection('upload');
    }
}

function updateLoadingProgress() {
    const steps = document.querySelectorAll('.step');
    let currentStep = 0;
    
    const interval = setInterval(() => {
        if (currentStep < steps.length) {
            steps[currentStep].classList.add('active');
            currentStep++;
        } else {
            clearInterval(interval);
        }
    }, 800);
}

function displayResults(analysis) {
    // Overall Assessment
    const complianceScore = document.getElementById('complianceScore');
    const riskLevel = document.getElementById('riskLevel');
    const executiveSummary = document.getElementById('executiveSummary');
    
    if (analysis.overall_assessment) {
        complianceScore.textContent = analysis.overall_assessment.compliance_score + '%';
        riskLevel.textContent = analysis.overall_assessment.risk_level.toUpperCase();
        riskLevel.className = `metric-value risk-level ${analysis.overall_assessment.risk_level}`;
        executiveSummary.textContent = analysis.overall_assessment.executive_summary || 'No summary available.';
    }
    
    // Section Analysis
    displaySectionAnalysis(analysis.section_analysis || []);
    
    // Key Findings
    displayFindings('criticalIssues', analysis.critical_issues || []);
    displayFindings('strengths', analysis.strengths || []);
    displayFindings('missingClauses', analysis.missing_clauses || []);
    displayFindings('recommendations', analysis.recommendations || []);
}

function displaySectionAnalysis(sections) {
    const container = document.getElementById('sectionResults');
    container.innerHTML = '';
    
    sections.forEach((section, index) => {
        const sectionElement = createSectionElement(section, index);
        container.appendChild(sectionElement);
    });
}

function createSectionElement(section, index) {
    const sectionDiv = document.createElement('div');
    sectionDiv.className = 'section-item';
    
    const statusClass = `status-${section.status || 'unclear'}`;
    const statusText = (section.status || 'unclear').replace('_', ' ').toUpperCase();
    
    sectionDiv.innerHTML = `
        <div class="section-header" onclick="toggleSection(${index})">
            <div class="section-title">${section.section}</div>
            <div class="section-info">
                <span class="section-score">Score: ${section.score || 'N/A'}</span>
                <span class="section-status ${statusClass}">${statusText}</span>
                <i class="fas fa-chevron-down"></i>
            </div>
        </div>
        <div class="section-content" id="section-${index}">
            <div class="section-details">
                ${section.findings && section.findings.length > 0 ? 
                    `<div class="findings">
                        <h5>Findings:</h5>
                        <ul>
                            ${section.findings.map(finding => `<li>${finding}</li>`).join('')}
                        </ul>
                    </div>` : ''
                }
                ${section.recommendations && section.recommendations.length > 0 ? 
                    `<div class="recommendations">
                        <h5>Recommendations:</h5>
                        <ul>
                            ${section.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                        </ul>
                    </div>` : ''
                }
                ${section.red_flags && section.red_flags.length > 0 ? 
                    `<div class="red-flags">
                        <h5>Red Flags:</h5>
                        <ul>
                            ${section.red_flags.map(flag => `<li>${flag}</li>`).join('')}
                        </ul>
                    </div>` : ''
                }
            </div>
        </div>
    `;
    
    return sectionDiv;
}

function toggleSection(index) {
    const content = document.getElementById(`section-${index}`);
    const chevron = content.previousElementSibling.querySelector('.fa-chevron-down');
    
    if (content.classList.contains('expanded')) {
        content.classList.remove('expanded');
        chevron.style.transform = 'rotate(0deg)';
    } else {
        content.classList.add('expanded');
        chevron.style.transform = 'rotate(180deg)';
    }
}

function displayFindings(elementId, items) {
    const container = document.getElementById(elementId);
    container.innerHTML = '';
    
    if (items.length === 0) {
        container.innerHTML = '<li>None identified</li>';
        return;
    }
    
    items.forEach(item => {
        const li = document.createElement('li');
        li.textContent = item;
        container.appendChild(li);
    });
}

function showSection(sectionName) {
    // Hide all sections
    uploadSection.style.display = 'none';
    loadingSection.style.display = 'none';
    resultsSection.style.display = 'none';
    
    // Show requested section
    switch(sectionName) {
        case 'upload':
            uploadSection.style.display = 'block';
            break;
        case 'loading':
            loadingSection.style.display = 'block';
            break;
        case 'results':
            resultsSection.style.display = 'block';
            break;
    }
}

function resetAnalysis() {
    selectedFile = null;
    currentAnalysis = null;
    fileInfo.style.display = 'none';
    fileInput.value = '';
    
    // Reset loading steps
    document.querySelectorAll('.step').forEach((step, index) => {
        if (index === 0) {
            step.classList.add('active');
        } else {
            step.classList.remove('active');
        }
    });
    
    showSection('upload');
}

async function loadPlaybook() {
    try {
        const response = await fetch(`${API_BASE_URL}/playbook`);
        if (response.ok) {
            const data = await response.json();
            displayPlaybook(data.playbook);
        }
    } catch (error) {
        console.error('Failed to load playbook:', error);
    }
}

function displayPlaybook(playbook) {
    const container = document.getElementById('playbookDetails');
    
    if (!playbook) return;
    
    let html = `
        <div class="playbook-overview">
            <h3>${playbook.overview?.title || 'DPA Review Playbook'}</h3>
            <p>${playbook.overview?.purpose || ''}</p>
        </div>
    `;
    
    if (playbook.review_sections) {
        html += '<div class="playbook-sections">';
        playbook.review_sections.forEach((section, index) => {
            html += `
                <div class="playbook-section">
                    <h4>${section.section}</h4>
                    <p>${section.description}</p>
                    
                    ${section.key_points ? `
                        <div class="key-points">
                            <h5>Key Points:</h5>
                            <ul>
                                ${section.key_points.map(point => `<li>${point}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                    
                    ${section.red_flags ? `
                        <div class="red-flags">
                            <h5>Red Flags:</h5>
                            <ul>
                                ${section.red_flags.map(flag => `<li>${flag}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            `;
        });
        html += '</div>';
    }
    
    container.innerHTML = html;
}

function togglePlaybook() {
    const content = document.getElementById('playbookContent');
    const button = document.querySelector('[onclick="togglePlaybook()"]');
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        button.innerHTML = '<i class="fas fa-eye-slash"></i> Hide Playbook';
    } else {
        content.style.display = 'none';
        button.innerHTML = '<i class="fas fa-eye"></i> View Playbook';
    }
}

// Export functions for global access
window.analyzeDocument = analyzeDocument;
window.resetAnalysis = resetAnalysis;
window.togglePlaybook = togglePlaybook;
window.toggleSection = toggleSection;
