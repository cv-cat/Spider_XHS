const jsdom = require("jsdom");
const { JSDOM } = jsdom;
const html = "<!DOCTYPE html><p></p>";
const resourceLoader = new jsdom.ResourceLoader({
    userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
});

const dom = new JSDOM(html,{
    url: "https://www.xiaohongshu.com",
    referrer: "https://www.xiaohongshu.com",
    contentType: "text/html",
    resources: resourceLoader,
})
window = dom.window;
document = window.document;
DOMParser = window.DOMParser;
location = window.location;
navigator = window.navigator;
localStorage = window.localStorage;
HTMLBodyElement = window.HTMLBodyElement;
HTMLHeadElement = window.HTMLHeadElement;
HTMLElement = window.HTMLElement;
addEventListener = window.addEventListener;
self = global;
try {
    require('./xhs_creator_sign_other.js');
}catch (e) {
    try {
        require('./static/xhs_creator_sign_other.js');
    }catch (e) {
        require('../static/xhs_creator_sign_other.js');
    }
}

class AudioContextMock {
    constructor() {
    }
}
class webkitAudioContextMock {
    constructor() {
    }
}
var indexedDB = {}

var canvas = {
    toDataURL: function toDataURL() {
    },
    getContext: function getContext(x) {
    }
};
var zc666;
!function() {
    "use strict";
    var e, t, n, r, o, i = {}, u = {};
    function c(e) {
        var t = u[e];
        if (void 0 !== t)
            return t.exports;
        var n = u[e] = {
            id: e,
            loaded: !1,
            exports: {}
        };
        // console.log(e)
        return i[e].call(n.exports, n, n.exports, c),
        n.loaded = !0,
        n.exports
    }
    c.m = i,
    c.amdD = function() {
        throw new Error("define cannot be used indirect")
    }
    ,
    c.amdO = {},
    e = [],
    c.O = function(t, n, r, o) {
        if (!n) {
            var i = 1 / 0;
            for (d = 0; d < e.length; d++) {
                n = e[d][0],
                r = e[d][1],
                o = e[d][2];
                for (var u = !0, f = 0; f < n.length; f++)
                    (!1 & o || i >= o) && Object.keys(c.O).every((function(e) {
                        return c.O[e](n[f])
                    }
                    )) ? n.splice(f--, 1) : (u = !1,
                    o < i && (i = o));
                if (u) {
                    e.splice(d--, 1);
                    var a = r();
                    void 0 !== a && (t = a)
                }
            }
            return t
        }
        o = o || 0;
        for (var d = e.length; d > 0 && e[d - 1][2] > o; d--)
            e[d] = e[d - 1];
        e[d] = [n, r, o]
    }
    ,
    c.n = function(e) {
        var t = e && e.__esModule ? function() {
            return e.default
        }
        : function() {
            return e
        }
        ;
        return c.d(t, {
            a: t
        }),
        t
    }
    ,
    n = Object.getPrototypeOf ? function(e) {
        return Object.getPrototypeOf(e)
    }
    : function(e) {
        return e.__proto__
    }
    ,
    c.t = function(e, r) {
        if (1 & r && (e = this(e)),
        8 & r)
            return e;
        if ("object" == typeof e && e) {
            if (4 & r && e.__esModule)
                return e;
            if (16 & r && "function" == typeof e.then)
                return e
        }
        var o = Object.create(null);
        c.r(o);
        var i = {};
        t = t || [null, n({}), n([]), n(n)];
        for (var u = 2 & r && e; "object" == typeof u && !~t.indexOf(u); u = n(u))
            Object.getOwnPropertyNames(u).forEach((function(t) {
                i[t] = function() {
                    return e[t]
                }
            }
            ));
        return i.default = function() {
            return e
        }
        ,
        c.d(o, i),
        o
    }
    ,
    c.d = function(e, t) {
        for (var n in t)
            c.o(t, n) && !c.o(e, n) && Object.defineProperty(e, n, {
                enumerable: !0,
                get: t[n]
            })
    }
    ,
    c.f = {},
    c.e = function(e) {
        return Promise.all(Object.keys(c.f).reduce((function(t, n) {
            return c.f[n](e, t),
            t
        }
        ), []))
    }
    ,
    c.u = function(e) {
        return "js/" + e + "." + {
            26: "ff9c6cc",
            30: "a0cc2bd",
            296: "5c44491",
            495: "e5ff7f7",
            762: "77d0f77",
            826: "65c91fa",
            865: "de0e838"
        }[e] + ".chunk.js"
    }
    ,
    c.miniCssF = function(e) {
        return "css/" + e + ".61840dc.chunk.css"
    }
    ,
    c.g = function() {
        if ("object" == typeof globalThis)
            return globalThis;
        try {
            return this || new Function("return this")()
        } catch (e) {
            if ("object" == typeof window)
                return window
        }
    }(),
    c.o = function(e, t) {
        return Object.prototype.hasOwnProperty.call(e, t)
    }
    ,
    r = {},
    o = "ugc:",
    c.l = function(e, t, n, i) {
        if (r[e])
            r[e].push(t);
        else {
            var u, f;
            if (void 0 !== n)
                for (var a = document.getElementsByTagName("script"), d = 0; d < a.length; d++) {
                    var l = a[d];
                    if (l.getAttribute("src") == e || l.getAttribute("data-webpack") == o + n) {
                        u = l;
                        break
                    }
                }
            u || (f = !0,
            (u = document.createElement("script")).charset = "utf-8",
            u.timeout = 120,
            c.nc && u.setAttribute("nonce", c.nc),
            u.setAttribute("data-webpack", o + n),
            u.src = e),
            r[e] = [t];
            var s = function(t, n) {
                u.onerror = u.onload = null,
                clearTimeout(h);
                var o = r[e];
                if (delete r[e],
                u.parentNode && u.parentNode.removeChild(u),
                o && o.forEach((function(e) {
                    return e(n)
                }
                )),
                t)
                    return t(n)
            }
              , h = setTimeout(s.bind(null, void 0, {
                type: "timeout",
                target: u
            }), 12e4);
            u.onerror = s.bind(null, u.onerror),
            u.onload = s.bind(null, u.onload),
            f && document.head.appendChild(u)
        }
    }
    ,
    c.r = function(e) {
        "undefined" != typeof Symbol && Symbol.toStringTag && Object.defineProperty(e, Symbol.toStringTag, {
            value: "Module"
        }),
        Object.defineProperty(e, "__esModule", {
            value: !0
        })
    }
    ,
    c.nmd = function(e) {
        return e.paths = [],
        e.children || (e.children = []),
        e
    }
    ,
    c.p = "//fe-static.xhscdn.com/formula-static/ugc/public/",
    function() {
        if (void 0 !== c) {
            var e = c.e
              , t = c.p
              , n = ["//fe-static-backup.xhscdn.com", "//fe-static.xhscdn.net"].sort((function() {
                return Math.random() - .5
            }
            ))
              , r = n.length
              , o = {};
            c.e = function(i) {
                var u = o.hasOwnProperty(i) ? o[i] : r;
                return c.p = u === r ? t : t.replace("//fe-static.xhscdn.com", n[u]),
                e(i).catch((function(e) {
                    if (u < 1)
                        throw e;
                    return new Promise((function(e) {
                        setTimeout((function() {
                            o[i] = u - 1,
                            e(c.e(i))
                        }
                        ), 100)
                    }
                    ))
                }
                ))
            }
        }
    }(),
    function() {
        if ("undefined" != typeof document) {
            var e = function(e) {
                return new Promise((function(t, n) {
                    var r = c.miniCssF(e)
                      , o = c.p + r;
                    if (function(e, t) {
                        for (var n = document.getElementsByTagName("link"), r = 0; r < n.length; r++) {
                            var o = (u = n[r]).getAttribute("data-href") || u.getAttribute("href");
                            if ("stylesheet" === u.rel && (o === e || o === t))
                                return u
                        }
                        var i = document.getElementsByTagName("style");
                        for (r = 0; r < i.length; r++) {
                            var u;
                            if ((o = (u = i[r]).getAttribute("data-href")) === e || o === t)
                                return u
                        }
                    }(r, o))
                        return t();
                    !function(e, t, n, r, o) {
                        var i = document.createElement("link");
                        i.rel = "stylesheet",
                        i.type = "text/css",
                        c.nc && (i.nonce = c.nc),
                        i.onerror = i.onload = function(n) {
                            if (i.onerror = i.onload = null,
                            "load" === n.type)
                                r();
                            else {
                                var u = n && n.type
                                  , c = n && n.target && n.target.href || t
                                  , f = new Error("Loading CSS chunk " + e + " failed.\n(" + u + ": " + c + ")");
                                f.name = "ChunkLoadError",
                                f.code = "CSS_CHUNK_LOAD_FAILED",
                                f.type = u,
                                f.request = c,
                                i.parentNode && i.parentNode.removeChild(i),
                                o(f)
                            }
                        }
                        ,
                        i.href = t,
                        n ? n.parentNode.insertBefore(i, n.nextSibling) : document.head.appendChild(i)
                    }(e, o, null, t, n)
                }
                ))
            }
              , t = {
                577: 0
            };
            c.f.miniCss = function(n, r) {
                t[n] ? r.push(t[n]) : 0 !== t[n] && {
                    296: 1
                }[n] && r.push(t[n] = e(n).then((function() {
                    t[n] = 0
                }
                ), (function(e) {
                    throw delete t[n],
                    e
                }
                )))
            }
        }
    }(),
    function() {
        c.b = document.baseURI || self.location.href;
        var e = {
            577: 0
        };
        c.f.j = function(t, n) {
            var r = c.o(e, t) ? e[t] : void 0;
            if (0 !== r)
                if (r)
                    n.push(r[2]);
                else if (577 != t) {
                    var o = new Promise((function(n, o) {
                        r = e[t] = [n, o]
                    }
                    ));
                    n.push(r[2] = o);
                    var i = c.p + c.u(t)
                      , u = new Error;
                    c.l(i, (function(n) {
                        if (c.o(e, t) && (0 !== (r = e[t]) && (e[t] = void 0),
                        r)) {
                            var o = n && ("load" === n.type ? "missing" : n.type)
                              , i = n && n.target && n.target.src;
                            u.message = "Loading chunk " + t + " failed.\n(" + o + ": " + i + ")",
                            u.name = "ChunkLoadError",
                            u.type = o,
                            u.request = i,
                            r[1](u)
                        }
                    }
                    ), "chunk-" + t, t)
                } else
                    e[t] = 0
        }
        ,
        c.O.j = function(t) {
            return 0 === e[t]
        }
        ;
        var t = function(t, n) {
            var r, o, i = n[0], u = n[1], f = n[2], a = 0;
            if (i.some((function(t) {
                return 0 !== e[t]
            }
            ))) {
                for (r in u)
                    c.o(u, r) && (c.m[r] = u[r]);
                if (f)
                    var d = f(c)
            }
            for (t && t(n); a < i.length; a++)
                o = i[a],
                c.o(e, o) && e[o] && e[o][0](),
                e[o] = 0;
            return c.O(d)
        }
          , n = self.webpackChunkugc = self.webpackChunkugc || [];
        n.forEach(t.bind(null, 0)),
        n.push = t.bind(null, n.push.bind(n))
    }();
    zc666 = c;
}();
//# sourceMappingURL=https://picasso-private-1251524319.cos.ap-shanghai.myqcloud.com/data/formula-static/formula/ugc/runtime-main.2e9b9ed.js.map
var uploader_src = zc666(56624)
          , md5 = zc666(63487)
          , md5_default = zc666.n(md5)
          , instance_concat = zc666(93966)
          , instance_concat_default = zc666.n(instance_concat)
          , now = zc666(29623)
          , now_default = zc666.n(now)
function dec2hex(e, t) {
    for (var r = "", n = e; n; ) {
        var o = 15 & n;
        r = String.fromCharCode((o > 9 ? 55 : 48) + o) + r,
        n >>= 4
    }
    if (t)
        for (; r.length < t; )
            r = "0".concat(r);
    return r.toLowerCase()
}
function urlSing(e) {
    var t;
    return md5_default()(instance_concat_default()(t = "hIJXulBFYcGRQjrz".concat(e)).call(t, dec2hex(now_default()() / 1e3)))
}
// let msg = "/110/0/01e63449420709d60010000000018f3c3e3630_0.jpg"
// console.log(urlSing(msg)) // 0e
// console.log(111) // 0e
