// app.js - The GLOBAL script for your application
document.addEventListener('DOMContentLoaded', function() {
    const welcomeContainer = document.getElementById('welcome-message-container');
    const logoutButton = document.getElementById('logout-button');
    const loggedInUserId = localStorage.getItem('userId');
    const loggedInUserName = localStorage.getItem('userName');

    if (!loggedInUserId) {
        if (!window.location.pathname.endsWith('login.html') && !window.location.pathname.endsWith('register.html') && !window.location.pathname.endsWith('index.html')) {
            window.location.href = 'login.html';
        }
        return;
    }

    if (welcomeContainer) {
        welcomeContainer.innerHTML = `Welcome, <span id="user-name">${loggedInUserName}</span>!`;
    }

    if (logoutButton) {
        logoutButton.addEventListener('click', () => {
            localStorage.clear();
            window.location.href = 'login.html';
        });
    }
});