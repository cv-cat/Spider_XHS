const CryptoJS = require('crypto-js');

function getSignature(message, fileId, contentLength, host) {
    host = host || 'ros-upload.xiaohongshu.com';
    let key = 'null'
    let hash = CryptoJS.HmacSHA1(message, key);
    key = CryptoJS.enc.Hex.stringify(hash);
    let new_message = "put\n" +
    `/spectrum/${fileId}\n` +
    "\n" +
    `content-length=${contentLength}&host=${host}\n`;
    let params = CryptoJS.SHA1(new_message).toString()
    message = "sha1\n" +
    `${message}\n` +
    `${params}\n`;
    hash = CryptoJS.HmacSHA1(message, key);
    return CryptoJS.enc.Hex.stringify(hash);
}
// let message = "1709905283;1709912483"
// let fileId = 'UcaECZ-40xa7Uir1V8msV4XAq3bF6E8m16IT5eoR6Z12spg'
// let contentLength = 13975
// console.log(getSignature(message, fileId, contentLength))

