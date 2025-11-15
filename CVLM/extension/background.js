// Background Service Worker pour l'extension CVLM
console.log('🚀 CVLM Extension - Service Worker activé');

// Écouter les messages depuis les content scripts et popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('Message reçu:', request);
  
  if (request.action === 'jobPageDetected') {
    console.log('✅ Page d\'offre d\'emploi détectée:', request.url);
    
    // Optionnel: Afficher une notification
    // chrome.notifications.create({
    //   type: 'basic',
    //   iconUrl: 'icons/icon48.png',
    //   title: 'CVLM',
    //   message: 'Offre d\'emploi détectée ! Cliquez sur l\'extension pour générer votre lettre.'
    // });
  }
  
  if (request.action === 'openPopup') {
    // Ouvrir le popup programmatiquement
    chrome.action.openPopup();
  }
  
  // Toujours retourner true pour les réponses asynchrones
  return true;
});

// Gérer les événements d'installation
chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === 'install') {
    console.log('🎉 Extension CVLM installée pour la première fois');
    
    // Ouvrir une page de bienvenue (optionnel)
    // chrome.tabs.create({
    //   url: 'https://votre-site.com/bienvenue'
    // });
  } else if (details.reason === 'update') {
    console.log('🔄 Extension CVLM mise à jour');
  }
});

// Gérer le clic sur l'icône de l'extension
chrome.action.onClicked.addListener((tab) => {
  console.log('🖱️ Clic sur l\'icône CVLM');
  // Le popup s'ouvrira automatiquement grâce à default_popup dans manifest.json
});