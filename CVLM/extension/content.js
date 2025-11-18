console.log('🚀 CVLM: Content script chargé');

// La configuration API_URL est importée via manifest.json depuis config.js
const currentUrl = window.location.href;
const isJobPage = /welcometothejungle\.com\/.*\/jobs\/.*|linkedin\.com\/jobs\/.*|indeed\.fr\/.*\/viewjob.*/.test(currentUrl);

if (isJobPage) {
    detectMotivationLetterFields();
}

function detectMotivationLetterFields() {
    const selectors = [
        'textarea[name*="cover"]',
        'textarea[name*="motivation"]',
        'textarea[name*="letter"]',
        'textarea[id*="cover"]',
        'textarea[id*="motivation"]',
        'textarea[placeholder*="motivation"]',
        'textarea[placeholder*="lettre"]',
        'textarea[name="cover_letter"]',
        'textarea#cover_letter'
    ];
    
    const textareas = new Set();
    selectors.forEach(selector => {
        try {
            document.querySelectorAll(selector).forEach(textarea => textareas.add(textarea));
        } catch (e) {
            console.error('Erreur sélecteur:', selector, e);
        }
    });
    
    console.log(`🔍 CVLM: ${textareas.size} zone(s) de texte détectée(s)`);
    textareas.forEach((textarea, index) => addInsertButton(textarea, index + 1));
}

function addInsertButton(textarea, index) {
    if (textarea.dataset.cvlmButtonAdded) return;
    
    textarea.dataset.cvlmButtonAdded = 'true';
    
    const buttonContainer = document.createElement('div');
    buttonContainer.style.cssText = 'margin-top: 8px; text-align: right;';
    
    const button = document.createElement('button');
    button.type = 'button';
    button.innerHTML = '📄 Insérer ma lettre CVLM';
    button.style.cssText = `
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    `;
    
    button.addEventListener('mouseenter', () => {
        button.style.transform = 'translateY(-2px)';
        button.style.boxShadow = '0 4px 12px rgba(102, 126, 234, 0.4)';
    });
    
    button.addEventListener('mouseleave', () => {
        button.style.transform = 'translateY(0)';
        button.style.boxShadow = 'none';
    });
    
    button.addEventListener('click', async () => {
        const pageUrl = window.location.href;
        const result = await chrome.storage.local.get(['lastGeneratedLetter', 'lastGeneratedUrl']);
        const lastUrl = result?.lastGeneratedUrl;
        const lastText = result?.lastGeneratedLetter;

        if (lastText && lastUrl && lastUrl === pageUrl) {
            textarea.value = lastText;
            textarea.dispatchEvent(new Event('input', { bubbles: true }));
            textarea.dispatchEvent(new Event('change', { bubbles: true }));

            button.innerHTML = '✅ Lettre insérée !';
            button.style.background = '#28a745';
            setTimeout(() => {
                button.innerHTML = '📄 Insérer ma lettre CVLM';
                button.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
            }, 1600);
            return;
        }

        const originalHTML = button.innerHTML;
        const originalBackground = button.style.background;

        // Vérifier qu'un CV est sélectionné
        const cvRes = await chrome.storage.local.get(['selectedCvId']);
        const cv_id = cvRes?.selectedCvId || null;

        if (!cv_id) {
            button.innerHTML = '⚠️ Veuillez d\'abord sélectionner un CV';
            button.style.background = '#f59e0b';
            setTimeout(() => {
                button.innerHTML = originalHTML;
                button.style.background = originalBackground;
            }, 2500);
            return;
        }

        button.disabled = true;
        button.innerHTML = '⏳ Génération en cours...';

        try {
            const payload = {
                job_url: pageUrl,
                cv_id: cv_id,
                llm_provider: 'openai',
                text_type: 'why_join'
            };

            // Récupérer le token JWT depuis le storage
            const storage = await chrome.storage.local.get(['authToken']);
            const headers = { 'Content-Type': 'application/json' };
            
            if (storage.authToken) {
                headers['Authorization'] = `Bearer ${storage.authToken}`;
            }

            const resp = await fetch(`${API_URL}/generate-text`, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(payload)
            });

            if (!resp.ok) {
                const errorData = await resp.json().catch(() => ({}));
                throw new Error(errorData.detail || `Erreur API: ${resp.status}`);
            }

            const data = await resp.json();
            const generated = data?.text || '';

            if (generated) {
                chrome.storage.local.set({ lastGeneratedLetter: generated, lastGeneratedUrl: pageUrl });
                textarea.value = generated;
                textarea.dispatchEvent(new Event('input', { bubbles: true }));
                textarea.dispatchEvent(new Event('change', { bubbles: true }));
            }
        } catch (err) {
            console.error('Erreur génération:', err);
            button.innerHTML = '❌ Erreur: ' + (err.message || 'Erreur inconnue');
            button.style.background = '#ef4444';
            setTimeout(() => {
                button.innerHTML = originalHTML;
                button.style.background = originalBackground;
            }, 3000);
            return;
        } finally {
            button.disabled = false;
            button.innerHTML = '✅ Lettre insérée !';
            button.style.background = '#28a745';
            setTimeout(() => {
                button.innerHTML = originalHTML;
                button.style.background = originalBackground;
            }, 1600);
        }
    });
    
    buttonContainer.appendChild(button);
    textarea.parentNode.insertBefore(buttonContainer, textarea.nextSibling);
    console.log(`✅ CVLM: Bouton d'insertion ajouté pour zone #${index}`);
}

const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
        if (mutation.addedNodes.length) detectMotivationLetterFields();
    });
});

setTimeout(() => {
    observer.observe(document.body, { childList: true, subtree: true });
    console.log('👀 CVLM: Observation du DOM activée');
}, 1000);

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request?.action === 'insertLastGeneratedLetter') {
        const text = request.text || '';
        let target = null;
        const active = document.activeElement;
        
        if (active && (active.tagName === 'TEXTAREA' || 
            (active.tagName === 'INPUT' && (active.type === 'text' || active.type === 'search')))) {
            target = active;
        }

        if (!target) {
            const selectors = [
                'textarea[name*="cover"]', 'textarea[name*="motivation"]', 'textarea[name*="letter"]',
                'textarea[id*="cover"]', 'textarea[id*="motivation"]',
                'textarea[placeholder*="motivation"]', 'textarea[placeholder*="lettre"]',
                'textarea[name="cover_letter"]', 'textarea#cover_letter'
            ];

            for (const sel of selectors) {
                try {
                    const el = document.querySelector(sel);
                    if (el) { target = el; break; }
                } catch (e) {}
            }
        }

        if (!target) {
            sendResponse({ status: 'error', error: 'no_textarea_found' });
            return;
        }

        try {
            target.focus();
            target.value = text;
            target.dispatchEvent(new Event('input', { bubbles: true }));
            target.dispatchEvent(new Event('change', { bubbles: true }));

            const oldOutline = target.style.outline;
            target.style.outline = '3px solid rgba(102,126,234,0.25)';
            setTimeout(() => { target.style.outline = oldOutline; }, 1600);

            sendResponse({ status: 'ok' });
        } catch (err) {
            console.error('Erreur insertion:', err);
            sendResponse({ status: 'error', error: 'insertion_failed' });
        }
    }
});