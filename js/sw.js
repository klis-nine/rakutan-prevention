self.addEventListener('push', function(event) {
    const options = {
        body: event.data.text(),
        icon: 'icon.png',
        vibrate: [200, 100, 200],
        tag: 'class-notification'
    };
    event.waitUntil(
        self.registration.showNotification('授業が始まります！', options)
    );
});
