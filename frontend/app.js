const API_URL = 'http://localhost:8000/api';

// DOM Elements
const form = document.getElementById('analyzeForm');
const resumeInput = document.getElementById('resume');
const dropZone = document.getElementById('dropZone');
const fileSelected = document.getElementById('fileSelected');
const fileName = document.getElementById('fileName');
const removeFileBtn = document.getElementById('removeFile');
const submitBtn = document.getElementById('submitBtn');
const btnText = submitBtn.querySelector('.btn-text');
const btnLoading = submitBtn.querySelector('.btn-loading');
const results = document.getElementById('results');
const newAnalysisBtn = document.getElementById('newAnalysisBtn');

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

// File upload handling
resumeInput.addEventListener('change', handleFileSelect);
removeFileBtn.addEventListener('click', clearFile);

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

function handleFileSelect() {
    if (resumeInput.files.length > 0) {
        const file = resumeInput.files[0];
        fileName.textContent = file.name;
        dropZone.querySelector('.file-upload-content').style.display = 'none';
        fileSelected.style.display = 'flex';
    }
}

function clearFile() {
    resumeInput.value = '';
    dropZone.querySelector('.file-upload-content').style.display = 'block';
    fileSelected.style.display = 'none';
}

// Form submission
form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = new FormData();
    formData.append('resume', resumeInput.files[0]);
    formData.append('job_description', document.getElementById('jobDescription').value);

    const jobTitle = document.getElementById('jobTitle').value;
    if (jobTitle) {
        formData.append('job_title', jobTitle);
    }

    // Show loading state
    submitBtn.disabled = true;
    btnText.style.display = 'none';
    btnLoading.style.display = 'inline';

    try {
        const response = await fetch(`${API_URL}/analyze`, {
            method: 'POST',
            body: formData
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
        submitBtn.disabled = false;
        btnText.style.display = 'inline';
        btnLoading.style.display = 'none';
    }
});

// Get score class based on value
function getScoreClass(score) {
    if (score >= 70) return 'high';
    if (score >= 40) return 'medium';
    return 'low';
}

// Store sections data globally for click handling
let sectionsData = [];

// Display results
function displayResults(data) {
    const { analysis } = data;

    // Top Stats
    const overallScore = analysis.section_analysis?.overall_score || analysis.match_score;
    document.getElementById('overallScore').textContent = `${overallScore}%`;
    document.getElementById('overallScoreBar').style.width = `${overallScore}%`;

    if (analysis.section_analysis) {
        document.getElementById('totalSections').textContent = analysis.section_analysis.total_sections;
        document.getElementById('totalImprovements').textContent = analysis.section_analysis.total_improvements;

        // Store sections data
        sectionsData = analysis.section_analysis.sections;

        // Render sidebar section list
        const sectionList = document.getElementById('sectionList');
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

        // Show first section by default
        showSectionDetail(0);
    }

    // AI Summary
    document.getElementById('scoreJustification').textContent = analysis.match_justification;

    // Check if job description was provided (based on ATS breakdown)
    const hasJD = analysis.ats_score?.breakdown?.skill_match?.matched_skills?.length > 0 ||
                  analysis.ats_score?.breakdown?.keyword_match?.total_keywords > 0;

    // Update titles based on whether JD was provided
    const matchedSkillsTitle = document.getElementById('matchedSkillsTitle');
    const matchedSkillsCard = document.getElementById('matchedSkillsCard');
    const missingSkillsTitle = document.getElementById('missingSkillsTitle');
    const missingSkillsDesc = document.getElementById('missingSkillsDesc');

    if (hasJD) {
        matchedSkillsTitle.textContent = 'Matched Skills';
        missingSkillsTitle.textContent = 'Missing Skills';
        missingSkillsDesc.textContent = 'Add these to your resume if applicable';
        matchedSkillsCard.style.display = 'block';
    } else {
        matchedSkillsTitle.textContent = 'Detected Skills';
        missingSkillsTitle.textContent = 'Improvement Areas';
        missingSkillsDesc.textContent = 'General recommendations to strengthen your resume';
        matchedSkillsCard.style.display = 'none'; // Hide matched skills when no JD
    }

    // Matched Skills (from ATS breakdown)
    const matchedSkills = document.getElementById('matchedSkills');
    if (analysis.ats_score?.breakdown?.skill_match?.matched_skills?.length > 0) {
        matchedSkills.innerHTML = analysis.ats_score.breakdown.skill_match.matched_skills
            .map(skill => `<span class="skill-tag">${escapeHtml(skill)}</span>`)
            .join('');
    } else {
        matchedSkills.innerHTML = '<p style="color: var(--text-muted);">No skills matched</p>';
    }

    // Missing skills / Improvement Areas
    const missingSkills = document.getElementById('missingSkills');
    if (analysis.missing_skills.length > 0) {
        missingSkills.innerHTML = analysis.missing_skills
            .map(skill => `<span class="skill-tag">${escapeHtml(skill)}</span>`)
            .join('');
    } else {
        missingSkills.innerHTML = hasJD
            ? '<p style="color: var(--success);">No critical skills missing!</p>'
            : '<p style="color: var(--success);">Resume looks good for general ATS compatibility!</p>';
    }

    // Rewritten bullets
    const rewrittenBullets = document.getElementById('rewrittenBullets');
    rewrittenBullets.innerHTML = analysis.rewritten_bullets.map(bullet => `
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
    `).join('');

    // Show results, hide form
    form.style.display = 'none';
    results.style.display = 'block';

    // Scroll to results
    results.scrollIntoView({ behavior: 'smooth' });
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
    `;
}

// New analysis
newAnalysisBtn.addEventListener('click', () => {
    form.reset();
    clearFile();
    results.style.display = 'none';
    form.style.display = 'block';
});

// Utility functions
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
