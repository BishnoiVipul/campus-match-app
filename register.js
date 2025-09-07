// register.js - The complete and final version

document.addEventListener('DOMContentLoaded', function() {
    // --- ELEMENT SELECTORS ---
    const formSteps = Array.from(document.querySelectorAll('.form-step'));
    const progressSteps = Array.from(document.querySelectorAll('.progress-step'));
    const nextButtons = document.querySelectorAll('.btn-next');
    const prevButtons = document.querySelectorAll('.btn-prev');
    const form = document.querySelector('#register-form');
    const interestsContainer = document.querySelector('.interest-tags-container');

    let currentStep = 1;

    // --- INTERESTS LIST ---
    const interests = [
        "Gaming", "Coding", "AI", "Traveling", "Reading", "Movies", "Music", "Photography", "Cooking", "Hiking",
        "Art", "Sports", "Fitness", "Dancing", "Writing", "Anime", "Startups", "Volunteering", "Fashion", "Yoga",
        "Podcasts", "Concerts", "Theater", "Board Games", "Investing", "Politics", "History", "Science", "Nature", "Coffee",
        "Tea", "Foodie", "DIY Projects", "Cars", "Pets", "Meditation", "Running", "Swimming", "Cycling", "Entrepreneurship",
        "Debate", "Stand-up Comedy", "Netflix", "YouTube", "Social Media", "Memes", "Technology", "Space", "Philosophy", "Psychology"
    ];

    // --- GENERATE INTEREST TAGS ---
    interests.forEach(interest => {
        const tag = document.createElement('div');
        tag.classList.add('interest-tag');
        tag.textContent = interest;
        tag.dataset.interest = interest;
        interestsContainer.appendChild(tag);
    });

    // --- HANDLE INTEREST SELECTION ---
    interestsContainer.addEventListener('click', e => {
        if (e.target.classList.contains('interest-tag')) {
            e.target.classList.toggle('selected');
        }
    });

    // --- HANDLE "NEXT" BUTTON CLICKS ---
    nextButtons.forEach(button => {
        button.addEventListener('click', () => {
            if (validateStep(currentStep)) {
                changeStep(currentStep + 1);
            }
        });
    });

    // --- HANDLE "PREVIOUS" BUTTON CLICKS ---
    prevButtons.forEach(button => {
        button.addEventListener('click', () => {
            changeStep(currentStep - 1);
        });
    });

    // --- HANDLE FORM SUBMISSION ---
    form.addEventListener('submit', function(event) {
        event.preventDefault();
        if (!validateStep(currentStep)) return;

        // Use FormData, which is necessary for sending files.
        const formData = new FormData(form);

        // Get the selected interests and join them into a single string.
        const selectedInterests = Array.from(document.querySelectorAll('.interest-tag.selected'))
                                       .map(tag => tag.dataset.interest);
        formData.append('interests', selectedInterests.join(','));

        // Remove the confirmPassword field as it's not needed by the backend.
        formData.delete('confirmPassword');

        fetch('https://campus-match-app.onrender.com/signup', {
            method: 'POST',
            body: formData // Send the FormData object directly. No headers needed.
        })
        .then(response => response.json())
        .then(result => {
            alert(result.message);
            if (result.status === 'success') {
                localStorage.setItem('userId', result.user.id);
                localStorage.setItem('userName', result.user.fullName);
                window.location.href = 'home.html';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred during registration. Please try again.');
        });
    });

    // --- FUNCTION TO CHANGE STEPS ---
    function changeStep(step) {
        formSteps.forEach(formStep => {
            formStep.classList.toggle('active', parseInt(formStep.dataset.step) === step);
        });
        progressSteps.forEach(progressStep => {
            progressStep.classList.toggle('active', parseInt(progressStep.dataset.step) <= step);
        });
        currentStep = step;
    }

    // --- FUNCTION TO VALIDATE EACH STEP ---
    function validateStep(step) {
        let isValid = true;
        const currentFormStep = formSteps.find(s => parseInt(s.dataset.step) === step);
        const inputs = currentFormStep.querySelectorAll('input[required], select[required], textarea[required]');
        
        inputs.forEach(input => {
            if (!isValid) return; // Stop checking if already invalid
            // For file inputs, we check if a file has been selected
            if (input.type === 'file') {
                if (input.files.length === 0) {
                    alert(`Please select a profile photo.`);
                    isValid = false;
                }
            } else if (!input.value.trim()) { // For other inputs, check if they are empty
                alert(`Please fill out the "${input.labels[0].textContent.replace(':', '')}" field.`);
                isValid = false;
            }
        });

        // Special validation for step 2 (passwords)
        if (step === 2 && isValid) {
            const password = document.querySelector('#password').value;
            const confirmPassword = document.querySelector('#confirmPassword').value;
            if (password.length < 6) {
                alert('Password must be at least 6 characters long.');
                isValid = false;
            } else if (password !== confirmPassword) {
                alert('Passwords do not match.');
                isValid = false;
            }
        }

        // Special validation for step 4 (interests)
        if (step === 4 && isValid) {
            const selectedCount = document.querySelectorAll('.interest-tag.selected').length;
            if (selectedCount < 3) {
                alert('Please select at least 3 interests.');
                isValid = false;
            }
        }
        
        return isValid;
    }
});