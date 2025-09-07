// my_profile.js - The complete and final version

document.addEventListener('DOMContentLoaded', function() {
    const loggedInUserId = localStorage.getItem('userId');
    if (!loggedInUserId) {
        // This is a fallback, app.js should already handle this
        window.location.href = 'login.html';
        return;
    }

    // --- ELEMENT SELECTORS ---
    const viewMode = document.getElementById('profile-view-mode');
    const editMode = document.getElementById('profile-edit-mode');
    const editProfileBtn = document.getElementById('edit-profile-btn');
    const cancelEditBtn = document.getElementById('cancel-edit-btn');
    const editProfileForm = document.getElementById('edit-profile-form');
    const interestsEditContainer = document.getElementById('edit-interests');

    // --- AVAILABLE INTERESTS (should match register.js) ---
    const allInterests = ["Gaming", "Coding", "AI", "Traveling", "Reading", "Movies", "Music", "Photography", "Cooking", "Hiking", "Art", "Sports", "Fitness", "Dancing", "Writing", "Anime", "Startups", "Volunteering", "Fashion", "Yoga", "Podcasts", "Concerts", "Theater", "Board Games", "Investing", "Politics", "History", "Science", "Nature", "Coffee", "Tea", "Foodie", "DIY Projects", "Cars", "Pets", "Meditation", "Running", "Swimming", "Cycling", "Entrepreneurship"];

    let currentUserData = {};

    // --- FETCH AND DISPLAY PROFILE DATA ---
    function loadProfileData() {
        fetch(`/profile/${loggedInUserId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Could not fetch profile data.');
                }
                return response.json();
            })
            .then(user => {
                currentUserData = user;
                populateViewMode(user);
                populateEditMode(user);
            })
            .catch(error => console.error('Error fetching profile:', error));
    }

    function populateViewMode(user) {
        // --- THIS IS THE UPDATED PART FOR THE PHOTO ---
        const avatarContainer = document.getElementById('profile-avatar');
        avatarContainer.innerHTML = ''; // Clear previous content
        if (user.profile_image_url) {
            const img = document.createElement('img');
            img.src = user.profile_image_url;
            img.alt = user.fullName;
            img.className = 'profile-avatar-photo';
            avatarContainer.appendChild(img);
        } else {
            avatarContainer.textContent = user.fullName.charAt(0);
        }
        // --- END OF UPDATED PART ---

        document.getElementById('profile-fullName').textContent = user.fullName;
        document.getElementById('profile-college').textContent = user.college;
        document.getElementById('profile-bio').textContent = user.bio || 'You have not written a bio yet.';
        document.getElementById('profile-age').textContent = user.age || '--';
        document.getElementById('profile-gender').textContent = user.gender || '--';
        document.getElementById('profile-preference').textContent = user.preference || '--';
        const interestsContainer = document.getElementById('profile-interests');
        interestsContainer.innerHTML = '';
        if (user.interests) {
            user.interests.split(',').forEach(interest => {
                const tag = document.createElement('span');
                tag.className = 'interest-tag-card';
                tag.textContent = interest.trim();
                interestsContainer.appendChild(tag);
            });
        }
    }

    function populateEditMode(user) {
        document.getElementById('edit-fullName').value = user.fullName;
        document.getElementById('edit-college').value = user.college;
        document.getElementById('edit-age').value = user.age;
        document.getElementById('edit-bio').value = user.bio;
        
        // Populate and select interests
        interestsEditContainer.innerHTML = '';
        const userInterests = user.interests ? user.interests.split(',').map(i => i.trim()) : [];
        allInterests.forEach(interest => {
            const tag = document.createElement('div');
            tag.className = 'interest-tag';
            if (userInterests.includes(interest)) {
                tag.classList.add('selected');
            }
            tag.textContent = interest;
            tag.dataset.interest = interest;
            interestsEditContainer.appendChild(tag);
        });
    }

    // --- EVENT LISTENERS ---
    editProfileBtn.addEventListener('click', () => {
        viewMode.style.display = 'none';
        editMode.style.display = 'block';
    });

    cancelEditBtn.addEventListener('click', () => {
        viewMode.style.display = 'block';
        editMode.style.display = 'none';
    });

    interestsEditContainer.addEventListener('click', e => {
        if (e.target.classList.contains('interest-tag')) {
            const selectedCount = interestsEditContainer.querySelectorAll('.interest-tag.selected').length;
            if (e.target.classList.contains('selected') || selectedCount < 5) {
                e.target.classList.toggle('selected');
            } else {
                alert('You can select a maximum of 5 interests.');
            }
        }
    });

    editProfileForm.addEventListener('submit', function(event) {
        event.preventDefault();
        const selectedInterests = Array.from(interestsEditContainer.querySelectorAll('.interest-tag.selected'))
                                       .map(tag => tag.dataset.interest);
        
        const updatedData = {
            userId: loggedInUserId,
            fullName: document.getElementById('edit-fullName').value,
            college: document.getElementById('edit-college').value,
            age: document.getElementById('edit-age').value,
            bio: document.getElementById('edit-bio').value,
            interests: selectedInterests
        };

        fetch('/update_profile', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(updatedData)
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            if (data.status === 'success') {
                loadProfileData(); // Reload the profile data to show changes
                viewMode.style.display = 'block';
                editMode.style.display = 'none';
            }
        })
        .catch(error => console.error('Error updating profile:', error));
    });

    // --- INITIAL LOAD ---
    loadProfileData();
});