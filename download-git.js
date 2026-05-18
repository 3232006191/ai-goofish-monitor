const https = require("https");
const fs = require("fs");
const path = require("path");
const os = require("os");

const GIT_URL =
  "https://github.com/git-for-windows/git/releases/download/v2.49.0.windows.1/MinGit-2.49.0-64-bit.zip";
const DEST = path.join(os.homedir(), "Downloads", "MinGit-2.49.0-64-bit.zip");
const EXTRACT_DIR = path.join(os.homedir(), "git-portable");

function download(url, dest) {
  return new Promise((resolve, reject) => {
    console.log("Downloading: " + url);
    const file = fs.createWriteStream(dest);
    https
      .get(url, (res) => {
        if (res.statusCode === 302 || res.statusCode === 301) {
          return download(res.headers.location, dest).then(resolve, reject);
        }
        res.pipe(file);
        file.on("finish", () => {
          file.close();
          console.log("Downloaded to: " + dest);
          resolve();
        });
      })
      .on("error", reject);
  });
}

download(GIT_URL, DEST)
  .then(() => console.log("GIT_DOWNLOADED: " + DEST))
  .catch((e) => console.error("ERROR: " + e.message));