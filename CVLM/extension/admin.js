// Configuration API
const API_URL = 'http://localhost:8000';

// État global
let currentUser = null;
let allUsers = [];
let allPromoCodes = [];

// Initialisation
document.addEventListener('DOMContentLoaded', async () => {
    await checkAdminAccess();
    if (currentUser && currentUser.is_admin) {
        await loadDashboard();
        setupEventListeners();
    }
});

// Vérification accès admin
async function checkAdminAccess() {
    const loadingScreen = document.getElementById('loading-screen');
    const accessDenied = document.getElementById('access-denied');
    const adminContent = document.getElementById('admin-content');
    
    try {
        const token = await getAuthToken();
        if (!token) {
            showAccessDenied();
            return;
        }
        
        // Récupérer info utilisateur via endpoint /user/credits
        const response = await fetch(`${API_URL}/user/credits`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) {
            showAccessDenied();
            return;
        }
        
        // Vérifier si admin via endpoint stats (qui vérifie les droits)
        const statsResponse = await fetch(`${API_URL}/admin/stats`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (statsResponse.status === 403) {
            showAccessDenied();
            return;
        }
        
        if (!statsResponse.ok) {
            throw new Error('Erreur lors de la vérification des droits');
        }
        
        // L'utilisateur est admin
        currentUser = { is_admin: true, token };
        loadingScreen.style.display = 'none';
        adminContent.style.display = 'block';
        
    } catch (error) {
        console.error('Erreur vérification admin:', error);
        showAccessDenied();
    }
    
    function showAccessDenied() {
        loadingScreen.style.display = 'none';
        accessDenied.style.display = 'block';
    }
}

// Récupération du token
async function getAuthToken() {
    return new Promise((resolve) => {
        chrome.storage.local.get(['authToken'], (result) => {
            resolve(result.authToken || null);
        });
    });
}

// Chargement du dashboard
async function loadDashboard() {
    await Promise.all([
        loadStats(),
        loadUsers(),
        loadPromoCodes()
    ]);
}

// Chargement des statistiques
async function loadStats() {
    try {
        const response = await fetch(`${API_URL}/admin/stats`, {
            headers: { 'Authorization': `Bearer ${currentUser.token}` }
        });
        
        if (!response.ok) throw new Error('Erreur chargement stats');
        
        const stats = await response.json();
        document.getElementById('stat-users').textContent = stats.total_users;
        document.getElementById('stat-admins').textContent = stats.total_admins;
        document.getElementById('stat-promo-codes').textContent = stats.total_promo_codes;
        document.getElementById('stat-redemptions').textContent = stats.total_promo_redemptions;
        
    } catch (error) {
        console.error('Erreur stats:', error);
    }
}

// Chargement des utilisateurs
async function loadUsers() {
    const tbody = document.getElementById('users-tbody');
    
    try {
        const response = await fetch(`${API_URL}/admin/users`, {
            headers: { 'Authorization': `Bearer ${currentUser.token}` }
        });
        
        if (!response.ok) throw new Error('Erreur chargement utilisateurs');
        
        allUsers = await response.json();
        renderUsers();
        
    } catch (error) {
        console.error('Erreur utilisateurs:', error);
        tbody.innerHTML = '<tr><td colspan="6" style="color:red;text-align:center;">Erreur chargement</td></tr>';
    }
}

// Affichage des utilisateurs
function renderUsers() {
    const tbody = document.getElementById('users-tbody');
    
    if (allUsers.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;">Aucun utilisateur</td></tr>';
        return;
    }
    
    tbody.innerHTML = allUsers.map(user => `
        <tr>
            <td>${user.email}</td>
            <td>${user.name}</td>
            <td><span style="color:#667eea;font-weight:600;">${user.pdf_credits}</span></td>
            <td><span style="color:#764ba2;font-weight:600;">${user.text_credits}</span></td>
            <td>
                <span class="badge ${user.is_admin ? 'badge-admin' : 'badge-user'}">
                    ${user.is_admin ? '👑 Admin' : '👤 User'}
                </span>
            </td>
            <td>
                ${!user.is_admin ? `
                    <button class="btn-warning" data-action="promote" data-user-id="${user.id}">↗️ Promouvoir</button>
                ` : `
                    <button class="btn-danger" data-action="revoke" data-user-id="${user.id}">↙️ Rétrograder</button>
                `}
                <button class="btn-success" data-action="edit-credits" data-user-id="${user.id}">💰 Crédits</button>
            </td>
        </tr>
    `).join('');
}

// Chargement des codes promo
async function loadPromoCodes() {
    const tbody = document.getElementById('promo-codes-tbody');
    
    try {
        const response = await fetch(`${API_URL}/admin/promo-codes`, {
            headers: { 'Authorization': `Bearer ${currentUser.token}` }
        });
        
        if (!response.ok) throw new Error('Erreur chargement codes promo');
        
        allPromoCodes = await response.json();
        renderPromoCodes();
        
    } catch (error) {
        console.error('Erreur codes promo:', error);
        tbody.innerHTML = '<tr><td colspan="7" style="color:red;text-align:center;">Erreur chargement</td></tr>';
    }
}

// Affichage des codes promo
function renderPromoCodes() {
    const tbody = document.getElementById('promo-codes-tbody');
    
    if (allPromoCodes.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;">Aucun code promo</td></tr>';
        return;
    }
    
    tbody.innerHTML = allPromoCodes.map(promo => `
        <tr>
            <td><strong>${promo.code}</strong></td>
            <td>${promo.pdf_credits}</td>
            <td>${promo.text_credits}</td>
            <td>${promo.current_uses} / ${promo.max_uses === 0 ? '∞' : promo.max_uses}</td>
            <td>
                <span class="badge ${promo.is_active ? 'badge-active' : 'badge-inactive'}">
                    ${promo.is_active ? '✅ Actif' : '❌ Inactif'}
                </span>
            </td>
            <td>${promo.expires_at ? new Date(promo.expires_at).toLocaleDateString('fr-FR') : 'Jamais'}</td>
            <td>
                <button class="btn-warning" data-action="toggle-promo" data-code="${promo.code}">
                    ${promo.is_active ? '⏸️ Désactiver' : '▶️ Activer'}
                </button>
                <button class="btn-danger" data-action="delete-promo" data-code="${promo.code}">🗑️</button>
            </td>
        </tr>
    `).join('');
}

// Event listeners
function setupEventListeners() {
    // Gestion des onglets
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const tabName = tab.dataset.tab;
            
            // Désactiver tous les onglets
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            // Activer l'onglet sélectionné
            tab.classList.add('active');
            document.getElementById(`tab-${tabName}`).classList.add('active');
        });
    });
    
    // Délégation d'événements pour les boutons de la table utilisateurs
    document.getElementById('users-tbody').addEventListener('click', (e) => {
        const button = e.target.closest('button');
        if (!button) return;
        
        const action = button.dataset.action;
        const userId = button.dataset.userId;
        
        if (action === 'promote') {
            promoteUser(userId);
        } else if (action === 'revoke') {
            revokeAdmin(userId);
        } else if (action === 'edit-credits') {
            showEditCredits(userId);
        }
    });
    
    // Délégation d'événements pour les boutons de la table codes promo
    document.getElementById('promo-codes-tbody').addEventListener('click', (e) => {
        const button = e.target.closest('button');
        if (!button) return;
        
        const action = button.dataset.action;
        const code = button.dataset.code;
        
        if (action === 'toggle-promo') {
            togglePromoCode(code);
        } else if (action === 'delete-promo') {
            deletePromoCode(code);
        }
    });
    
    // Bouton créer code promo
    document.getElementById('create-promo-btn').addEventListener('click', createPromoCode);
}

