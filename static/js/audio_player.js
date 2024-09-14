document.addEventListener('DOMContentLoaded', function () {
    // Инициализируем Plyr
    const player = new Plyr('#audio-player', {
        controls: [
            'play',
            'progress',
            'current-time',
            'mute',
            'volume'
            // 'fullscreen' убран для аудио
        ]
    });

    const audioPlayerContainer = document.getElementById('audio-player-container');
    const audioTitle = document.getElementById('audio-title');
    const audioClose = document.getElementById('audio-close');

    let currentTrackIndex = 0;
    let trackList = [];
    let repeatMode = localStorage.getItem('repeatMode') || 'none'; // 'all', 'one', 'none'

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
    }

    // Функция для воспроизведения следующего трека
    function nextTrack() {
        if (repeatMode === 'one') {
            player.restart();
            return;
        }
        if (currentTrackIndex < trackList.length - 1) {
            playTrack(currentTrackIndex + 1);
        } else if (repeatMode === 'all') {
            playTrack(0);
        }
    }

    // Функция для воспроизведения предыдущего трека
    function previousTrack() {
        if (player.currentTime > 5) {
            player.restart();
            return;
        }
        if (currentTrackIndex > 0) {
            playTrack(currentTrackIndex - 1);
        } else if (repeatMode === 'all') {
            playTrack(trackList.length - 1);
        }
    }

    // Обработчик закрытия плеера
    audioClose.addEventListener('click', function () {
        player.pause();
        audioPlayerContainer.style.display = 'none';
    });

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
        if (repeatMode === 'one') {
            player.restart();
        } else {
            nextTrack();
        }
    });

    // Добавление кнопки повтора
    function addRepeatButton() {
        // Создаем кнопку повтора
        const repeatBtn = document.createElement('button');
        repeatBtn.classList.add('btn', 'btn-light', 'btn-sm', 'ms-2');
        repeatBtn.title = 'Повтор';
        repeatBtn.innerHTML = '<i class="fas fa-repeat"></i>';

        // Добавляем обработчик клика
        repeatBtn.addEventListener('click', function () {
            if (repeatMode === 'all') {
                repeatMode = 'one';
            } else if (repeatMode === 'one') {
                repeatMode = 'none';
            } else {
                repeatMode = 'all';
            }
            updateRepeatButton();
            localStorage.setItem('repeatMode', repeatMode);
        });

        // Добавляем кнопку в интерфейс Plyr
        const controls = player.elements.controls;
        controls.insertBefore(repeatBtn, controls.firstChild);
    }

    // Функция обновления состояния кнопки повтора
    function updateRepeatButton() {
        const repeatBtn = player.elements.controls.querySelector('.fa-repeat, .fa-repeat-1');
        if (repeatBtn) {
            if (repeatMode === 'all') {
                repeatBtn.classList.remove('fa-repeat-1');
                repeatBtn.classList.add('fa-repeat');
                repeatBtn.parentElement.style.opacity = '1';
                repeatBtn.parentElement.title = 'Повторить все';
            } else if (repeatMode === 'one') {
                repeatBtn.classList.remove('fa-repeat');
                repeatBtn.classList.add('fa-repeat-1');
                repeatBtn.parentElement.style.opacity = '1';
                repeatBtn.parentElement.title = 'Повторить один';
            } else {
                repeatBtn.classList.remove('fa-repeat-1');
                repeatBtn.classList.add('fa-repeat');
                repeatBtn.parentElement.style.opacity = '0.5';
                repeatBtn.parentElement.title = 'Повтор отключен';
            }
        }
    }

    // Инициализация списка треков при загрузке
    initializeTrackList();

    // Инициализация кнопки повтора
    addRepeatButton();
    updateRepeatButton();

    // Восстановление предыдущего трека, если есть
    if (localStorage.getItem('currentTrackIndex')) {
        const savedIndex = parseInt(localStorage.getItem('currentTrackIndex'));
        if (!isNaN(savedIndex) && savedIndex >= 0 && savedIndex < trackList.length) {
            playTrack(savedIndex);
        }
    }

    // Сохранение текущего трека при воспроизведении
    player.on('play', () => {
        localStorage.setItem('currentTrackIndex', currentTrackIndex);
    });

    // Остановка плеера при выгрузке страницы
    window.addEventListener('beforeunload', function () {
        player.pause();
        audioPlayerContainer.style.display = 'none';
    });
});
