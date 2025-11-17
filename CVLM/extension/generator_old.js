const API_URL = 'http://localhost:8000';

const jobUrlDisplay = document.getElementById('job-url');
const cvFileInput = document.getElementById('cv-file');
const cvListContainer = document.getElementById('cv-list');
const llmSelect = document.getElementById('llm-select');
const pdfSelect = document.getElementById('pdf-select');
const insertBtn = document.getElementById('insert-btn');
const statusDiv = document.getElementById('status');
const loadingDiv = document.getElementById('loading');
const mainContent = document.getElementById('main-content');
const noUrlMessage = document.getElementById('no-url-message');

let currentUrl = '';
let selectedCvId = null;

document.addEventListener('DOMContentLoaded', async () => {
    loadPreferences();
    loadCvList();

    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        const url = tabs[0]?.url || '';
        
        if (url && isJobOfferUrl(url)) {
            jobUrlDisplay.textContent = url;
            mainContent.style.display = "block";
            noUrlMessage.style.display = "none";
            currentUrl = url;
        } else {
            jobUrlDisplay.textContent = "Aucune URL détectée";
            mainContent.style.display = "none";
            noUrlMessage.style.display = "block";
        }
    });

    chrome.storage.local.get(['selectedCvId'], (result) => {
        if (result.selectedCvId) {
            selectedCvId = result.selectedCvId;
        }
    });
});

function isJobOfferUrl(url) {
    return /welcometothejungle\.com\/.*\/jobs\/.*|linkedin\.com\/jobs\/.*|indeed\.fr\/.*\/viewjob.*/.test(url);
}

cvFileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (!file.name.endsWith('.pdf')) {
        showStatus('error', 'Le CV doit être un fichier PDF');
        return;
    }

    showStatus('info', 'Upload du CV en cours...');

    try {
        const formData = new FormData();
        formData.append('cv_file', file);

        const response = await fetch(`${API_URL}/upload-cv`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            selectedCvId = data.cv_id;
            chrome.storage.local.set({ selectedCvId: data.cv_id });
            showStatus('success', 'CV uploadé avec succès !');
            await loadCvList();
            setTimeout(() => hideStatus(), 2000);
        } else {
            showStatus('error', data.detail);
        }
    } catch (error) {
        showStatus('error', error.message);
    }
    cvFileInput.value = '';
});

async function loadCvList() {
    try {
        const response = await fetch(`${API_URL}/list-cvs`);
        const data = await response.json();
        
        if (!response.ok || !data.cvs) {
            cvListContainer.innerHTML = '<p style="color: #6b7280; font-size: 13px; text-align: center;">Aucun CV disponible</p>';
            return;
        }

        if (data.cvs.length === 0) {
            cvListContainer.innerHTML = '<p style="color: #6b7280; font-size: 13px; text-align: center;">Aucun CV uploadé</p>';
            return;
        }

        cvListContainer.innerHTML = data.cvs.map(cv => `
            <div class="cv-item ${cv.cv_id === selectedCvId ? 'selected' : ''}" data-cv-id="${cv.cv_id}">
                <div class="cv-info">
                    <input type="radio" name="cv-select" value="${cv.cv_id}" ${cv.cv_id === selectedCvId ? 'checked' : ''}>
                    <div class="cv-details">
                        <div class="cv-name">${cv.filename}</div>
                        <div class="cv-meta">${formatFileSize(cv.file_size)} • ${formatDate(cv.upload_date)}</div>
                    </div>
                </div>
                <button class="cv-delete" data-cv-id="${cv.cv_id}" title="Supprimer">✕</button>
            </div>
        `).join('');

        cvListContainer.querySelectorAll('input[name="cv-select"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                selectedCvId = e.target.value;
                chrome.storage.local.set({ selectedCvId });
                loadCvList();
            });
        });

        cvListContainer.querySelectorAll('.cv-delete').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const cvId = e.target.dataset.cvId;
                if (confirm('Supprimer définitivement ce CV ?')) {
                    await deleteCv(cvId);
                }
            });
        });
    } catch (error) {
        console.error('Erreur chargement CVs:', error);
        cvListContainer.innerHTML = '<p style="color: #ef4444; font-size: 13px;">Erreur de chargement</p>';
    }
}

