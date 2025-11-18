// Importer la configuration depuis config.js
// L'URL API est maintenant définie dans config.js selon l'environnement

// Auth Elements
const authSection = document.getElementById('auth-section');
const mainApp = document.getElementById('main-app');
const googleSigninBtn = document.getElementById('google-signin-btn');
const signoutBtn = document.getElementById('signout-btn');
const userAvatar = document.getElementById('user-avatar');
const userName = document.getElementById('user-name');
const userEmail = document.getElementById('user-email');

// UI Elements
const jobUrlDisplay = document.getElementById('job-url');
const cvFileInput = document.getElementById('cv-file');
const cvListContainer = document.getElementById('cv-list');
const insertBtn = document.getElementById('insert-btn');
const loadingDiv = document.getElementById('loading');
const statusDiv = document.getElementById('status');
const noUrlMessage = document.getElementById('no-url-message');
const mainContent = document.getElementById('main-content');
const pdfSelect = document.getElementById('pdf-select');
const refreshLettersBtn = document.getElementById('refresh-letters-btn');

let currentUrl = '';
let selectedCvId = null;
let authToken = null;
let currentUser = null;

// === Authentification Google ===

async function initAuth() {
    const stored = await chrome.storage.local.get(['authToken', 'userProfile']);
    
    if (stored.authToken && stored.userProfile) {
        authToken = stored.authToken;
        currentUser = stored.userProfile;
        showMainApp();
    } else {
        showAuthSection();
    }
}

function showAuthSection() {
    authSection.style.display = 'block';
    mainApp.style.display = 'none';
}

function showMainApp() {
    authSection.style.display = 'none';
    mainApp.style.display = 'block';
    
    // Afficher le profil utilisateur
    if (currentUser) {
        userName.textContent = currentUser.name || 'Utilisateur';
        userEmail.textContent = currentUser.email || '';
        userAvatar.src = currentUser.picture || 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"%3E%3Cpath fill="%232563eb" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/%3E%3C/svg%3E';
    }
    
    // Charger le reste de l'interface
    init();
}

googleSigninBtn.addEventListener('click', async () => {
    try {
        googleSigninBtn.disabled = true;
        googleSigninBtn.innerHTML = '<span>⏳</span> Connexion...';
        
        // Obtenir le token Google via chrome.identity
        const token = await new Promise((resolve, reject) => {
            chrome.identity.getAuthToken({ interactive: true }, (token) => {
                if (chrome.runtime.lastError) {
                    reject(new Error(chrome.runtime.lastError.message));
                } else {
                    resolve(token);
                }
            });
        });
        
        // Envoyer le token à notre backend pour validation et JWT
        const response = await fetch(`${API_URL}/auth/google`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ google_token: token })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erreur d\'authentification');
        }
        
        const data = await response.json();
        
        // Stocker le token JWT et le profil
        authToken = data.access_token;
        currentUser = data.user;
        
        await chrome.storage.local.set({
            authToken: authToken,
            userProfile: currentUser
        });
        
        showMainApp();
    } catch (error) {
        console.error('Erreur authentification:', error);
        alert('Erreur de connexion: ' + error.message);
        googleSigninBtn.disabled = false;
        googleSigninBtn.innerHTML = '<span>🔑</span> Se connecter avec Google';
    }
});

signoutBtn.addEventListener('click', async () => {
    // Révoquer le token Google
    chrome.identity.getAuthToken({ interactive: false }, (token) => {
        if (token) {
            chrome.identity.removeCachedAuthToken({ token }, () => {
                console.log('✅ Token Google révoqué');
            });
        }
    });
    
    // Nettoyer le storage
    await chrome.storage.local.remove(['authToken', 'userProfile', 'selectedCvId']);
    
    authToken = null;
    currentUser = null;
    selectedCvId = null;
    
    showAuthSection();
});

// === Initialisation principale ===

async function init() {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (tabs[0]?.url) {
            currentUrl = tabs[0].url;
            const isJobPage = /welcometothejungle\.com\/.*\/jobs\/.*|linkedin\.com\/jobs\/.*|indeed\.fr\/.*\/viewjob.*/.test(currentUrl);
            
            if (isJobPage) {
                jobUrlDisplay.textContent = currentUrl;
                mainContent.style.display = 'block';
                noUrlMessage.style.display = 'none';
            } else {
                mainContent.style.display = 'none';
                noUrlMessage.style.display = 'flex';
            }
        }
    });
    
    chrome.storage.local.get(['selectedCvId'], (result) => {
        selectedCvId = result.selectedCvId || null;
    });
    
    loadPreferences();
    await loadCredits(); // Charger les crédits
    await loadCvList();
    await loadLettersList();
}

