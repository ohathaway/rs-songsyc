// Configuration for Rocksmith Library Viewer
// Copy this file to config.js and update with your settings

const CONFIG = {
    // Dropbox configuration
    // Set this to your Dropbox base URL for the RockSmithDLC folder
    // To find this URL:
    //   1. Go to dropbox.com
    //   2. Navigate to your RockSmithDLC folder
    //   3. Copy the URL from the browser address bar
    //
    // Example: "https://www.dropbox.com/home/RockSmithDLC"
    // Leave as null to disable download links
    dropboxBaseUrl: "https://www.dropbox.com/home/RockSmithDLC",

    // If your files are organized in subdirectories by artist in Dropbox,
    // set this to true. Otherwise set to false if all files are in one folder.
    //
    // true  = Files organized like: RockSmithDLC/Artist Name/song.psarc
    // false = Files organized like: RockSmithDLC/song.psarc
    dropboxOrganizedByArtist: true,
};

// Example configurations:

// For organized library (files in artist folders):
// dropboxBaseUrl: "https://www.dropbox.com/home/RockSmithDLC"
// dropboxOrganizedByArtist: true

// For flat library (all files in one folder):
// dropboxBaseUrl: "https://www.dropbox.com/home/RockSmithDLC/AllFiles"
// dropboxOrganizedByArtist: false

// To disable download links:
// dropboxBaseUrl: null
// dropboxOrganizedByArtist: true
