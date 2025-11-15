chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    const currentUrl = tabs[0]?.url || null;

    chrome.windows.create({
        url: "generator.html",
        type: "popup",
        width: 420,
        height: 650
    }, (window) => {
        // Quand la fenêtre est ouverte, on envoie l'URL
        setTimeout(() => {
            chrome.runtime.sendMessage({
                type: "JOB_URL",
                url: currentUrl
            });
        }, 300);
    });
});
