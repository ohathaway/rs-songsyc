const fs      = require('fs');
const fetch   = require('isomorphic-fetch');
const Dropbox = require('dropbox').Dropbox;


var box = new Dropbox({ accessToken: 'GRkov04pkTIAAAAAAABXWtQ6sdH8Bhhm1KHMQU3-2wwFf9ALG89C8sMSAIZaQZ_3', fetch: fetch});

var searchParms = {
  path: '/RockSmithDLC',
  query: '_m.psarc',
  max_results: 1000,
  mode: 'filename'
}

var localDir = process.env.HOME+'/Library/Application Support/Steam/steamapps/common/Rocksmith2014/dlc/'

box.filesSearch(searchParms)
  .then(function(response) {
    response.matches.forEach(function(songFile){
      if(songFile.metadata.name.match(/.*_m\.psarc/)) {
        if(fs.existsSync(localDir+songFile.metadata.name)) console.log(" skipping: "+songFile.metadata.name)
        else {
          let downloadParms = {path: songFile.metadata.path_lower}
          console.log("Downloading "+downloadParms.path);
          let songBuffer = box.filesDownload(downloadParms);
          console.log(songBuffer);
        }
      }
    })
    //console.log(response);
  })
  .catch(function(error) {
    console.log(error);
  });
