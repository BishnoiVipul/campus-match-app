// home.js - The complete and final version for the Discover page

document.addEventListener('DOMContentLoaded', function() {
    // --- ELEMENT SELECTORS ---
    // Get references to all the elements we need to interact with on this page.
    const cardStack = document.querySelector('#card-stack');
    const noMoreProfilesMsg = document.querySelector('#no-more-profiles');
    const likeButton = document.querySelector('#btn-like');
    const nextButton = document.querySelector('#btn-next');
    
    // --- STATE VARIABLES ---
    // These keep track of the users and which profile is currently visible.
    let allUsers = [];
    let currentUserIndex = 0;

    // Get the logged-in user's ID from browser storage.
    const loggedInUserId = localStorage.getItem('userId');
    // If no one is logged in, do nothing. app.js should have already redirected.
    if (!loggedInUserId) return;

    // --- SETUP EVENT LISTENERS ---
    // Make the "Like" and "Next" buttons clickable.
    likeButton.addEventListener('click', () => handleAction('like'));
    nextButton.addEventListener('click', () => handleAction('next'));

    // --- FETCH USERS FROM BACKEND ---
    // This is the main function that gets the profiles to display.
    fetch(`/users?userId=${loggedInUserId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(users => {
            allUsers = users;
            if (allUsers.length > 0) {
                renderCards(); // If we found users, show them.
            } else {
                showNoMoreProfiles(); // Otherwise, show the "no more profiles" message.
            }
        })
        .catch(error => {
            console.error('Error fetching users:', error);
            noMoreProfilesMsg.textContent = 'Could not load profiles. Please try again.';
            showNoMoreProfiles();
        });
    
    // --- RENDER CARDS ---
    // This function creates the stack of profile cards on the page.
    function renderCards() {
        cardStack.innerHTML = ''; // Clear any old cards
        // We get the next 3 users and reverse them to create the visual stack effect.
        allUsers.slice(currentUserIndex, currentUserIndex + 3).reverse().forEach(user => {
            const card = createProfileCard(user);
            cardStack.appendChild(card);
        });
    }

    // --- CREATE A SINGLE PROFILE CARD ---
    // This function builds the HTML for one profile card.
    function createProfileCard(user) {
        const card = document.createElement('div');
        card.className = 'profile-card-swipe';

        // --- NEW: Logic to display photo or initial ---
        // If the user has a profile_image_url, create an <img> tag.
        // Otherwise, create a div with their first initial.
        const imageHTML = user.profile_image_url
            ? `<img src="${user.profile_image_url}" alt="${user.fullName}" class="card-image-photo">`
            : `<div class="card-image-initial">${user.fullName.charAt(0)}</div>`;

        let interestsHTML = '<div class="card-interests">';
        if (user.interests) {
            user.interests.split(',').slice(0, 5).forEach(interest => {
                interestsHTML += `<span class="interest-tag-card">${interest.trim()}</span>`;
            });
        }
        interestsHTML += '</div>';

        // This is the full HTML structure of the card.
        card.innerHTML = `
            <div class="card-image">${imageHTML}</div>
            <h2>${user.fullName}, ${user.age || ''}</h2>
            <div class="card-sub-info">${user.college || 'College Not Specified'}</div>
            <p>${user.bio || 'No bio yet.'}</p>
            ${interestsHTML}
        `;
        return card;
    }

    // --- HANDLE SWIPE ACTIONS ---
    // This function runs when the "Like" or "Next" button is clicked.
    function handleAction(action) {
        if (currentUserIndex >= allUsers.length) return; // Stop if we're out of users.

        const topCard = cardStack.querySelector('.profile-card-swipe:last-child');
        const likedUser = allUsers[currentUserIndex];

        if (topCard) {
            if (action === 'like') {
                topCard.classList.add('dismiss-right'); // Animate card to the right
                // Send the "like" to the server
                fetch('/like', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ liker_id: loggedInUserId, liked_id: likedUser.id })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.match) {
                        alert(`It's a Match with ${likedUser.fullName}!`);
                    }
                });
            } else {
                topCard.classList.add('dismiss-left'); // Animate card to the left
            }
        }

        currentUserIndex++; // Move to the next user in our list

        // Wait for the animation to finish, then update the card stack.
        setTimeout(() => {
            if (currentUserIndex < allUsers.length) {
                renderCards();
            } else {
                showNoMoreProfiles();
            }
        }, 300);
    }

    // --- SHOW "NO MORE PROFILES" MESSAGE ---
    function showNoMoreProfiles() {
        cardStack.style.display = 'none';
        noMoreProfilesMsg.style.display = 'block';
    }
});