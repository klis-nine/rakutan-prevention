self.addEventListener('push', function(event) {
    const options = {
        body: 'アラームの時間になりました！',
        icon: 'icon.png',
        vibrate: [200, 100, 200],
        tag: 'alarm-notification'
    };
    event.waitUntil(
        self.registration.showNotification('アラーム', options)
    );
});
