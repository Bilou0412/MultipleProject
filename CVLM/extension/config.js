// Configuration API selon l'environnement
const CONFIG = {
    // Détecter automatiquement l'environnement
    isDevelopment: () => {
        // En dev, on est sur une page locale ou l'extension n'est pas packagée
        return !('update_url' in chrome.runtime.getManifest());
    },
    
    getApiUrl: () => {
        if (CONFIG.isDevelopment()) {
            return 'http://localhost:8000';
        }
        // En production, utiliser la variable d'environnement ou valeur par défaut
        // À mettre à jour lors du build pour production
        return 'https://api.ton-domaine.com';  // TODO: Remplacer par ton domaine
    }
};

// Export de l'URL API
const API_URL = CONFIG.getApiUrl();

// Log pour debugging (seulement en dev)
if (CONFIG.isDevelopment()) {
    console.log('🔧 Mode développement - API:', API_URL);
}
