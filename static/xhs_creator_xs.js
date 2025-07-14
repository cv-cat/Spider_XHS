const crypto = require('crypto');
let key = '7cc4adla5ay0701v'
let iv = '4uzjr7mbsibcaldp'
key = Buffer.from(key);
iv = Buffer.from(iv);
var encrypt = function (data) {
    const cipher = crypto.createCipheriv('aes-128-cbc', key, iv);
    let encrypted = cipher.update(data, 'utf8', 'hex');
    encrypted += cipher.final('hex');
    return encrypted;
};
function decrypt(encryptedText) {
    const decipher = crypto.createDecipheriv('aes-128-cbc', key, iv);
    let decrypted = decipher.update(encryptedText, 'hex', 'utf8');
    decrypted += decipher.final('utf8');
    return decrypted;
}
function get_xs(api, data, a1) {
    if (data){
        api = api + JSON.stringify(data);
    }
    const md5 = crypto.createHash('md5');
    let x1 = md5.update(api).digest('hex');
    let x2 = "0|0|0|1|0|0|1|0|0|0|1|0|0|0|0|1|0|0|0";
    let x3 = a1;
    let x4 = Date.now();
    let x = `x1=${x1};x2=${x2};x3=${x3};x4=${x4};`;
    let payload = encrypt(btoa(x));
    let encrypt_data = {
        "signSvn":"56",
        "signType":"x2",
        "appId":"ugc",
        "signVersion":"1",
        "payload":payload
    }
    encrypt_data = JSON.stringify(encrypt_data);
    encrypt_data = 'XYW_' + btoa(encrypt_data);
    return {
        'X-s': encrypt_data,
        'X-t': x4
    }
}


function get_request_headers_params(api, data, a1){
    api = 'url=' + api
    let xs_xt = get_xs(api, data, a1);
    let xs = xs_xt['X-s'];
    let xt = xs_xt['X-t'];
    return {
        "xs": xs,
        "xt": xt,
    }
}
