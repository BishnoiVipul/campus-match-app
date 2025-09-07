document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.querySelector('form');
    const emailInput = document.querySelector('#email');
    const passwordInput = document.querySelector('#password');

    loginForm.addEventListener('submit', function(event) {
        event.preventDefault();

        const formData = {
            email: emailInput.value.trim(),
            password: passwordInput.value.trim()
        };

        // Send login data to the new /login endpoint
        fetch('https://campus-match-app.onrender.com/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        })
        .then(response => response.json())
        .then(data => {
            // Display the message from the server (either success or failure)
            alert(data.message);
            
            // If login was successful, redirect the user
            // This is the corrected block. We only need to check once.
            if (data.status === 'success') {
                // Save the user's info into the browser's localStorage
                localStorage.setItem('userId', data.user.id);
                localStorage.setItem('userName', data.user.fullName);

                // Redirect to the home page on successful login
                window.location.href = 'home.html';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while trying to log in.');
        });
    });
});