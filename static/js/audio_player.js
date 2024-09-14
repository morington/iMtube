document.addEventListener('DOMContentLoaded', function () {
    // Инициализируем Plyr с необходимыми контролами
    const player = new Plyr('#audio-player', {
        controls: [
            'play',
            'progress',
            'current-time',
            'mute',
            'volume'
        ]
    });

    const audioPlayerContainer = document.getElementById('audio-player-container');
    const audioTitle = document.getElementById('audio-title');

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
        player.source = {
            type: 'audio',
            title: track.name.replace(/\.(mp3|wav|ogg)$/i, ''),
            sources: [{
                src: `/audio/${track.account}/${track.name}`,
                type: 'audio/mpeg'
            }]
        };
        audioTitle.textContent = track.name.replace(/\.(mp3|wav|ogg)$/i, '');
        audioPlayerContainer.style.display = 'flex';
        player.play();

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
    player.on('ended', () => {
        // Автоматическое воспроизведение следующего трека
        if (currentTrackIndex < trackList.length - 1) {
            playTrack(currentTrackIndex + 1);
        } else {
            audioPlayerContainer.style.display = 'none';
        }
    });

    // Инициализация списка треков при загрузке
    initializeTrackList();
});
