const API_URL = window.location.origin + '/api';

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

// NLP sub-score labels
const nlpLabels = {
    'skill_match': { label: 'Skill Match', icon: '⚡' },
    'keyword_match': { label: 'Keyword Density', icon: '🔑' },
    'experience_alignment': { label: 'Experience', icon: '💼' },
    'formatting': { label: 'Formatting', icon: '📐' }
};

// Store data globally for click handling
let sectionsData = [];
let matchedSkillsData = [];
let missingSkillsData = [];
let rewrittenBulletsData = [];
let hasJobDescription = false;

// Current user state
let currentUser = null;

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', () => {
    checkAuthState();
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
    const navButtons = document.querySelector('.nav-buttons');
    const navUser = document.getElementById('navUser');
    const userUsername = document.getElementById('userUsername');

    if (navButtons) navButtons.style.display = 'none';
    if (navUser) {
        navUser.style.display = 'flex';
        if (userUsername) userUsername.textContent = currentUser.username || currentUser.name;
    }

    const loginRequired = document.getElementById('loginRequired');
    const analyzeContent = document.getElementById('analyzeContent');

    if (loginRequired) loginRequired.style.display = 'none';
    if (analyzeContent) analyzeContent.style.display = 'block';
}

function updateUIForLoggedOutUser() {
    const navButtons = document.querySelector('.nav-buttons');
    const navUser = document.getElementById('navUser');

    if (navButtons) navButtons.style.display = 'flex';
    if (navUser) navUser.style.display = 'none';

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

document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        e.target.classList.remove('active');
        document.body.style.overflow = '';
    }
});

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
            headers: { 'Content-Type': 'application/json' },
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
            headers: { 'Content-Type': 'application/json' },
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
        scrollToAnalyze();
    } catch (error) {
        alert(`Signup failed: ${error.message}`);
    }
}

function logout() {
    const token = localStorage.getItem('resumize_token');
    if (token) {
        fetch(`${API_URL}/auth/logout`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        }).catch(() => {});
    }

    currentUser = null;
    localStorage.removeItem('resumize_user');
    localStorage.removeItem('resumize_token');
    updateUIForLoggedOutUser();

    const form = document.getElementById('analyzeForm');
    const results = document.getElementById('results');
    if (form) { form.reset(); form.style.display = 'block'; }
    if (results) results.style.display = 'none';
    clearFile();
}

async function handleForgotPassword(event) {
    event.preventDefault();
    const email = document.getElementById('forgotEmail').value;

    try {
        await fetch(`${API_URL}/auth/forgot-password`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
        });
    } catch (e) { /* ignore */ }

    alert('If an account exists with this email, you will receive a password reset link.');
    closeModal('forgotPasswordModal');
    openModal('loginModal');
}

// ==================== FAQ TOGGLE ====================
function toggleFaq(button) {
    const faqItem = button.parentElement;
    const isActive = faqItem.classList.contains('active');
    document.querySelectorAll('.faq-item').forEach(item => item.classList.remove('active'));
    if (!isActive) faqItem.classList.add('active');
}

// ==================== SCROLL FUNCTION ====================
function scrollToAnalyze() {
    const analyzeSection = document.getElementById('analyzeSection');
    if (analyzeSection) analyzeSection.scrollIntoView({ behavior: 'smooth' });
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
    if (jobTitle) formData.append('job_title', jobTitle);

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
    if (form) { form.reset(); form.style.display = 'block'; }
    if (results) results.style.display = 'none';
    clearFile();
}

