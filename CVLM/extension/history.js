// Configuration
const API_BASE_URL = 'http://localhost:8000';
let currentPage = 1;
let currentFilters = {
    search: '',
    type: '',
    period: 'all'
};

// Initialisation
document.addEventListener('DOMContentLoaded', async () => {
    // Vérifier l'authentification au chargement
    try {
        await getAuthToken();
        // Si authentifié, continuer normalement
        setupEventListeners();
        loadStats();
        loadHistory();
    } catch (error) {
        // Si pas authentifié, afficher un message et un bouton de connexion
        showAuthRequired();
    }
});

// Event Listeners
function setupEventListeners() {
    // Recherche avec debounce
    const searchInput = document.getElementById('searchInput');
    let searchTimeout;
    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            currentFilters.search = e.target.value;
            currentPage = 1;
            loadHistory();
        }, 500);
    });

    // Filtres
    document.getElementById('periodFilter').addEventListener('change', (e) => {
        currentFilters.period = e.target.value;
        currentPage = 1;
        loadHistory();
    });

    document.getElementById('typeFilter').addEventListener('change', (e) => {
        currentFilters.type = e.target.value;
        currentPage = 1;
        loadHistory();
    });

    // Export
    document.getElementById('exportBtn').addEventListener('click', exportHistory);

    // Pagination
    document.getElementById('prevBtn').addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            loadHistory();
        }
    });

    document.getElementById('nextBtn').addEventListener('click', () => {
        currentPage++;
        loadHistory();
    });

    // Modal
    document.getElementById('closeModal').addEventListener('click', closeModal);
    document.getElementById('textModal').addEventListener('click', (e) => {
        if (e.target.id === 'textModal') {
            closeModal();
        }
    });

    // Event delegation pour les boutons d'action
    document.getElementById('historyBody').addEventListener('click', async (e) => {
        const button = e.target.closest('button');
        if (!button) return;

        const action = button.dataset.action;
        const id = button.dataset.id;

        switch (action) {
            case 'download':
                await downloadFile(id);
                break;
            case 'view':
                await viewText(id);
                break;
            case 'delete':
                await deleteEntry(id);
                break;
        }
    });
}

// Chargement des statistiques
async function loadStats() {
    try {
        const token = await getAuthToken();
        const response = await fetch(`${API_BASE_URL}/user/history/stats`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            if (response.status === 401) {
                // Token invalide ou expiré
                chrome.storage.local.remove(['auth_token']);
                window.location.href = chrome.runtime.getURL('generator.html');
                return;
            }
            throw new Error('Erreur lors du chargement des stats');
        }

        const stats = await response.json();
        
        document.getElementById('statTotal').textContent = stats.total || 0;
        document.getElementById('statPdf').textContent = stats.pdf_count || 0;
        document.getElementById('statText').textContent = stats.text_count || 0;
        document.getElementById('statSuccess').textContent = `${stats.success_rate || 0}%`;
        document.getElementById('statMonth').textContent = stats.this_month || 0;
        document.getElementById('statCompanies').textContent = stats.unique_companies || 0;

    } catch (error) {
        console.error('Erreur chargement stats:', error);
        // Si erreur d'authentification, on laisse getAuthToken() gérer la redirection
    }
}