// Promouvoir utilisateur
async function promoteUser(userId) {
    if (!confirm('Promouvoir cet utilisateur en administrateur ?')) return;
    
    try {
        const response = await fetch(`${API_URL}/admin/users/promote`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentUser.token}`
            },
            body: JSON.stringify({ user_id: userId })
        });
        
        if (!response.ok) throw new Error('Erreur promotion');
        
        await loadDashboard();
        alert('Utilisateur promu avec succès !');
        
    } catch (error) {
        console.error('Erreur:', error);
        alert('Erreur lors de la promotion');
    }
}

// Révoquer admin
async function revokeAdmin(userId) {
    if (!confirm('Retirer les droits administrateur à cet utilisateur ?')) return;
    
    try {
        const response = await fetch(`${API_URL}/admin/users/revoke`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentUser.token}`
            },
            body: JSON.stringify({ user_id: userId })
        });
        
        if (!response.ok) throw new Error('Erreur révocation');
        
        await loadDashboard();
        alert('Droits retirés avec succès !');
        
    } catch (error) {
        console.error('Erreur:', error);
        alert('Erreur lors de la révocation');
    }
}

// Modifier crédits
function showEditCredits(userId) {
    const user = allUsers.find(u => u.id === userId);
    if (!user) return;
    
    const pdfCredits = prompt(`Crédits PDF pour ${user.email}\nActuel: ${user.pdf_credits}\nNouveau:`, user.pdf_credits);
    if (pdfCredits === null) return;
    
    const textCredits = prompt(`Crédits Texte pour ${user.email}\nActuel: ${user.text_credits}\nNouveau:`, user.text_credits);
    if (textCredits === null) return;
    
    updateUserCredits(userId, parseInt(pdfCredits), parseInt(textCredits));
}