// === Charger les crédits utilisateur ===
async function loadCredits() {
    try {
        const response = await fetch(`${API_URL}/user/credits`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const credits = await response.json();
            document.getElementById('pdf-credits').textContent = credits.pdf_credits;
            document.getElementById('text-credits').textContent = credits.text_credits;
            
            // Afficher un avertissement si crédits bas
            if (credits.pdf_credits <= 2 || credits.text_credits <= 2) {
                const creditsDisplay = document.getElementById('credits-display');
                creditsDisplay.style.background = 'linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)';
                creditsDisplay.style.borderColor = '#fbbf24';
            }
            
            // Marquer comme épuisé si 0
            if (credits.pdf_credits === 0 || credits.text_credits === 0) {
                const creditsDisplay = document.getElementById('credits-display');
                creditsDisplay.style.background = 'linear-gradient(135deg, #fee2e2 0%, #fecaca 100%)';
                creditsDisplay.style.borderColor = '#ef4444';
            }
        }
    } catch (error) {
        console.error('Erreur chargement crédits:', error);
    }
}

// === Bouton Rafraîchir les lettres ===

if (refreshLettersBtn) {
    refreshLettersBtn.addEventListener('click', async () => {
        refreshLettersBtn.style.animation = 'spin 0.5s linear';
        await loadLettersList();
        setTimeout(() => {
            refreshLettersBtn.style.animation = '';
        }, 500);
    });
}

// === Upload CV ===

cvFileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (!file.type.includes('pdf')) {
        showStatus('error', 'Le fichier doit être un PDF.');
        return;
    }

    const formData = new FormData();
    formData.append('cv_file', file);

    try {
        showStatus('info', 'Upload en cours...');
        
        const headers = authToken ? { 'Authorization': `Bearer ${authToken}` } : {};
        
        const response = await fetch(`${API_URL}/upload-cv`, {
            method: 'POST',
            headers,
            body: formData
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || `Erreur ${response.status}`);
        }

        const data = await response.json();
        selectedCvId = data.cv_id;
        chrome.storage.local.set({ selectedCvId });

        showStatus('success', `✅ ${file.name} uploadé !`);
        setTimeout(() => hideStatus(), 2000);
        
        await loadCvList();
    } catch (error) {
        showStatus('error', `❌ Erreur upload: ${error.message}`);
    }
    cvFileInput.value = '';
});

// === Liste des CVs ===

