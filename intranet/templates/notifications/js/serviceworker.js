// This file is in a templates directory so it can be served from root. Check intranet/urls.py for more info

self.addEventListener("push", function(event) {
    const data = event.data.json();

    const options = {
        body: data.body,
        icon: data.icon,
        badge: data.badge,
        data: {
            url: data.data.url
        }
    };

    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
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