async function deleteCv(cvId) {
    try {
        const response = await fetch(`${API_URL}/cleanup/${cvId}`, { method: 'DELETE' });
        if (response.ok) {
            if (selectedCvId === cvId) {
                selectedCvId = null;
                chrome.storage.local.remove(['selectedCvId']);
            }
            showStatus('success', 'CV supprimé');
            await loadCvList();
            setTimeout(() => hideStatus(), 2000);
        } else {
            const data = await response.json().catch(() => ({}));
            showStatus('error', data.detail || 'Erreur lors de la suppression');
        }
    } catch (error) {
        showStatus('error', error.message);
    }
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function formatDate(isoDate) {
    const date = new Date(isoDate);
    const now = new Date();
    const diff = now - date;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (minutes < 1) return 'À l\'instant';
    if (minutes < 60) return `Il y a ${minutes}min`;
    if (hours < 24) return `Il y a ${hours}h`;
    if (days < 7) return `Il y a ${days}j`;
    return date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
}

llmSelect.addEventListener('change', savePreferences);
pdfSelect.addEventListener('change', savePreferences);

function savePreferences() {
    chrome.storage.local.set({
        llmProvider: llmSelect.value,
        pdfGenerator: pdfSelect.value
    });
}

function loadPreferences() {
    chrome.storage.local.get(['llmProvider', 'pdfGenerator'], (result) => {
        if (result.llmProvider) llmSelect.value = result.llmProvider;
        if (result.pdfGenerator) pdfSelect.value = result.pdfGenerator;
    });
}

if (insertBtn) {
    insertBtn.addEventListener('click', async () => {
        if (!currentUrl) {
            showStatus('error', 'Aucune URL d\'offre détectée.');
            return;
        }

        if (!selectedCvId) {
            showStatus('error', 'Veuillez sélectionner un CV.');
            return;
        }

        insertBtn.disabled = true;
        loadingDiv.style.display = 'block';
        hideStatus();

        try {
            const form = new FormData();
            form.append('cv_id', selectedCvId);
            form.append('job_url', currentUrl);
            form.append('llm_provider', llmSelect.value || 'openai');
            form.append('pdf_generator', pdfSelect.value || 'fpdf');

            const response = await fetch(`${API_URL}/generate-cover-letter`, {
                method: 'POST',
                body: form
            });

            if (!response.ok) {
                const err = await response.json().catch(() => ({}));
                throw new Error(err.detail || `Erreur serveur ${response.status}`);
            }

            const data = await response.json();
            const generated = data && data.letter_text;

            if (generated) {
                chrome.storage.local.set({ lastGeneratedLetter: generated, lastGeneratedUrl: currentUrl });
            }

            const downloadUrl = (data.download_url && data.download_url.startsWith('http')) 
                ? data.download_url 
                : `${API_URL}${data.download_url}`;

            if (chrome.downloads && chrome.downloads.download) {
                chrome.downloads.download({
                    url: downloadUrl,
                    filename: `lettre_${data.file_id}.pdf`,
                    conflictAction: 'overwrite'
                }, (downloadId) => {
                    if (chrome.runtime.lastError) {
                        chrome.tabs.create({ url: downloadUrl });
                        showStatus('info', 'Génération terminée — ouverture du PDF');
                    } else {
                        showStatus('success', 'Lettre générée et téléchargement lancé !');
                    }
                });
            } else {
                chrome.tabs.create({ url: downloadUrl });
                showStatus('success', 'Lettre générée — ouverture du PDF');
            }
        } catch (error) {
            showStatus('error', error.message || 'Erreur lors de la génération');
        } finally {
            insertBtn.disabled = false;
            loadingDiv.style.display = 'none';
        }
    });
}

function showStatus(type, message) {
    statusDiv.className = `status ${type}`;
    statusDiv.textContent = message;
    statusDiv.style.display = 'block';
}

function hideStatus() {
    statusDiv.style.display = 'none';
}