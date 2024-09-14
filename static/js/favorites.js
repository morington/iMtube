// Избранные видео из localStorage
let favorites = JSON.parse(localStorage.getItem('favorites')) || [];

// Обновление кнопок избранного
function updateFavoriteButtons() {
    const favoriteButtons = document.querySelectorAll('.favorite-btn[data-video]');
    favoriteButtons.forEach(button => {
        const videoPath = button.getAttribute('data-video');
        if (favorites.includes(videoPath)) {
            button.classList.add('active');
            button.innerHTML = 'Убрать из избранного';
        } else {
            button.classList.remove('active');
            button.innerHTML = '<i class="fas fa-star"></i> Добавить в избранное';
        }
    });
}

// Обработчик клика по кнопке избранного
document.body.addEventListener('click', function (e) {
    const favoriteBtn = e.target.closest('.favorite-btn[data-video]');
    if (favoriteBtn) {
        const videoPath = favoriteBtn.getAttribute('data-video');
        if (!videoPath) return;

        if (favorites.includes(videoPath)) {
            // Удаление из избранного
            favorites = favorites.filter(fav => fav !== videoPath);
            favoriteBtn.classList.remove('active');
            favoriteBtn.innerHTML = '<i class="fas fa-star"></i> Добавить в избранное';
        } else {
            // Добавление в избранное
            favorites.push(videoPath);
            favoriteBtn.classList.add('active');
            favoriteBtn.innerHTML = 'Убрать из избранного';
        }

        localStorage.setItem('favorites', JSON.stringify(favorites));
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
            link.textContent = video.replace(/\.(mp4|avi|mkv)$/i, '');
            link.className = 'text-dark';
            listItem.appendChild(link);
            favoritesList.appendChild(listItem);
        });
    }
}

// Инициализация
updateFavoriteButtons();
updateFavoritesList();
