// Rocksmith Library Viewer
let libraryData = null;
let filteredSongs = [];
let config = null;

// DOM Elements
const searchInput = document.getElementById('searchInput');
const artistFilter = document.getElementById('artistFilter');
const arrangementFilter = document.getElementById('arrangementFilter');
const tuningFilter = document.getElementById('tuningFilter');
const platformFilter = document.getElementById('platformFilter');
const resetFiltersBtn = document.getElementById('resetFilters');
const songList = document.getElementById('songList');
const loadingMessage = document.getElementById('loadingMessage');
const errorMessage = document.getElementById('errorMessage');
const resultCount = document.getElementById('resultCount');

// Stats elements
const totalSongsEl = document.getElementById('totalSongs');
const totalArtistsEl = document.getElementById('totalArtists');
const leadCountEl = document.getElementById('leadCount');
const rhythmCountEl = document.getElementById('rhythmCount');
const bassCountEl = document.getElementById('bassCount');

// Load library data
async function loadLibrary() {
    try {
        // Load config
        config = typeof CONFIG !== 'undefined' ? CONFIG : { dropboxBaseUrl: null, dropboxOrganizedByArtist: true };

        const response = await fetch('library.json');
        if (!response.ok) {
            throw new Error('Failed to load library.json');
        }

        libraryData = await response.json();

        loadingMessage.style.display = 'none';
        initializeViewer();
    } catch (error) {
        console.error('Error loading library:', error);
        loadingMessage.style.display = 'none';
        errorMessage.style.display = 'block';
    }
}

// Initialize viewer with data
function initializeViewer() {
    if (!libraryData || !libraryData.songs) {
        errorMessage.style.display = 'block';
        return;
    }

    // Update stats
    updateStats();

    // Populate filter dropdowns
    populateFilters();

    // Initial display
    filteredSongs = [...libraryData.songs];
    displaySongs();

    // Add event listeners
    searchInput.addEventListener('input', applyFilters);
    artistFilter.addEventListener('change', applyFilters);
    arrangementFilter.addEventListener('change', applyFilters);
    tuningFilter.addEventListener('change', applyFilters);
    platformFilter.addEventListener('change', applyFilters);
    resetFiltersBtn.addEventListener('click', resetFilters);
}

// Update statistics
function updateStats() {
    const songs = libraryData.songs;

    totalSongsEl.textContent = libraryData.total_songs || songs.length;

    const artists = new Set(songs.map(s => s.artist));
    totalArtistsEl.textContent = artists.size;

    let leadCount = 0, rhythmCount = 0, bassCount = 0;
    songs.forEach(song => {
        const arrangements = song.arrangements || [];
        if (arrangements.some(a => a.type === 'Lead')) leadCount++;
        if (arrangements.some(a => a.type === 'Rhythm')) rhythmCount++;
        if (arrangements.some(a => a.type === 'Bass')) bassCount++;
    });

    leadCountEl.textContent = leadCount;
    rhythmCountEl.textContent = rhythmCount;
    bassCountEl.textContent = bassCount;
}

// Populate filter dropdowns
function populateFilters() {
    const songs = libraryData.songs;

    // Artists
    const artists = [...new Set(songs.map(s => s.artist))].sort();
    artists.forEach(artist => {
        const option = document.createElement('option');
        option.value = artist;
        option.textContent = artist;
        artistFilter.appendChild(option);
    });

    // Tunings
    const tunings = new Set();
    songs.forEach(song => {
        (song.arrangements || []).forEach(arr => {
            if (arr.tuning && arr.tuning !== 'Unknown') {
                tunings.add(arr.tuning);
            }
        });
    });

    [...tunings].sort().forEach(tuning => {
        const option = document.createElement('option');
        option.value = tuning;
        option.textContent = tuning;
        tuningFilter.appendChild(option);
    });
}

