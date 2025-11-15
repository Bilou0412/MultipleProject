// Configuration de l'API
const API_URL = 'http://localhost:8000';

// Éléments DOM
const jobUrlDisplay = document.getElementById('job-url');
const cvFileInput = document.getElementById('cv-file');
const fileNameDisplay = document.getElementById('file-name');
const llmSelect = document.getElementById('llm-select');
const pdfSelect = document.getElementById('pdf-select');
const generateBtn = document.getElementById('generate-btn');
const statusDiv = document.getElementById('status');
const loadingDiv = document.getElementById('loading');
const mainContent = document.getElementById('main-content');
const noUrlMessage = document.getElementById('no-url-message');

let currentUrl = '';
let cvId = null;
const clearCvBtn = document.getElementById('clear-cv-btn');

// 🔥 Réception de l'URL envoyée par popup.js
chrome.runtime.onMessage.addListener((message) => {
    if (message.type === "JOB_URL") {
        const url = message.url;

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
    }
});

// 🔥 NE PAS récupérer l’URL via chrome.tabs.query → interdit
document.addEventListener('DOMContentLoaded', async () => {
    loadPreferences();

    // 🔥 Récupérer le CV sauvegardé
    chrome.storage.local.get(['savedCvId'], (result) => {
        if (result.savedCvId) {
            cvId = result.savedCvId;

            fileNameDisplay.textContent = "📄 CV déjà uploadé";
            // Afficher le bouton de suppression lorsque un CV est présent
            if (clearCvBtn) {
                clearCvBtn.style.display = 'block';
            }
        }
    });
});

// Vérifier si l'URL est une offre d'emploi
function isJobOfferUrl(url) {
    const jobPatterns = [
        /welcometothejungle\.com\/.*\/jobs\/.*/,
        /linkedin\.com\/jobs\/.*/,
        /indeed\.fr\/.*\/viewjob.*/
    ];
    return jobPatterns.some(pattern => pattern.test(url));
}

// Upload du CV
cvFileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (!file.name.endsWith('.pdf')) {
        showStatus('error', 'Le CV doit être un fichier PDF');
        return;
    }

    fileNameDisplay.textContent = `✅ ${file.name}`;
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
            cvId = data.cv_id;
            chrome.storage.local.set({ savedCvId: cvId });
            showStatus('success', 'CV uploadé avec succès !');
            setTimeout(() => hideStatus(), 2000);
        } else {
            showStatus('error', data.detail);
            cvId = null;
        }
    } catch (error) {
        showStatus('error', error.message);
        cvId = null;
    }
});

// Sauvegarde des préférences
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

// Génération de la lettre
generateBtn.addEventListener('click', async () => {
    if (!cvId) {
        showStatus('error', 'Veuillez uploader votre CV');
        return;
    }

    if (!currentUrl) {
        showStatus('error', 'URL de l\'offre non détectée');
        return;
    }

    generateBtn.disabled = true;
    loadingDiv.style.display = 'block';
    hideStatus();

    try {
        const formData = new FormData();
        formData.append('cv_id', cvId);
        formData.append('job_url', currentUrl);
        formData.append('llm_provider', llmSelect.value);
        formData.append('pdf_generator', pdfSelect.value);

        const response = await fetch(`${API_URL}/generate-cover-letter`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            showStatus('success', 'Lettre générée !');

            chrome.tabs.create({
                url: `${API_URL}/download/${data.file_id}`
            });
            // NOTE: ne plus nettoyer automatiquement le CV après génération.
            // L'utilisateur peut supprimer son CV explicitement via le bouton "Supprimer le CV".
        } else {
            showStatus('error', data.detail);
        }
    } catch (error) {
        showStatus('error', error.message);
    } finally {
        generateBtn.disabled = false;
        loadingDiv.style.display = 'none';
    }
});

// Nettoyage
async function cleanupFiles() {
    if (!cvId) return;
    try {
        const response = await fetch(`${API_URL}/cleanup/${cvId}`, { method: 'DELETE' });
        if (response.ok) {
            // Supprimer l'ID stocké côté extension
            chrome.storage.local.remove(['savedCvId'], () => {});
            cvId = null;
            fileNameDisplay.textContent = '';
            if (clearCvBtn) clearCvBtn.style.display = 'none';
            showStatus('success', 'CV supprimé du serveur');
        } else {
            try {
                const data = await response.json();
                showStatus('error', data.detail || 'Erreur lors du nettoyage');
            } catch (e) {
                showStatus('error', 'Erreur lors du nettoyage');
            }
        }
    } catch (error) {
        console.error(error);
        showStatus('error', error.message);
    }
}

// Gestion du bouton "Supprimer le CV"
if (clearCvBtn) {
    clearCvBtn.addEventListener('click', async () => {
        // Confirmer l'action
        const confirmDelete = confirm('Supprimer définitivement le CV du serveur ?');
        if (!confirmDelete) return;
        await cleanupFiles();
    });
}

function showStatus(type, message) {
    statusDiv.className = `status ${type}`;
    statusDiv.textContent = message;
}

function hideStatus() {
    statusDiv.style.display = 'none';
}


