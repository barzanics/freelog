self.addEventListener('install', (event) => {
    console.log('[ServiceWorker] Installed');
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    console.log('[ServiceWorker] Activated');
    return self.clients.claim();
});

// Listen to messages from the client
self.addEventListener('message', (event) => {
    // checkNotifications({token: event.data.token, url: event.data.url, path_file: event.data.path_file});
    if (event.data && event.data.type === 'GET_VOIP_NOTIFICATIONS') {
        getVoipNotifications({token: event.data.voipToken, url: event.data.voipURL, path_file: event.data.path_file, cas_id: event.data.cas_id, platform: event.data.platform});
    } else if (event.data && event.data.type === 'GET_NOTIFICATIONS') {
        getNotifications({token: event.data.token, url: event.data.notiURL, path_file: event.data.path_file, cas_id: event.data.cas_id, platform: event.data.platform});
    }
});


async function getVoipNotifications({token, url, path_file, cas_id, platform}) {
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': `Bearer ${token}`
            },
            body: `cas_id=${cas_id}&platform=${platform}`
        });

        const data = await response.json();
        if (data.status != '2') {
            alert(data);
        }
        // // Show a notification if needed
        if (data.new && data.new.length > 0) {
            self.registration.showNotification("You have new notifications!", {
                body: `${data.new.length} new items.`,
                icon: '/favicon.ico'
            });
        }

        // // Optionally send data to the client
        const allClients = await self.clients.matchAll({ includeUncontrolled: true });
        for (const client of allClients) {
            client.postMessage({ cas_id, token, type: 'GET_VOIP_NOTIFICATIONS_RESPONSE', data });
        }

    } catch (err) {
        console.error('Notification fetch failed:', err);
    }
}

async function getNotifications({token, url, path_file, cas_id, platform}) {
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: `cas_id=${cas_id}&platform=${platform}&token=${token}`
        });

        const data = await response.json();

        // // Optionally send data to the client
        const allClients = await self.clients.matchAll({ includeUncontrolled: true });
        for (const client of allClients) {
            client.postMessage({ cas_id, token, type: 'GET_NOTIFICATIONS_RESPONSE', data });
        }

    } catch (err) {
        console.error('Notification fetch failed:', err);
    }
}
