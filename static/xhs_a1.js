self = global;
require('./xhs_a1_other.js');

let zc;
!function() {
    "use strict";
    var e, t, n, r, o, i = {}, u = {};
    function a(e) {
        var t = u[e];
        if (void 0 !== t)
            return t.exports;
        var n = u[e] = {
            id: e,
            loaded: !1,
            exports: {}
        };
        // console.log(e);
        return i[e].call(n.exports, n, n.exports, a),
        n.loaded = !0,
        n.exports
    }
    a.m = i,
    a.amdO = {},
    e = [],
    a.O = function(t, n, r, o) {
        if (!n) {
            var i = 1 / 0;
            for (d = 0; d < e.length; d++) {
                n = e[d][0],
                r = e[d][1],
                o = e[d][2];
                for (var u = !0, c = 0; c < n.length; c++)
                    (!1 & o || i >= o) && Object.keys(a.O).every((function(e) {
                        return a.O[e](n[c])
                    }
                    )) ? n.splice(c--, 1) : (u = !1,
                    o < i && (i = o));
                if (u) {
                    e.splice(d--, 1);
                    var f = r();
                    void 0 !== f && (t = f)
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
    a.n = function(e) {
        var t = e && e.__esModule ? function() {
            return e.default
        }
        : function() {
            return e
        }
        ;
        return a.d(t, {
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
    a.t = function(e, r) {
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
        a.r(o);
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
        a.d(o, i),
        o
    }
    ,
    a.d = function(e, t) {
        for (var n in t)
            a.o(t, n) && !a.o(e, n) && Object.defineProperty(e, n, {
                enumerable: !0,
                get: t[n]
            })
    }
    ,
    a.f = {},
    a.e = function(e) {
        return Promise.all(Object.keys(a.f).reduce((function(t, n) {
            return a.f[n](e, t),
            t
        }
        ), []))
    }
    ,
    a.u = function(e) {
        return "js/" + ({
            94: "Login",
            256: "NPS",
            290: "Notification",
            406: "User",
            464: "FeedToNote",
            540: "Explore",
            692: "Track",
            763: "Search",
            891: "xhs-web-player",
            895: "Note",
            898: "minor"
        }[e] || e) + "." + {
            12: "8b28169",
            18: "88c4016",
            85: "88eb7f6",
            94: "104ed7f",
            144: "5bfcae5",
            180: "a15bc58",
            226: "d1ae358",
            256: "6fd3536",
            270: "0f5c234",
            281: "ade9f6a",
            290: "cf5e782",
            311: "4c434c7",
            349: "337d0b8",
            406: "53c15af",
            442: "65251ce",
            464: "f3bec4f",
            469: "a49ea26",
            540: "a6e0a4a",
            614: "db669fd",
            651: "c01512b",
            692: "2893a74",
            712: "c08b90f",
            737: "9268c58",
            756: "4dda505",
            763: "1fc8785",
            772: "50c8fcf",
            891: "26c34b7",
            895: "6be359b",
            898: "eb35bc9"
        }[e] + ".chunk.js"
    }
    ,
    a.miniCssF = function(e) {
        return "css/" + ({
            94: "Login",
            256: "NPS",
            290: "Notification",
            406: "User",
            464: "FeedToNote",
            763: "Search",
            895: "Note",
            898: "minor"
        }[e] || e) + "." + {
            94: "3e4f13a",
            144: "3ad0c72",
            180: "1c6eeed",
            226: "4498383",
            256: "cac88bf",
            270: "a6b4ed2",
            290: "0f1b4ff",
            406: "f5289f1",
            464: "07c9bd1",
            756: "7953e4f",
            763: "82b3b59",
            895: "408e289",
            898: "5a4e17f"
        }[e] + ".chunk.css"
    }
    ,
    a.g = function() {
        if ("object" == typeof globalThis)
            return globalThis;
        try {
            return this || new Function("return this")()
        } catch (e) {
            if ("object" == typeof window)
                return window
        }
    }(),
    a.o = function(e, t) {
        return Object.prototype.hasOwnProperty.call(e, t)
    }
    ,
    r = {},
    o = "xhs-pc-web:",
    a.l = function(e, t, n, i) {
        if (r[e])
            r[e].push(t);
        else {
            var u, c;
            if (void 0 !== n)
                for (var f = document.getElementsByTagName("script"), d = 0; d < f.length; d++) {
                    var l = f[d];
                    if (l.getAttribute("src") == e || l.getAttribute("data-webpack") == o + n) {
                        u = l;
                        break
                    }
                }
            u || (c = !0,
            (u = document.createElement("script")).charset = "utf-8",
            u.timeout = 120,
            a.nc && u.setAttribute("nonce", a.nc),
            u.setAttribute("data-webpack", o + n),
            u.src = e),
            r[e] = [t];
            var s = function(t, n) {
                u.onerror = u.onload = null,
                clearTimeout(p);
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
              , p = setTimeout(s.bind(null, void 0, {
                type: "timeout",
                target: u
            }), 12e4);
            u.onerror = s.bind(null, u.onerror),
            u.onload = s.bind(null, u.onload),
            c && document.head.appendChild(u)
        }
    }
    ,
    a.r = function(e) {
        "undefined" != typeof Symbol && Symbol.toStringTag && Object.defineProperty(e, Symbol.toStringTag, {
            value: "Module"
        }),
        Object.defineProperty(e, "__esModule", {
            value: !0
        })
    }
    ,
    a.nmd = function(e) {
        return e.paths = [],
        e.children || (e.children = []),
        e
    }
    ,
    a.p = "//fe-static.xhscdn.com/formula-static/xhs-pc-web/public/",
    function() {
        if ("undefined" != typeof document) {
            var e = function(e) {
                return new Promise((function(t, n) {
                    var r = a.miniCssF(e)
                      , o = a.p + r;
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
                        a.nc && (i.nonce = a.nc),
                        i.onerror = i.onload = function(n) {
                            if (i.onerror = i.onload = null,
                            "load" === n.type)
                                r();
                            else {
                                var u = n && n.type
                                  , a = n && n.target && n.target.href || t
                                  , c = new Error("Loading CSS chunk " + e + " failed.\n(" + u + ": " + a + ")");
                                c.name = "ChunkLoadError",
                                c.code = "CSS_CHUNK_LOAD_FAILED",
                                c.type = u,
                                c.request = a,
                                i.parentNode && i.parentNode.removeChild(i),
                                o(c)
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
            a.f.miniCss = function(n, r) {
                t[n] ? r.push(t[n]) : 0 !== t[n] && {
                    94: 1,
                    144: 1,
                    180: 1,
                    226: 1,
                    256: 1,
                    270: 1,
                    290: 1,
                    406: 1,
                    464: 1,
                    756: 1,
                    763: 1,
                    895: 1,
                    898: 1
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
        var e = {
            577: 0
        };
        a.f.j = function(t, n) {
            var r = a.o(e, t) ? e[t] : void 0;
            if (0 !== r)
                if (r)
                    n.push(r[2]);
                else if (577 != t) {
                    var o = new Promise((function(n, o) {
                        r = e[t] = [n, o]
                    }
                    ));
                    n.push(r[2] = o);
                    var i = a.p + a.u(t)
                      , u = new Error;
                    a.l(i, (function(n) {
                        if (a.o(e, t) && (0 !== (r = e[t]) && (e[t] = void 0),
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
        a.O.j = function(t) {
            return 0 === e[t]
        }
        ;
        var t = function(t, n) {
            var r, o, i = n[0], u = n[1], c = n[2], f = 0;
            if (i.some((function(t) {
                return 0 !== e[t]
            }
            ))) {
                for (r in u)
                    a.o(u, r) && (a.m[r] = u[r]);
                if (c)
                    var d = c(a)
            }
            for (t && t(n); f < i.length; f++)
                o = i[f],
                a.o(e, o) && e[o] && e[o][0](),
                e[o] = 0;
            return a.O(d)
        }
          , n = self.webpackChunkxhs_pc_web = self.webpackChunkxhs_pc_web || [];
        n.forEach(t.bind(null, 0)),
        n.push = t.bind(null, n.push.bind(n))
    }()
    zc = a
}();

//# sourceMappingURL=https://picasso-private-1251524319.cos.ap-shanghai.myqcloud.com/data/formula-static/formula/xhs-pc-web/runtime-main.80d27af.js.map
var CHARSET = "abcdefghijklmnopqrstuvwxyz1234567890", LOCAL_ID_SECRET_VERSION = "0"

concat_default = zc.n(zc(93966))
map_default = zc.n(zc(79346))
fill_default = zc.n(zc(70119))
const PlatformCode = {
    "0": "Windows",
    "1": "iOS",
    "2": "Android",
    "3": "MacOs",
    "4": "Linux",
    "5": "other",
    "Windows": 0,
    "iOS": 1,
    "Android": 2,
    "MacOs": 3,
    "Linux": 4,
    "other": 5
}
var crc32 = function(t) {
    for (var e, r = [], n = 0; n < 256; n++) {
        e = n;
        for (var o = 0; o < 8; o++)
            e = 1 & e ? 3988292384 ^ e >>> 1 : e >>> 1;
        r[n] = e
    }
    for (var i = -1, a = 0; a < t.length; a++)
        i = i >>> 8 ^ r[255 & (i ^ t.charCodeAt(a))];
    return ~i >>> 0
};
function genRandomString(t) {
    var e, r;
    return map_default()(e = fill_default()(r = Array(t)).call(r, void 0)).call(e, (function() {
        return CHARSET[Math.floor(36 * Math.random())]
    }
    )).join("")
}
function generateLocalId(t) {
    var e, r, n, o, i, a = getPlatformCode(t), u = concat_default()(e = concat_default()(r = concat_default()(n = concat_default()(o = "".concat((+new Date).toString(16))).call(o, genRandomString(30))).call(n, a)).call(r, LOCAL_ID_SECRET_VERSION)).call(e, "000"), s = crc32(u);
    return concat_default()(i = "".concat(u)).call(i, s).substring(0, 52)
}
function getPlatformCode(t) {
    switch (t) {
    case "Android":
        return PlatformCode.Android;
    case "iOS":
        return PlatformCode.iOS;
    case "Mac OS":
        return PlatformCode.MacOs;
    case "Linux":
        return PlatformCode.Linux;
    default:
        return PlatformCode.other
    }
}

console.log(generateLocalId("Windows"));