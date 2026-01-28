const API_URL = 'http://localhost:8000/api';

// Section icons mapping
const sectionIcons = {
    'Contact Information': '📧',
    'Professional Summary': '📝',
    'Work Experience': '💼',
    'Skills': '⚡',
    'Education': '🎓',
    'Certifications': '🏆',
    'Formatting & Structure': '📐'
};

// Store sections data globally for click handling
let sectionsData = [];
let matchedSkillsData = [];
let missingSkillsData = [];
let rewrittenBulletsData = [];
let hasJobDescription = false;

// Current user state
let currentUser = null;

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', () => {
    // Check if user is logged in
    checkAuthState();

    // Initialize form elements if they exist
    initializeFormElements();
});

function initializeFormElements() {
    const resumeInput = document.getElementById('resume');
    const dropZone = document.getElementById('dropZone');
    const removeFileBtn = document.getElementById('removeFile');
    const form = document.getElementById('analyzeForm');
    const newAnalysisBtn = document.getElementById('newAnalysisBtn');

    if (resumeInput) {
        resumeInput.addEventListener('change', handleFileSelect);
    }

    if (removeFileBtn) {
        removeFileBtn.addEventListener('click', clearFile);
    }

    if (dropZone) {
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            if (e.dataTransfer.files.length) {
                resumeInput.files = e.dataTransfer.files;
                handleFileSelect();
            }
        });
    }

    if (form) {
        form.addEventListener('submit', handleFormSubmit);
    }

    if (newAnalysisBtn) {
        newAnalysisBtn.addEventListener('click', startNewAnalysis);
    }
}

// ==================== AUTH STATE ====================
function checkAuthState() {
    const savedUser = localStorage.getItem('resumize_user');
    if (savedUser) {
        currentUser = JSON.parse(savedUser);
        updateUIForLoggedInUser();
    } else {
        updateUIForLoggedOutUser();
    }
}

function updateUIForLoggedInUser() {
    // Update navbar
    const navButtons = document.querySelector('.nav-buttons');
    const navUser = document.getElementById('navUser');
    const userUsername = document.getElementById('userUsername');

    if (navButtons) navButtons.style.display = 'none';
    if (navUser) {
        navUser.style.display = 'flex';
        if (userUsername) userUsername.textContent = currentUser.username || currentUser.name;
    }

    // Show analyze content, hide login required
    const loginRequired = document.getElementById('loginRequired');
    const analyzeContent = document.getElementById('analyzeContent');

    if (loginRequired) loginRequired.style.display = 'none';
    if (analyzeContent) analyzeContent.style.display = 'block';
}

function updateUIForLoggedOutUser() {
    // Update navbar
    const navButtons = document.querySelector('.nav-buttons');
    const navUser = document.getElementById('navUser');

    if (navButtons) navButtons.style.display = 'flex';
    if (navUser) navUser.style.display = 'none';

    // Hide analyze content, show login required
    const loginRequired = document.getElementById('loginRequired');
    const analyzeContent = document.getElementById('analyzeContent');

    if (loginRequired) loginRequired.style.display = 'block';
    if (analyzeContent) analyzeContent.style.display = 'none';
}

// ==================== MODAL FUNCTIONS ====================
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

function switchModal(fromModalId, toModalId) {
    closeModal(fromModalId);
    setTimeout(() => openModal(toModalId), 100);
}

// Close modal when clicking outside
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        e.target.classList.remove('active');
        document.body.style.overflow = '';
    }
});

// Close modal with Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal.active').forEach(modal => {
            modal.classList.remove('active');
        });
        document.body.style.overflow = '';
    }
});

// ==================== AUTH HANDLERS ====================
async function handleLogin(event) {
    event.preventDefault();

    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;

    try {
        const response = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Login failed');
        }

        const data = await response.json();
        currentUser = data.user;
        localStorage.setItem('resumize_user', JSON.stringify(currentUser));
        localStorage.setItem('resumize_token', data.token);

        closeModal('loginModal');
        updateUIForLoggedInUser();

        // Scroll to analyze section
        scrollToAnalyze();

    } catch (error) {
        alert(`Login failed: ${error.message}`);
    }
}