// Get score class
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

    const combined = analysis.combined_score;
    const nlpResult = analysis.nlp_result;
    const genaiResult = analysis.genai_result;
    const sectionAnalysis = analysis.section_analysis;

    // --- Score Circle ---
    const finalScore = combined.final_score;
    const scoreClass = getScoreClass(finalScore);

    const overallScoreEl = document.getElementById('overallScore');
    const scoreCircle = document.getElementById('scoreCircle');
    if (overallScoreEl) overallScoreEl.textContent = `${finalScore}%`;
    if (scoreCircle) scoreCircle.className = `score-circle ${scoreClass}`;

    // --- NLP + GenAI Mini Breakdown ---
    const nlpScoreDisplay = document.getElementById('nlpScoreDisplay');
    if (nlpScoreDisplay) nlpScoreDisplay.textContent = combined.nlp_score;

    const genaiAdjustDisplay = document.getElementById('genaiAdjustDisplay');
    if (genaiAdjustDisplay) {
        const adj = combined.genai_adjustment;
        const sign = adj >= 0 ? '+' : '';
        if (combined.genai_available) {
            genaiAdjustDisplay.innerHTML = `AI: <strong>${sign}${adj}</strong>`;
            genaiAdjustDisplay.style.display = 'inline';
        } else {
            genaiAdjustDisplay.innerHTML = `AI: <strong>N/A</strong>`;
            genaiAdjustDisplay.classList.add('unavailable');
        }
    }

    // --- Confidence Badge ---
    const confidenceBadge = document.getElementById('confidenceBadge');
    if (confidenceBadge) {
        const confLabels = {
            'high': 'High Confidence',
            'moderate': 'Moderate Confidence',
            'low': 'Low Confidence',
            'nlp_only': 'NLP Only'
        };
        confidenceBadge.textContent = confLabels[combined.confidence] || combined.confidence;
        confidenceBadge.className = `confidence-badge confidence-${combined.confidence}`;
    }

    // --- Stats Cards ---
    if (sectionAnalysis) {
        const totalSections = document.getElementById('totalSections');
        const totalImprovements = document.getElementById('totalImprovements');
        if (totalSections) totalSections.textContent = sectionAnalysis.total_sections;
        if (totalImprovements) totalImprovements.textContent = sectionAnalysis.total_improvements;
    }

    // --- NLP Breakdown Bars ---
    const nlpBars = document.getElementById('nlpBars');
    if (nlpBars && nlpResult?.breakdown) {
        const breakdown = nlpResult.breakdown;
        nlpBars.innerHTML = Object.entries(breakdown).map(([key, sub]) => {
            const meta = nlpLabels[key] || { label: key, icon: '📊' };
            const barClass = getScoreClass(sub.score);
            return `
                <div class="nlp-bar-item">
                    <div class="nlp-bar-header">
                        <span class="nlp-bar-label">${meta.icon} ${meta.label}</span>
                        <span class="nlp-bar-score ${barClass}">${sub.score}% <span class="nlp-bar-weight">(${sub.weight}% weight)</span></span>
                    </div>
                    <div class="nlp-bar-track">
                        <div class="nlp-bar-fill ${barClass}" style="width: ${sub.score}%"></div>
                    </div>
                    <p class="nlp-bar-explanation">${escapeHtml(sub.explanation)}</p>
                </div>
            `;
        }).join('');
    }

    // --- GenAI Panel ---
    const genaiPanel = document.getElementById('genaiPanel');
    if (genaiPanel) {
        if (genaiResult && combined.genai_available) {
            genaiPanel.style.display = 'block';

            // Adjustment reason
            const genaiAdjustment = document.getElementById('genaiAdjustment');
            if (genaiAdjustment) {
                const adj = combined.genai_adjustment;
                const sign = adj >= 0 ? '+' : '';
                genaiAdjustment.innerHTML = `
                    <div class="adjustment-summary">
                        <span class="adjustment-value ${adj >= 0 ? 'positive' : 'negative'}">${sign}${adj} points</span>
                        <span class="adjustment-reason">${escapeHtml(genaiResult.adjustment_reason)}</span>
                    </div>
                `;
            }

            // Semantic skills
            const semanticSection = document.getElementById('genaiSemanticSkills');
            const semanticList = document.getElementById('semanticSkillsList');
            if (genaiResult.semantic_skills?.length > 0 && semanticSection && semanticList) {
                semanticSection.style.display = 'block';
                semanticList.innerHTML = genaiResult.semantic_skills
                    .map(s => `<span class="skill-tag semantic">${escapeHtml(s)}</span>`)
                    .join('');
            }

            // Gap analysis
            const gapSection = document.getElementById('genaiGapAnalysis');
            const gapList = document.getElementById('gapAnalysisList');
            if (genaiResult.gap_analysis?.length > 0 && gapSection && gapList) {
                gapSection.style.display = 'block';
                gapList.innerHTML = genaiResult.gap_analysis.map(gap => `
                    <div class="gap-item">
                        <div class="gap-header">
                            <span class="gap-skill">${escapeHtml(gap.skill)}</span>
                            <span class="gap-importance importance-${gap.importance}">${gap.importance}</span>
                        </div>
                        <p class="gap-reason">${escapeHtml(gap.reason)}</p>
                        <p class="gap-suggestion">${escapeHtml(gap.suggestion)}</p>
                    </div>
                `).join('');
            }

            // Positioning advice
            const posSection = document.getElementById('genaiPositioning');
            const posAdvice = document.getElementById('positioningAdvice');
            if (genaiResult.positioning_advice && posSection && posAdvice) {
                posSection.style.display = 'block';
                posAdvice.textContent = genaiResult.positioning_advice;
            }
        } else {
            genaiPanel.style.display = 'none';
        }
    }

    // --- Section Analysis Sidebar ---
    if (sectionAnalysis) {
        sectionsData = sectionAnalysis.sections;

        const sectionList = document.getElementById('sectionList');
        if (sectionList) {
            sectionList.innerHTML = sectionsData.map((section, index) => {
                const sClass = getScoreClass(section.score);
                const icon = sectionIcons[section.name] || '📋';
                return `
                    <div class="section-item" data-index="${index}" onclick="showSectionDetail(${index})">
                        <div class="section-item-left">
                            <span class="section-item-icon">${icon}</span>
                            <span class="section-item-name">${escapeHtml(section.name)}</span>
                        </div>
                        <span class="section-item-score ${sClass}">${section.score}%</span>
                    </div>
                `;
            }).join('');
        }

        showSectionDetail(0);
    }

    // --- AI Justification ---
    const scoreJustification = document.getElementById('scoreJustification');
    if (scoreJustification) {
        scoreJustification.textContent = analysis.match_justification;
    }

    // --- Store skills/bullets data ---
    const skillDetails = nlpResult?.breakdown?.skill_match?.details || {};
    matchedSkillsData = skillDetails.matched || [];
    missingSkillsData = analysis.missing_skills || [];
    rewrittenBulletsData = genaiResult?.rewritten_bullets || [];
    hasJobDescription = matchedSkillsData.length > 0 || missingSkillsData.length > 0;

    // Show results
    if (form) form.style.display = 'none';
    if (results) results.style.display = 'block';
    results?.scrollIntoView({ behavior: 'smooth' });
}