// Mise à jour crédits
async function updateUserCredits(userId, pdfCredits, textCredits) {
    try {
        const response = await fetch(`${API_URL}/admin/users/credits`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentUser.token}`
            },
            body: JSON.stringify({
                user_id: userId,
                pdf_credits: pdfCredits,
                text_credits: textCredits,
                operation: 'set'
            })
        });
        
        if (!response.ok) throw new Error('Erreur mise à jour crédits');
        
        await loadDashboard();
        alert('Crédits mis à jour avec succès !');
        
    } catch (error) {
        console.error('Erreur:', error);
        alert('Erreur lors de la mise à jour des crédits');
    }
}

// Créer code promo
async function createPromoCode() {
    const pdfCredits = parseInt(document.getElementById('create-pdf-credits').value);
    const textCredits = parseInt(document.getElementById('create-text-credits').value);
    const maxUses = parseInt(document.getElementById('create-max-uses').value);
    const daysValid = document.getElementById('create-days-valid').value;
    const customCode = document.getElementById('create-custom-code').value.trim().toUpperCase();
    
    const messageDiv = document.getElementById('create-message');
    
    try {
        const body = {
            pdf_credits: pdfCredits,
            text_credits: textCredits,
            max_uses: maxUses
        };
        
        if (daysValid) body.days_valid = parseInt(daysValid);
        if (customCode) body.custom_code = customCode;
        
        const response = await fetch(`${API_URL}/promo/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentUser.token}`
            },
            body: JSON.stringify(body)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erreur génération');
        }
        
        const result = await response.json();
        
        messageDiv.textContent = `✅ Code créé avec succès: ${result.code}`;
        messageDiv.className = 'message success';
        messageDiv.style.display = 'block';
        
        // Réinitialiser le formulaire
        document.getElementById('create-custom-code').value = '';
        
        // Recharger les codes promo
        await loadPromoCodes();
        await loadStats();
        
        setTimeout(() => {
            messageDiv.style.display = 'none';
        }, 5000);
        
    } catch (error) {
        console.error('Erreur:', error);
        messageDiv.textContent = `❌ ${error.message}`;
        messageDiv.className = 'message error';
        messageDiv.style.display = 'block';
    }
}

// Toggle code promo
async function togglePromoCode(code) {
    try {
        const response = await fetch(`${API_URL}/admin/promo-codes/${code}/toggle`, {
            method: 'PATCH',
            headers: { 'Authorization': `Bearer ${currentUser.token}` }
        });
        
        if (!response.ok) throw new Error('Erreur toggle');
        
        await loadPromoCodes();
        await loadStats();
        
    } catch (error) {
        console.error('Erreur:', error);
        alert('Erreur lors de la modification du code');
    }
}

// Supprimer code promo
async function deletePromoCode(code) {
    if (!confirm(`Supprimer définitivement le code ${code} ?`)) return;
    
    try {
        const response = await fetch(`${API_URL}/admin/promo-codes/${code}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${currentUser.token}` }
        });
        
        if (!response.ok) throw new Error('Erreur suppression');
        
        await loadPromoCodes();
        await loadStats();
        alert('Code supprimé avec succès !');
        
    } catch (error) {
        console.error('Erreur:', error);
        alert('Erreur lors de la suppression');
    }
}