async function loadCvList() {
    try {
        const headers = authToken ? { 'Authorization': `Bearer ${authToken}` } : {};
        
        const response = await fetch(`${API_URL}/list-cvs`, { headers });
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

// === Liste des lettres générées ===

async function loadLettersList() {
    const lettersListContainer = document.getElementById('letters-list');
    
    try {
        const headers = authToken ? { 'Authorization': `Bearer ${authToken}` } : {};
        
        console.log('🔍 Chargement des lettres...');
        const response = await fetch(`${API_URL}/list-letters`, { headers });
        const data = await response.json();
        
        console.log('📬 Réponse API:', data);
        
        if (!response.ok || !data.letters) {
            console.error('❌ Erreur réponse:', response.status, data);
            lettersListContainer.innerHTML = '<div class="letters-empty">Aucune lettre générée</div>';
            return;
        }

        if (data.letters.length === 0) {
            console.log('ℹ️ Aucune lettre trouvée');
            lettersListContainer.innerHTML = '<div class="letters-empty">📝 Vous n\'avez pas encore généré de lettre.<br>Commencez dès maintenant !</div>';
            return;
        }

        console.log(`✅ ${data.letters.length} lettre(s) trouvée(s)`);
        lettersListContainer.innerHTML = data.letters.map(letter => {
            const jobTitle = extractJobTitle(letter.job_offer_url);
            return `
                <div class="letter-item">
                    <div class="letter-header">
                        <div>
                            <div class="letter-title">${jobTitle}</div>
                            <div class="letter-meta">
                                <span>📄 ${letter.cv_filename}</span>
                                <span>📅 ${formatDate(letter.created_at)}</span>
                                ${letter.job_offer_url ? `<span title="${letter.job_offer_url}" style="cursor: help;">🔗 Offre en ligne</span>` : ''}
                            </div>
                        </div>
                        <button class="letter-download" data-letter-id="${letter.letter_id}">
                            ⬇️ PDF
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        // Ajouter les event listeners pour télécharger
        lettersListContainer.querySelectorAll('.letter-download').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const letterId = e.target.dataset.letterId;
                await downloadLetter(letterId);
            });
        });

        // Event listener pour afficher l'URL complète au clic
        lettersListContainer.querySelectorAll('.letter-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (!e.target.classList.contains('letter-download')) {
                    const url = item.querySelector('[title]')?.getAttribute('title');
                    if (url) {
                        chrome.tabs.create({ url });
                    }
                }
            });
        });
    } catch (error) {
        console.error('Erreur chargement lettres:', error);
        lettersListContainer.innerHTML = '<div class="letters-empty" style="color: var(--error);">❌ Erreur de chargement</div>';
    }
}

async function downloadLetter(letterId) {
    try {
        const headers = authToken ? { 'Authorization': `Bearer ${authToken}` } : {};
        
        const response = await fetch(`${API_URL}/download-letter/${letterId}`, { headers });
        
        if (!response.ok) {
            throw new Error('Erreur de téléchargement');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `lettre_motivation_${letterId}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        showStatus('success', 'Lettre téléchargée');
    } catch (error) {
        console.error('Erreur téléchargement lettre:', error);
        showStatus('error', 'Erreur de téléchargement');
    }
}

function extractJobTitle(url) {
    if (!url) return 'Lettre de motivation';
    
    // Extraire le titre depuis l'URL
    try {
        const urlObj = new URL(url);
        const pathParts = urlObj.pathname.split('/').filter(p => p);
        
        // Pour Welcome to the Jungle: /fr/companies/xxx/jobs/titre-du-poste_xxx
        if (url.includes('welcometothejungle.com')) {
            const jobPart = pathParts[pathParts.length - 1];
            const title = jobPart.split('_')[0].replace(/-/g, ' ');
            return title.charAt(0).toUpperCase() + title.slice(1);
        }
        
        // Pour LinkedIn: /jobs/view/titre-du-poste-xxx
        if (url.includes('linkedin.com')) {
            const title = pathParts[pathParts.length - 1].split('-').slice(0, -1).join(' ');
            return title.charAt(0).toUpperCase() + title.slice(1);
        }
        
        return 'Lettre de motivation';
    } catch {
        return 'Lettre de motivation';
    }
}

async function deleteCv(cvId) {
    try {
        const headers = authToken ? { 'Authorization': `Bearer ${authToken}` } : {};
        
        const response = await fetch(`${API_URL}/cleanup/${cvId}`, { 
            method: 'DELETE',
            headers
        });
        
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

// === Génération de lettre ===

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
            form.append('llm_provider', 'openai'); // Hardcodé OpenAI
            form.append('pdf_generator', pdfSelect.value || 'fpdf');

            const headers = authToken ? { 'Authorization': `Bearer ${authToken}` } : {};

            const response = await fetch(`${API_URL}/generate-cover-letter`, {
                method: 'POST',
                headers,
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
                    // Recharger la liste des lettres et les crédits
                    loadLettersList();
                    loadCredits();
                });
            } else {
                chrome.tabs.create({ url: downloadUrl });
                showStatus('success', 'Lettre générée — ouverture du PDF');
                // Recharger la liste des lettres et les crédits
                loadLettersList();
                loadCredits();
            }
        } catch (error) {
            showStatus('error', error.message || 'Erreur lors de la génération');
        } finally {
            insertBtn.disabled = false;
            loadingDiv.style.display = 'none';
        }
    });
}

// === Utilitaires ===

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

function savePreferences() {
    chrome.storage.local.set({
        pdfGenerator: pdfSelect.value
    });
}

function loadPreferences() {
    chrome.storage.local.get(['pdfGenerator'], (result) => {
        if (result.pdfGenerator) pdfSelect.value = result.pdfGenerator;
    });
}

pdfSelect.addEventListener('change', savePreferences);

function showStatus(type, message) {
    statusDiv.className = `status ${type}`;
    statusDiv.textContent = message;
    statusDiv.style.display = 'block';
}

function hideStatus() {
    statusDiv.style.display = 'none';
}

// === Démarrage ===

document.addEventListener('DOMContentLoaded', initAuth);
