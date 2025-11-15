// Script de contenu pour ajouter un bouton flottant sur les pages d'offres d'emploi

// Créer le bouton flottant
function createFloatingButton() {
    const button = document.createElement('div');
    button.id = 'cvlm-floating-button';
    button.innerHTML = `
        <div class="cvlm-btn-icon">📄</div>
        <span class="cvlm-btn-text">Générer lettre</span>
    `;
    
    button.addEventListener('click', () => {
        chrome.runtime.sendMessage({ action: 'openPopup' });
    });
    
    document.body.appendChild(button);
}

// Vérifier si on est sur une page d'offre d'emploi
const currentUrl = window.location.href;
const isJobPage = /welcometothejungle\.com\/.*\/jobs\/.*|linkedin\.com\/jobs\/.*|indeed\.fr\/.*\/viewjob.*/.test(currentUrl);

if (isJobPage) {
    createFloatingButton();
    
    // Notifier le background script
    chrome.runtime.sendMessage({
        action: 'jobPageDetected',
        url: currentUrl
    });
}