async function handleSignup(event) {
    event.preventDefault();

    const name = document.getElementById('signupName').value;
    const username = document.getElementById('signupUsername').value;
    const email = document.getElementById('signupEmail').value;
    const password = document.getElementById('signupPassword').value;

    try {
        const response = await fetch(`${API_URL}/auth/signup`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name, username, email, password })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Signup failed');
        }

        const data = await response.json();
        currentUser = data.user;
        localStorage.setItem('resumize_user', JSON.stringify(currentUser));
        localStorage.setItem('resumize_token', data.token);

        closeModal('signupModal');
        updateUIForLoggedInUser();

        // Scroll to analyze section
        scrollToAnalyze();

    } catch (error) {
        alert(`Signup failed: ${error.message}`);
    }
}

function logout() {
    currentUser = null;
    localStorage.removeItem('resumize_user');
    localStorage.removeItem('resumize_token');
    updateUIForLoggedOutUser();

    // Reset form and results if visible
    const form = document.getElementById('analyzeForm');
    const results = document.getElementById('results');
    if (form) {
        form.reset();
        form.style.display = 'block';
    }
    if (results) {
        results.style.display = 'none';
    }
    clearFile();
}

async function handleForgotPassword(event) {
    event.preventDefault();

    const email = document.getElementById('forgotEmail').value;

    try {
        const response = await fetch(`${API_URL}/auth/forgot-password`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to send reset link');
        }

        alert('Password reset link sent to your email!');
        closeModal('forgotPasswordModal');
        openModal('loginModal');

    } catch (error) {
        // For now, show success message anyway (since we don't have email service)
        alert('If an account exists with this email, you will receive a password reset link.');
        closeModal('forgotPasswordModal');
        openModal('loginModal');
    }
}

// ==================== FAQ TOGGLE ====================
function toggleFaq(button) {
    const faqItem = button.parentElement;
    const isActive = faqItem.classList.contains('active');

    // Close all FAQ items
    document.querySelectorAll('.faq-item').forEach(item => {
        item.classList.remove('active');
    });

    // Open clicked item if it wasn't active
    if (!isActive) {
        faqItem.classList.add('active');
    }
}

// ==================== SCROLL FUNCTION ====================
function scrollToAnalyze() {
    const analyzeSection = document.getElementById('analyzeSection');
    if (analyzeSection) {
        analyzeSection.scrollIntoView({ behavior: 'smooth' });
    }
}

// ==================== FILE HANDLING ====================
function handleFileSelect() {
    const resumeInput = document.getElementById('resume');
    const fileName = document.getElementById('fileName');
    const dropZone = document.getElementById('dropZone');
    const fileSelected = document.getElementById('fileSelected');

    if (resumeInput && resumeInput.files.length > 0) {
        const file = resumeInput.files[0];
        if (fileName) fileName.textContent = file.name;
        const uploadContent = dropZone?.querySelector('.file-upload-content');
        if (uploadContent) uploadContent.style.display = 'none';
        if (fileSelected) fileSelected.style.display = 'flex';
    }
}

function clearFile() {
    const resumeInput = document.getElementById('resume');
    const dropZone = document.getElementById('dropZone');
    const fileSelected = document.getElementById('fileSelected');

    if (resumeInput) resumeInput.value = '';
    const uploadContent = dropZone?.querySelector('.file-upload-content');
    if (uploadContent) uploadContent.style.display = 'block';
    if (fileSelected) fileSelected.style.display = 'none';
}