// Chargement de l'historique
async function loadHistory() {
    const loadingState = document.getElementById('loadingState');
    const emptyState = document.getElementById('emptyState');
    const historyTable = document.getElementById('historyTable');
    const pagination = document.getElementById('pagination');

    loadingState.style.display = 'block';
    emptyState.style.display = 'none';
    historyTable.style.display = 'none';
    pagination.style.display = 'none';

    try {
        const token = await getAuthToken();
        
        // Construire l'URL avec les paramètres
        const params = new URLSearchParams({
            page: currentPage,
            per_page: 50
        });

        if (currentFilters.search) {
            params.append('search', currentFilters.search);
        }
        if (currentFilters.type) {
            params.append('type_filter', currentFilters.type);
        }
        if (currentFilters.period !== 'all') {
            params.append('period', currentFilters.period);
        }

        const response = await fetch(`${API_BASE_URL}/user/history?${params}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            if (response.status === 401) {
                // Token invalide ou expiré
                chrome.storage.local.remove(['auth_token']);
                window.location.href = chrome.runtime.getURL('generator.html');
                return;
            }
            throw new Error('Erreur lors du chargement de l\'historique');
        }

        const data = await response.json();

        loadingState.style.display = 'none';

        if (data.total === 0) {
            emptyState.style.display = 'block';
            return;
        }

        // Afficher le tableau
        historyTable.style.display = 'table';
        renderHistoryTable(data.items);

        // Afficher la pagination si nécessaire
        if (data.pages > 1) {
            pagination.style.display = 'flex';
            updatePagination(data.page, data.pages);
        }

    } catch (error) {
        console.error('Erreur chargement historique:', error);
        loadingState.innerHTML = `
            <div style="color: #dc3545;">
                ❌ Erreur lors du chargement de l'historique
            </div>
        `;
    }
}

// Rendu de la table
function renderHistoryTable(items) {
    const tbody = document.getElementById('historyBody');
    tbody.innerHTML = '';

    items.forEach(item => {
        const row = document.createElement('tr');
        
        // Type badge
        const typeBadge = `<span class="type-badge ${item.type}">${item.type.toUpperCase()}</span>`;
        
        // Job info
        const jobTitle = item.job_title || 'Non spécifié';
        const company = item.company_name || 'Non spécifié';
        
        // Date
        const date = new Date(item.created_at);
        const dateStr = date.toLocaleDateString('fr-FR', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });

        // Statut
        let statusBadge = '';
        let expirationInfo = '';
        if (item.is_expired) {
            statusBadge = '<span class="status-badge expired">Expiré</span>';
        } else if (item.status === 'success') {
            statusBadge = '<span class="status-badge success">Succès</span>';
            if (item.type === 'pdf' && item.days_until_expiration !== null) {
                expirationInfo = `<br><span class="expiration-warning">Expire dans ${item.days_until_expiration}j</span>`;
            }
        } else {
            statusBadge = '<span class="status-badge error">Erreur</span>';
        }

        // Actions
        let actions = '<div class="actions">';
        if (item.type === 'pdf' && item.is_downloadable) {
            actions += `<button class="btn btn-primary" data-action="download" data-id="${item.id}">📥 Télécharger</button>`;
        }
        if (item.type === 'text') {
            actions += `<button class="btn btn-secondary" data-action="view" data-id="${item.id}">👁️ Voir</button>`;
        }
        actions += `<button class="btn btn-danger" data-action="delete" data-id="${item.id}">🗑️ Supprimer</button>`;
        actions += '</div>';

        row.innerHTML = `
            <td>${typeBadge}</td>
            <td>
                <strong>${jobTitle}</strong><br>
                <small style="color: #6c757d;">${company}</small>
            </td>
            <td><small>${item.cv_filename || '-'}</small></td>
            <td>
                ${dateStr}
                ${expirationInfo}
            </td>
            <td>${statusBadge}</td>
            <td>${actions}</td>
        `;

        tbody.appendChild(row);
    });
}

// Mise à jour de la pagination
function updatePagination(page, totalPages) {
    document.getElementById('pageInfo').textContent = `Page ${page} sur ${totalPages}`;
    document.getElementById('prevBtn').disabled = page === 1;
    document.getElementById('nextBtn').disabled = page === totalPages;
}

// Télécharger un fichier
async function downloadFile(id) {
    try {
        const token = await getAuthToken();
        const response = await fetch(`${API_BASE_URL}/user/history/${id}/download`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            if (response.status === 410) {
                alert('Ce fichier a expiré (plus de 90 jours). Vous pouvez le régénérer depuis l\'extension.');
            } else {
                throw new Error('Erreur lors du téléchargement');
            }
            return;
        }

        // Extraire le nom du fichier depuis les headers
        const contentDisposition = response.headers.get('content-disposition');
        let filename = 'lettre_motivation.pdf';
        if (contentDisposition) {
            const match = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
            if (match && match[1]) {
                filename = match[1].replace(/['"]/g, '').trim();
            }
        }

        // Télécharger le fichier
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

    } catch (error) {
        console.error('Erreur téléchargement:', error);
        alert('Erreur lors du téléchargement du fichier');
    }
}

// Voir le texte
async function viewText(id) {
    try {
        const token = await getAuthToken();
        const response = await fetch(`${API_BASE_URL}/user/history/${id}/text`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            throw new Error('Erreur lors de la récupération du texte');
        }

        const data = await response.json();
        
        document.getElementById('modalTitle').textContent = 
            `${data.job_title || 'Texte'} - ${data.company_name || ''}`;
        document.getElementById('modalBody').textContent = data.text_content;
        document.getElementById('textModal').classList.add('active');

    } catch (error) {
        console.error('Erreur récupération texte:', error);
        alert('Erreur lors de la récupération du texte');
    }
}

// Fermer le modal
function closeModal() {
    document.getElementById('textModal').classList.remove('active');
}

// Supprimer une entrée
async function deleteEntry(id) {
    if (!confirm('Êtes-vous sûr de vouloir supprimer cette entrée ? Cette action est irréversible.')) {
        return;
    }

    try {
        const token = await getAuthToken();
        const response = await fetch(`${API_BASE_URL}/user/history/${id}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            throw new Error('Erreur lors de la suppression');
        }

        // Recharger l'historique et les stats
        await loadStats();
        await loadHistory();

        alert('Entrée supprimée avec succès');

    } catch (error) {
        console.error('Erreur suppression:', error);
        alert('Erreur lors de la suppression');
    }
}