// ==================== SECTION DETAIL ====================
function showSectionDetail(index) {
    const section = sectionsData[index];
    if (!section) return;

    const scoreClass = getScoreClass(section.score);
    const icon = sectionIcons[section.name] || '📋';

    document.querySelectorAll('.section-item').forEach((item, i) => {
        item.classList.toggle('active', i === index);
    });

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

    let sectionSpecificHtml = '';
    if (section.name === 'Skills') sectionSpecificHtml = buildSkillsDetailHtml();
    if (section.name === 'Work Experience') sectionSpecificHtml = buildBulletsDetailHtml();

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

// Build skills detail
function buildSkillsDetailHtml() {
    let html = '';

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

    if (missingSkillsData.length > 0) {
        const title = hasJobDescription ? 'Missing Skills' : 'Improvement Areas';
        const desc = hasJobDescription ? 'Add these to your resume if applicable' : 'General recommendations';
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

// Build bullets detail
function buildBulletsDetailHtml() {
    if (rewrittenBulletsData.length === 0) return '';

    return `
        <div class="detail-block">
            <div class="detail-block-header">
                <span class="icon">✨</span>
                <span>Optimized Bullet Points</span>
                <span class="source-tag ai-tag" style="margin-left: auto; font-size: 0.7rem;">AI-Generated</span>
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
                        <button class="copy-btn" data-copy-text="${escapeHtml(bullet.rewritten)}">
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

// Delegated click handler for copy buttons (avoids inline onclick XSS)
document.addEventListener('click', (e) => {
    const copyBtn = e.target.closest('.copy-btn[data-copy-text]');
    if (copyBtn) {
        copyToClipboard(copyBtn.getAttribute('data-copy-text'));
    }
});
