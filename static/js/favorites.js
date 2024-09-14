// static/js/favorites.js

document.addEventListener('DOMContentLoaded', function () {
    // Избранные видео из localStorage
    let favorites = JSON.parse(localStorage.getItem('favorites')) || [];

    // Обновление кнопок избранного
    function updateFavoriteButtons() {
        const favoriteButtons = document.querySelectorAll('.favorite-btn');
        favoriteButtons.forEach(button => {
            const videoPath = button.getAttribute('data-video');
            if (favorites.includes(videoPath)) {
                button.classList.add('active');
            } else {
                button.classList.remove('active');
            }
        });
    }

    // Обработчик клика по кнопке избранного
    document.body.addEventListener('click', function (e) {
        if (e.target.closest('.favorite-btn')) {
            const button = e.target.closest('.favorite-btn');
            const videoPath = button.getAttribute('data-video');
            if (favorites.includes(videoPath)) {
                favorites = favorites.filter(fav => fav !== videoPath);
            } else {
                favorites.push(videoPath);
            }
            localStorage.setItem('favorites', JSON.stringify(favorites));
            updateFavoriteButtons();
            updateFavoritesList();
        }
    });

    // Обновление списка избранного в offcanvas
    function updateFavoritesList() {
        const favoritesList = document.getElementById('favoritesList');
        favoritesList.innerHTML = '';
        if (favorites.length === 0) {
            const emptyMessage = document.createElement('p');
            emptyMessage.textContent = 'Список пуст';
            favoritesList.appendChild(emptyMessage);
        } else {
            favorites.forEach(videoPath => {
                const [account, video] = videoPath.split('/');
                const listItem = document.createElement('li');
                listItem.className = 'list-group-item';
                const link = document.createElement('a');
                link.href = `/video/${account}/${video}`;
                link.textContent = video.replace('.mp4', '').replace('.avi', '').replace('.mkv', '');
                link.className = 'text-dark';
                listItem.appendChild(link);
                favoritesList.appendChild(listItem);
            });
        }
    }

    // Инициализация
    updateFavoriteButtons();
    updateFavoritesList();
});