// Exporter l'historique
async function exportHistory() {
    try {
        const token = await getAuthToken();
        const response = await fetch(`${API_BASE_URL}/user/history/export`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            throw new Error('Erreur lors de l\'export');
        }

        // Télécharger le JSON
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `cvlm_history_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        alert('Export réussi !');

    } catch (error) {
        console.error('Erreur export:', error);
        alert('Erreur lors de l\'export');
    }
}

// Récupérer le token d'authentification
async function getAuthToken() {
    return new Promise((resolve, reject) => {
        chrome.storage.local.get(['authToken'], (result) => {
            console.log('🔍 Vérification token:', result);
            if (result.authToken) {
                console.log('✅ Token trouvé:', result.authToken.substring(0, 20) + '...');
                resolve(result.authToken);
            } else {
                console.log('❌ Aucun token trouvé');
                reject(new Error('Non authentifié'));
            }
        });
    });
}

// Afficher un message si non authentifié
function showAuthRequired() {
    const container = document.querySelector('.container');
    container.innerHTML = `
        <div class="header">
            <h1>🔒 Authentification Requise</h1>
            <p class="subtitle">Vous devez être connecté pour accéder à l'historique</p>
        </div>
        <div style="text-align: center; padding: 60px 30px; background: white; margin: 20px; border-radius: 15px;">
            <div style="font-size: 4em; margin-bottom: 20px;">🔐</div>
            <h2 style="color: #495057; margin-bottom: 20px;">Connexion nécessaire</h2>
            <p style="color: #6c757d; margin-bottom: 30px; font-size: 1.1em;">
                Pour consulter votre historique de générations, veuillez d'abord vous connecter via l'extension CVLM.
            </p>
            <button id="login-prompt-btn" style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 15px 40px;
                border-radius: 8px;
                font-size: 1.1em;
                font-weight: 600;
                cursor: pointer;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
                transition: transform 0.2s;
            ">
                📱 Ouvrir l'Extension pour se Connecter
            </button>
            <p style="color: #6c757d; margin-top: 20px; font-size: 0.9em;">
                Ou cliquez sur l'icône CVLM dans la barre d'outils de Chrome
            </p>
        </div>
    `;
    
    // Ajouter l'event listener après avoir créé le HTML
    const loginBtn = document.getElementById('login-prompt-btn');
    if (loginBtn) {
        loginBtn.addEventListener('click', () => {
            alert('Cliquez sur l\'icône CVLM dans la barre d\'outils de Chrome pour vous connecter.');
        });
        loginBtn.addEventListener('mouseover', () => {
            loginBtn.style.transform = 'translateY(-2px)';
        });
        loginBtn.addEventListener('mouseout', () => {
            loginBtn.style.transform = 'translateY(0)';
        });
    }
}

// Ouvrir le popup de l'extension
function openExtensionPopup() {
    alert('Cliquez sur l\'icône CVLM dans la barre d\'outils de Chrome pour vous connecter.');
}