// Apply all filters
function applyFilters() {
    const searchTerm = searchInput.value.toLowerCase();
    const selectedArtist = artistFilter.value;
    const selectedArrangement = arrangementFilter.value;
    const selectedTuning = tuningFilter.value;
    const selectedPlatform = platformFilter.value;

    filteredSongs = libraryData.songs.filter(song => {
        // Search filter
        if (searchTerm) {
            const searchMatch =
                song.title.toLowerCase().includes(searchTerm) ||
                song.artist.toLowerCase().includes(searchTerm) ||
                (song.album && song.album.toLowerCase().includes(searchTerm));

            if (!searchMatch) return false;
        }

        // Artist filter
        if (selectedArtist && song.artist !== selectedArtist) {
            return false;
        }

        // Arrangement filter
        if (selectedArrangement) {
            const hasArrangement = (song.arrangements || []).some(
                a => a.type === selectedArrangement
            );
            if (!hasArrangement) return false;
        }

        // Tuning filter
        if (selectedTuning) {
            const hasTuning = (song.arrangements || []).some(
                a => a.tuning === selectedTuning
            );
            if (!hasTuning) return false;
        }

        // Platform filter
        if (selectedPlatform) {
            const platforms = song.platforms || [];
            if (selectedPlatform === 'PC' && !platforms.includes('PC')) return false;
            if (selectedPlatform === 'Mac' && !platforms.includes('Mac')) return false;
            if (selectedPlatform === 'Both' && platforms.length < 2) return false;
        }

        return true;
    });

    displaySongs();
}

// Display filtered songs
function displaySongs() {
    songList.innerHTML = '';

    const count = filteredSongs.length;
    resultCount.textContent = `${count} song${count !== 1 ? 's' : ''}`;

    if (count === 0) {
        songList.innerHTML = '<div class="no-results">No songs match your filters</div>';
        return;
    }

    filteredSongs.forEach(song => {
        const card = createSongCard(song);
        songList.appendChild(card);
    });
}

// Generate Dropbox link for a file
function generateDropboxLink(filePath, artist) {
    if (!config.dropboxBaseUrl) {
        return null;
    }

    // Extract filename from path
    const fileName = filePath.split('/').pop().split('\\').pop();

    // Build the Dropbox URL
    let url = config.dropboxBaseUrl;

    // Add artist folder if organized by artist
    if (config.dropboxOrganizedByArtist) {
        // URL encode the artist name
        const encodedArtist = encodeURIComponent(artist);
        url += '/' + encodedArtist;
    }

    // Add preview parameter with the filename
    url += '?preview=' + encodeURIComponent(fileName);

    return url;
}

// Create song card element
function createSongCard(song) {
    const card = document.createElement('div');
    card.className = 'song-card';

    // Platforms with download links
    const platformsHTML = (song.platforms || []).map(p => {
        const filePath = song.files[p];
        const dropboxLink = filePath ? generateDropboxLink(filePath, song.artist) : null;

        if (dropboxLink) {
            return `<a href="${dropboxLink}" target="_blank" class="platform-badge platform-${p.toLowerCase()}" title="Download ${p} version from Dropbox">${p} ⬇</a>`;
        } else {
            return `<span class="platform-badge platform-${p.toLowerCase()}">${p}</span>`;
        }
    }).join('');

    // Arrangements
    const arrangementsHTML = (song.arrangements || []).map(arr => `
        <div class="arrangement">
            <div class="arrangement-type">${arr.type || arr.name}</div>
            <div class="arrangement-tuning">${arr.tuning || 'Unknown'}</div>
        </div>
    `).join('');

    // Album info
    const albumInfo = song.album && song.album !== 'Unknown'
        ? `${song.album}`
        : '';

    const yearInfo = song.year && song.year !== 0
        ? `${albumInfo ? ' • ' : ''}${song.year}`
        : '';

    card.innerHTML = `
        <div class="song-header">
            <div class="song-info">
                <div class="song-title">${escapeHtml(song.title)}</div>
                <div class="song-artist">${escapeHtml(song.artist)}</div>
                <div class="song-meta">${albumInfo}${yearInfo}</div>
            </div>
            <div class="platforms">
                ${platformsHTML}
            </div>
        </div>
        ${arrangementsHTML ? `<div class="arrangements">${arrangementsHTML}</div>` : ''}
    `;

    return card;
}

// Reset all filters
function resetFilters() {
    searchInput.value = '';
    artistFilter.value = '';
    arrangementFilter.value = '';
    tuningFilter.value = '';
    platformFilter.value = '';
    applyFilters();
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', loadLibrary);
