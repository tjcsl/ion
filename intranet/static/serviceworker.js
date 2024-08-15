
async function getSilentPreference() {
    return new Promise((resolve, reject) => {
        const dbRequest = indexedDB.open("notificationPreferences", 1);

        dbRequest.onupgradeneeded = function(event) {
            const db = event.target.result;
            db.createObjectStore("preferences", { keyPath: "id" });
        };

        dbRequest.onsuccess = function(event) {
            const db = event.target.result;
            const transaction = db.transaction(["preferences"], "readonly");
            const store = transaction.objectStore("preferences");
            const request = store.get("silentNotification");

            request.onsuccess = function() {
                if (request.result && request.result.silent) {
                    resolve(request.result.silent);
                } else {
                    resolve(false);
                }
            };

            request.onerror = function() {
                resolve(false);
            };
        };

        dbRequest.onerror = function() {
            resolve(false);
        };
    });
}

self.addEventListener("push", function(event) {
    const data = event.data.json();
    let options = {
        body: data.body,
        icon: data.icon,
        badge: data.badge,
        data: {
            url: data.data.url
        },
    };

    getSilentPreference().then(function (silent) {
        options["silent"] = silent;
        self.registration.showNotification(data.title, options).then((r) => {});
    })
});

// Immediately replace any old service worker(s)
self.addEventListener("install", function (event) {
  self.skipWaiting();
});

self.addEventListener("notificationclick", function(event) {
    event.notification.close();
    event.waitUntil(
        // eslint-disable-next-line no-undef
        clients.openWindow(event.notification.data.url)
    );
});

// Update subscription details on server on expiration

self.addEventListener("pushsubscriptionchange", function(event) {
  event.waitUntil(
    fetch("/api/notifications/webpush/update_subscription", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        "old_registration_id": event.oldSubscription.endpoint,
        "registration_id": event.newSubscription.endpoint,
        "p256dh": btoa(
            String.fromCharCode.apply(
                null, new Uint8Array(event.newSubscription.getKey("p256dh"))
            )
        ),
        "auth": btoa(
            String.fromCharCode.apply(
                null, new Uint8Array(event.newSubscription.getKey("auth"))
            )
        ),
      })
    })
  );
});
