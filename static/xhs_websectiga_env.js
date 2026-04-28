// 补环境 - 用于执行 websectiga JSVMP 代码
var window = globalThis;
window.window = window;
window.top = window;
window.parent = window;
window.self = window;
window.frames = [window];

window.navigator = {
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36',
    platform: 'Win32', language: 'zh-CN', languages: ['zh-CN','zh','en'],
    hardwareConcurrency: 8, deviceMemory: 8, maxTouchPoints: 0,
    cookieEnabled: true, webdriver: false, vendor: 'Google Inc.',
    appVersion: '5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36',
    appName: 'Netscape', product: 'Gecko', productSub: '20030107',
    plugins: {length: 5}, mimeTypes: {length: 2},
    connection: {effectiveType: '4g', rtt: 50, downlink: 10},
    getBattery: function() { return Promise.resolve({charging: true, chargingTime: 0, dischargingTime: Infinity, level: 1}); }
};

window.location = {
    href: 'https://www.xiaohongshu.com/explore',
    hostname: 'www.xiaohongshu.com',
    host: 'www.xiaohongshu.com',
    origin: 'https://www.xiaohongshu.com',
    protocol: 'https:',
    pathname: '/explore',
    search: '', hash: ''
};

window.screen = {width: 1920, height: 1080, availWidth: 1920, availHeight: 1040, colorDepth: 24, pixelDepth: 24};

window.document = {
    cookie: '', referrer: '', title: '', domain: 'xiaohongshu.com',
    URL: 'https://www.xiaohongshu.com/explore',
    documentElement: {style: {}, getAttribute: function() { return null; }},
    head: {appendChild: function() {}},
    body: {appendChild: function() {}},
    createElement: function(t) {
        return {
            tagName: t, style: {}, setAttribute: function() {}, getAttribute: function() { return null; },
            appendChild: function() {}, getContext: function() { return null; },
            toDataURL: function() { return ''; }, width: 0, height: 0
        };
    },
    getElementById: function() { return null; },
    getElementsByTagName: function() { return []; },
    querySelector: function() { return null; },
    querySelectorAll: function() { return []; },
    addEventListener: function() {},
    removeEventListener: function() {},
    hidden: false, visibilityState: 'visible'
};

window.localStorage = {_d: {}, getItem: function(k) { return this._d[k] || null; }, setItem: function(k, v) { this._d[k] = String(v); }, removeItem: function(k) { delete this._d[k]; }};
window.sessionStorage = {_d: {}, getItem: function(k) { return this._d[k] || null; }, setItem: function(k, v) { this._d[k] = String(v); }, removeItem: function(k) { delete this._d[k]; }};
window.performance = {now: function() { return Date.now() - 1000; }, timing: {navigationStart: Date.now() - 3000}};
window.history = {length: 1};
window.innerWidth = 1920;
window.innerHeight = 937;
window.outerWidth = 1920;
window.outerHeight = 1040;
window.devicePixelRatio = 1;
window.XMLHttpRequest = function() {};
window.Image = function() {};
window.MutationObserver = function() {};
window.MutationObserver.prototype = {observe: function() {}, disconnect: function() {}};
window.requestAnimationFrame = function(cb) { return setTimeout(cb, 16); };
window.cancelAnimationFrame = function(id) { clearTimeout(id); };
window.Intl = typeof Intl !== 'undefined' ? Intl : {DateTimeFormat: function() { return {resolvedOptions: function() { return {timeZone: 'Asia/Shanghai'}; }}; }};
window.crypto = {getRandomValues: function(a) { for (var i = 0; i < a.length; i++) a[i] = Math.floor(Math.random() * 256); return a; }};
window.atob = function(s) { return Buffer.from(s, 'base64').toString('binary'); };
window.btoa = function(s) { return Buffer.from(s, 'binary').toString('base64'); };

var _websectiga_result = '';
window.seccallback = function(value) { _websectiga_result = value; };