// ==================== FORM SUBMISSION ====================
async function handleFormSubmit(e) {
    e.preventDefault();

    const resumeInput = document.getElementById('resume');
    const submitBtn = document.getElementById('submitBtn');
    const btnText = submitBtn?.querySelector('.btn-text');
    const btnLoading = submitBtn?.querySelector('.btn-loading');

    if (!resumeInput?.files[0]) {
        alert('Please select a resume file');
        return;
    }

    const formData = new FormData();
    formData.append('resume', resumeInput.files[0]);
    formData.append('job_description', document.getElementById('jobDescription')?.value || '');

    const jobTitle = document.getElementById('jobTitle')?.value;
    if (jobTitle) {
        formData.append('job_title', jobTitle);
    }

    // Show loading state
    if (submitBtn) submitBtn.disabled = true;
    if (btnText) btnText.style.display = 'none';
    if (btnLoading) btnLoading.style.display = 'inline';

    try {
        const response = await fetch(`${API_URL}/analyze`, {
            method: 'POST',
            body: formData,
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('resumize_token') || ''}`
            }
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Analysis failed');
        }

        const data = await response.json();
        displayResults(data);

    } catch (error) {
        alert(`Error: ${error.message}`);
    } finally {
        if (submitBtn) submitBtn.disabled = false;
        if (btnText) btnText.style.display = 'inline';
        if (btnLoading) btnLoading.style.display = 'none';
    }
}

// ==================== START NEW ANALYSIS ====================
function startNewAnalysis() {
    const form = document.getElementById('analyzeForm');
    const results = document.getElementById('results');

    if (form) {
        form.reset();
        form.style.display = 'block';
    }
    if (results) {
        results.style.display = 'none';
    }
    clearFile();
}

// Get score class based on value
function getScoreClass(score) {
    if (score >= 70) return 'high';
    if (score >= 40) return 'medium';
    return 'low';
}

// ==================== DISPLAY RESULTS ====================
function displayResults(data) {
    const { analysis } = data;
    const form = document.getElementById('analyzeForm');
    const results = document.getElementById('results');

    // Top Stats
    const overallScore = analysis.section_analysis?.overall_score || analysis.match_score;
    const overallScoreEl = document.getElementById('overallScore');
    const overallScoreBar = document.getElementById('overallScoreBar');

    if (overallScoreEl) overallScoreEl.textContent = `${overallScore}%`;
    if (overallScoreBar) overallScoreBar.style.width = `${overallScore}%`;

    if (analysis.section_analysis) {
        const totalSections = document.getElementById('totalSections');
        const totalImprovements = document.getElementById('totalImprovements');

        if (totalSections) totalSections.textContent = analysis.section_analysis.total_sections;
        if (totalImprovements) totalImprovements.textContent = analysis.section_analysis.total_improvements;

        // Store sections data
        sectionsData = analysis.section_analysis.sections;

        // Render sidebar section list
        const sectionList = document.getElementById('sectionList');
        if (sectionList) {
            sectionList.innerHTML = sectionsData.map((section, index) => {
                const scoreClass = getScoreClass(section.score);
                const icon = sectionIcons[section.name] || '📋';

                return `
                    <div class="section-item" data-index="${index}" onclick="showSectionDetail(${index})">
                        <div class="section-item-left">
                            <span class="section-item-icon">${icon}</span>
                            <span class="section-item-name">${escapeHtml(section.name)}</span>
                        </div>
                        <span class="section-item-score ${scoreClass}">${section.score}%</span>
                    </div>
                `;
            }).join('');
        }

        // Show first section by default
        showSectionDetail(0);
    }

    // AI Summary
    const scoreJustification = document.getElementById('scoreJustification');
    if (scoreJustification) {
        scoreJustification.textContent = analysis.match_justification;
    }

    // Check if job description was provided (based on ATS breakdown)
    hasJobDescription = analysis.ats_score?.breakdown?.skill_match?.matched_skills?.length > 0 ||
                  analysis.ats_score?.breakdown?.keyword_match?.total_keywords > 0;

    // Store skills and bullets data for section detail display
    matchedSkillsData = analysis.ats_score?.breakdown?.skill_match?.matched_skills || [];
    missingSkillsData = analysis.missing_skills || [];
    rewrittenBulletsData = analysis.rewritten_bullets || [];

    // Show results, hide form
    if (form) form.style.display = 'none';
    if (results) results.style.display = 'block';

    // Scroll to results
    results?.scrollIntoView({ behavior: 'smooth' });
}

// Show section detail in right panel
function showSectionDetail(index) {
    const section = sectionsData[index];
    if (!section) return;

    const scoreClass = getScoreClass(section.score);
    const icon = sectionIcons[section.name] || '📋';

    // Update active state in sidebar
    document.querySelectorAll('.section-item').forEach((item, i) => {
        item.classList.toggle('active', i === index);
    });

    // Build detail HTML
    const detailPanel = document.getElementById('analysisDetail');

    let issuesHtml = '';
    if (section.issues.length > 0) {
        issuesHtml = `
            <div class="detail-block">
                <div class="detail-block-header">
                    <span class="icon">⚠️</span>
                    <span>Issues Found</span>
                </div>
                ${section.issues.map(issue => `
                    <div class="issue-item">
                        <span class="icon">✗</span>
                        <p>${escapeHtml(issue)}</p>
                    </div>
                `).join('')}
            </div>
        `;
    }

    let improvementsHtml = '';
    if (section.improvements.length > 0) {
        improvementsHtml = `
            <div class="detail-block">
                <div class="detail-block-header">
                    <span class="icon">💡</span>
                    <span>Suggestions for Improvement</span>
                </div>
                ${section.improvements.map(imp => `
                    <div class="suggestion-item">
                        <span class="icon">→</span>
                        <p>${escapeHtml(imp)}</p>
                    </div>
                `).join('')}
            </div>
        `;
    }

    let goodHtml = '';
    if (section.issues.length === 0 && section.improvements.length === 0) {
        goodHtml = `
            <div class="detail-block">
                <div class="good-item">
                    <span class="icon">✓</span>
                    <p>This section looks great! No issues or improvements needed.</p>
                </div>
            </div>
        `;
    }

    // Add section-specific content
    let sectionSpecificHtml = '';

    // Skills section: show matched and missing skills
    if (section.name === 'Skills') {
        sectionSpecificHtml = buildSkillsDetailHtml();
    }

    // Work Experience section: show optimized bullet points
    if (section.name === 'Work Experience') {
        sectionSpecificHtml = buildBulletsDetailHtml();
    }

    if (detailPanel) {
        detailPanel.innerHTML = `
            <div class="detail-section-header">
                <span class="detail-section-icon">${icon}</span>
                <div class="detail-section-info">
                    <h3>${escapeHtml(section.name)}</h3>
                    <span class="score-badge ${scoreClass}">${section.score}% Score</span>
                </div>
            </div>
            ${issuesHtml}
            ${improvementsHtml}
            ${goodHtml}
            ${sectionSpecificHtml}
        `;
    }
}

// Build HTML for skills detail (matched and missing skills)
function buildSkillsDetailHtml() {
    let html = '';

    // Matched Skills
    if (hasJobDescription && matchedSkillsData.length > 0) {
        html += `
            <div class="detail-block">
                <div class="detail-block-header">
                    <span class="icon">✓</span>
                    <span>Matched Skills</span>
                </div>
                <div class="skills-list matched-skills">
                    ${matchedSkillsData.map(skill => `<span class="skill-tag">${escapeHtml(skill)}</span>`).join('')}
                </div>
            </div>
        `;
    }

    // Missing Skills / Improvement Areas
    if (missingSkillsData.length > 0) {
        const title = hasJobDescription ? 'Missing Skills' : 'Improvement Areas';
        const desc = hasJobDescription ? 'Add these to your resume if applicable' : 'General recommendations to strengthen your resume';
        html += `
            <div class="detail-block">
                <div class="detail-block-header">
                    <span class="icon">📝</span>
                    <span>${title}</span>
                </div>
                <p class="section-description">${desc}</p>
                <div class="skills-list">
                    ${missingSkillsData.map(skill => `<span class="skill-tag">${escapeHtml(skill)}</span>`).join('')}
                </div>
            </div>
        `;
    } else if (hasJobDescription) {
        html += `
            <div class="detail-block">
                <div class="good-item">
                    <span class="icon">✓</span>
                    <p>No critical skills missing!</p>
                </div>
            </div>
        `;
    }

    return html;
}

// Build HTML for optimized bullet points
function buildBulletsDetailHtml() {
    if (rewrittenBulletsData.length === 0) {
        return '';
    }

    return `
        <div class="detail-block">
            <div class="detail-block-header">
                <span class="icon">✨</span>
                <span>Optimized Bullet Points</span>
            </div>
            <p class="section-description">Copy these ATS-friendly bullets to your resume</p>
            <div class="bullets-list">
                ${rewrittenBulletsData.map(bullet => `
                    <div class="bullet-item">
                        <div class="bullet-original">${escapeHtml(bullet.original)}</div>
                        <div class="bullet-rewritten">${escapeHtml(bullet.rewritten)}</div>
                        <div class="bullet-keywords">
                            ${bullet.keywords_used.map(kw => `<span class="keyword-tag">${escapeHtml(kw)}</span>`).join('')}
                        </div>
                        <button class="copy-btn" onclick="copyToClipboard('${escapeHtml(bullet.rewritten).replace(/'/g, "\\'")}')">
                            Copy bullet
                        </button>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

// ==================== UTILITY FUNCTIONS ====================
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        alert('Copied to clipboard!');
    }).catch(err => {
        console.error('Failed to copy:', err);
    });
}
