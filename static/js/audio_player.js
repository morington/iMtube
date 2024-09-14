document.addEventListener('DOMContentLoaded', function () {
    const audioPlayerContainer = document.getElementById('audio-player-container');
    const audioTitle = document.getElementById('audio-title');
    const audioElement = document.getElementById('audio-player');

    // Инициализация MediaElement.js
    const player = new MediaElementPlayer(audioElement, {
        features: ['playpause', 'progress', 'current', 'duration', 'volume'],
        success: function(mediaElement, originalNode) {
            // Дополнительные настройки при необходимости
        }
    });

    let currentTrackIndex = 0;
    let trackList = [];

    // Инициализация списка треков
    function initializeTrackList() {
        trackList = Array.from(document.querySelectorAll('.play-audio-btn')).map(btn => ({
            account: btn.getAttribute('data-account'),
            name: btn.getAttribute('data-name')
        }));
    }

    // Функция для загрузки и воспроизведения трека
    function playTrack(index) {
        if (index < 0 || index >= trackList.length) return;
        currentTrackIndex = index;
        const track = trackList[index];
        const src = `/audio/${track.account}/${track.name}`;
        player.setSrc(src);
        player.load();
        player.play();
        audioTitle.textContent = track.name.replace(/\.(mp3|wav|ogg)$/i, '');
        audioPlayerContainer.style.display = 'flex';

        // Обновление активного трека
        document.querySelectorAll('.audio-item').forEach(item => item.classList.remove('active'));
        const activeItem = document.querySelector(`.play-audio-btn[data-account="${track.account}"][data-name="${track.name}"]`).closest('.audio-item');
        if (activeItem) {
            activeItem.classList.add('active');
        }
    }

    // Обработка кликов по кнопкам воспроизведения аудио
    document.body.addEventListener('click', function (e) {
        const playButton = e.target.closest('.play-audio-btn');
        if (playButton) {
            e.preventDefault();
            initializeTrackList();
            const account = playButton.getAttribute('data-account');
            const name = playButton.getAttribute('data-name');
            const index = trackList.findIndex(track => track.account === account && track.name === name);
            if (index !== -1) {
                playTrack(index);
            }
        }
    });

    // Обработка окончания трека
    player.media.addEventListener('ended', () => {
        if (currentTrackIndex < trackList.length - 1) {
            playTrack(currentTrackIndex + 1);
        } else {
            audioPlayerContainer.style.display = 'none';
        }
    });

    // Инициализация списка треков при загрузке
    initializeTrackList();
});
