// Minimal JS implementation: only signXs (random mode)
// Dependencies: Node.js crypto (built-in)
// Usage:
//   const { signXs } = require('./xhshow_min');
//   const xs = signXs('POST','/api/sns/web/v1/homefeed', a1Value, 'xhs-pc-web', payload);
//   console.log(xs);

const crypto = require("crypto");

const CONFIG = {
  BASE58_ALPHABET:
    "NOPQRStuvwxWXYZabcyz012DEFTKLMdefghijkl4563GHIJBC7mnop89+/AUVqrsOPQefghijkABCDEFGuvwz0123456789xy",
  CUSTOM_BASE64_ALPHABET:
    "ZmserbBoHQtNP+wOcza/LpngG8yJq42KWYj0DSfdikx3VT16IlUAFM97hECvuRX5",
  STANDARD_BASE64_ALPHABET:
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/",
  HEX_KEY:
    "af572b95ca65b2d9ec76bb5d2e97cb653299cc663399cc663399cce673399cce6733190c06030100000000008040209048241289c4e271381c0e0703018040a05028148ac56231180c0683c16030984c2693c964b259ac56abd5eaf5fafd7e3f9f4f279349a4d2e9743a9d4e279349a4d2e9f47a3d1e8f47239148a4d269341a8d4623110884422190c86432994ca6d3e974baddee773b1d8e47a35128148ac5623198cce6f3f97c3e1f8f47a3d168b45aad562b158ac5e2f1f87c3e9f4f279349a4d269b45aad56",
  VERSION_BYTES: [119, 104, 96, 41],
  TIMESTAMP_XOR_KEY: 41,
  FIXED_INT_VALUE_1: 15,
  FIXED_INT_VALUE_2: 1291,
  STARTUP_TIME_OFFSET_MIN: 1000,
  STARTUP_TIME_OFFSET_MAX: 4000,
  ENV_STATIC_BYTES: [
    1, 249, 83, 102, 103, 201, 181, 131, 99, 94, 7, 68, 250, 132, 21,
  ],
  X3_PREFIX: "mns0101_",
  XYS_PREFIX: "XYS_",
  TEMPLATE: {
    x0: "4.2.6",
    x1: "xhs-pc-web",
    x2: "Windows",
    x3: "",
    x4: "object",
  },
};

function rand32() {
  const buf = crypto.randomBytes(4);
  return buf.readUInt32LE(0);
}
function randByte(min = 0, max = 255) {
  return min + (rand32() % (max - min + 1));
}
function intToLE(val, len = 4) {
  const out = [];
  let v = val >>> 0;
  for (let i = 0; i < len; i++) {
    out.push(v & 0xff);
    v >>= 8;
  }
  return out;
}
function bytesFromHex(hex) {
  const out = [];
  for (let i = 0; i < hex.length; i += 2)
    out.push(parseInt(hex.slice(i, i + 2), 16));
  return out;
}
const HEX_KEY_BYTES = bytesFromHex(CONFIG.HEX_KEY);
function xorArray(arr) {
  return arr.map((b, i) => (b ^ HEX_KEY_BYTES[i]) & 0xff);
}
function encodeTimestamp(ts) {
  const raw = intToLE(ts, 8);
  return raw
    .map((b, i) => (b ^ CONFIG.TIMESTAMP_XOR_KEY) & 0xff)
    .map((b, i) => (i === 0 ? randByte(0, 255) : b));
}
function base58Encode(bytes) {
  let zeros = 0;
  for (const b of bytes) {
    if (b === 0) zeros++;
    else break;
  }
  let num = 0n;
  for (const b of bytes) num = num * 256n + BigInt(b);
  const chars = [];
  const A = CONFIG.BASE58_ALPHABET;
  while (num > 0n) {
    const div = num / 58n;
    const rem = num % 58n;
    chars.push(A[Number(rem)]);
    num = div;
  }
  for (let i = 0; i < zeros; i++) chars.push(A[0]);
  return chars.reverse().join("");
}
function b64CustomEncode(s) {
  const std = Buffer.from(s, "utf-8").toString("base64");
  let out = "";
  const SA = CONFIG.STANDARD_BASE64_ALPHABET,
    CA = CONFIG.CUSTOM_BASE64_ALPHABET;
  for (const ch of std) {
    const idx = SA.indexOf(ch);
    out += idx !== -1 ? CA[idx] : ch;
  }
  return out;
}
function buildContentString(method, uri, payload) {
  payload = payload || {};
  if (method === "POST") return uri + JSON.stringify(payload);
  const keys = Object.keys(payload);
  if (!keys.length) return uri;
  return (
    uri +
    "?" +
    keys
      .map((k) =>
        Array.isArray(payload[k])
          ? `${k}=${payload[k].join(",")}`
          : `${k}=${payload[k] ?? ""}`
      )
      .join("&")
  );
}
function md5Hex(s) {
  return crypto.createHash("md5").update(s, "utf8").digest("hex");
}
function buildPayload(dHex, a1, appId, content) {
  const randNum = rand32();
  const ts = Date.now();
  const startupTs =
    ts -
    (CONFIG.STARTUP_TIME_OFFSET_MIN +
      randByte(
        0,
        CONFIG.STARTUP_TIME_OFFSET_MAX - CONFIG.STARTUP_TIME_OFFSET_MIN
      ));
  const arr = [];
  arr.push(...CONFIG.VERSION_BYTES);
  const randBytes = intToLE(randNum, 4);
  arr.push(...randBytes);
  const xorKey = randBytes[0];
  arr.push(...encodeTimestamp(ts));
  arr.push(...intToLE(startupTs, 8));
  arr.push(...intToLE(CONFIG.FIXED_INT_VALUE_1));
  arr.push(...intToLE(CONFIG.FIXED_INT_VALUE_2));
  const strLen = Buffer.from(content, "utf-8").length;
  arr.push(...intToLE(strLen));
  const md5Bytes = bytesFromHex(dHex);
  arr.push(...md5Bytes.slice(0, 8).map((b) => b ^ xorKey));
  const a1Buf = Buffer.from(a1, "utf-8");
  arr.push(a1Buf.length, ...a1Buf);
  const appBuf = Buffer.from(appId, "utf-8");
  arr.push(appBuf.length, ...appBuf);
  arr.push(
    CONFIG.ENV_STATIC_BYTES[0],
    randByte(0, 255),
    ...CONFIG.ENV_STATIC_BYTES.slice(1)
  );
  return arr;
}
function signXs(
  method,
  uri,
  a1Value,
  xsecAppid = "xhs-pc-web",
  payload = null
) {
  method = method.toUpperCase();
  const content = buildContentString(method, uri, payload);
  const dVal = md5Hex(content);
  const payloadArr = buildPayload(
    dVal,
    a1Value.trim(),
    xsecAppid.trim(),
    content
  );
  const xorBytes = xorArray(payloadArr);
  const x3Body = base58Encode(xorBytes);
  const x3Full = CONFIG.X3_PREFIX + x3Body;
  const jsonCompact = JSON.stringify({ ...CONFIG.TEMPLATE, x3: x3Full });
  const encoded = b64CustomEncode(jsonCompact);
  return CONFIG.XYS_PREFIX + encoded;
}
for (
  var c = [],
    d = "ZmserbBoHQtNP+wOcza/LpngG8yJq42KWYj0DSfdikx3VT16IlUAFM97hECvuRX5",
    s = 0,
    f = d.length;
  s < f;
  ++s
)
  c[s] = d[s];
function tripletToBase64(e) {
  return c[(e >> 18) & 63] + c[(e >> 12) & 63] + c[(e >> 6) & 63] + c[63 & e];
}
function encodeChunk(e, a, r) {
  for (var c, d = [], s = a; s < r; s += 3)
    (c =
      ((e[s] << 16) & 0xff0000) + ((e[s + 1] << 8) & 65280) + (255 & e[s + 2])),
      d.push(tripletToBase64(c));
  return d.join("");
}
function encodeUtf8(e) {
  for (var a = encodeURIComponent(e), r = [], c = 0; c < a.length; c++) {
    var d = a.charAt(c);
    if ("%" === d) {
      var s = parseInt(a.charAt(c + 1) + a.charAt(c + 2), 16);
      r.push(s), (c += 2);
    } else r.push(d.charCodeAt(0));
  }
  return r;
}
function b64Encode(e) {
  for (
    var a, r = e.length, d = r % 3, s = [], f = 16383, u = 0, l = r - d;
    u < l;
    u += f
  )
    s.push(encodeChunk(e, u, u + f > l ? l : u + f));
  return (
    1 === d
      ? ((a = e[r - 1]), s.push(c[a >> 2] + c[(a << 4) & 63] + "=="))
      : 2 === d &&
        ((a = (e[r - 2] << 8) + e[r - 1]),
        s.push(c[a >> 10] + c[(a >> 4) & 63] + c[(a << 2) & 63] + "=")),
    s.join("")
  );
}

var gens9 = (function (e) {
  for (var a = 0xedb88320, r, c, d = 256, s = []; d--; s[d] = r >>> 0)
    for (c = 8, r = d; c--; ) r = 1 & r ? (r >>> 1) ^ a : r >>> 1;
  return function (e) {
    if ("string" == typeof e) {
      for (var r = 0, c = -1; r < e.length; ++r)
        c = s[(255 & c) ^ e.charCodeAt(r)] ^ (c >>> 8);
      return -1 ^ c ^ a;
    }
    for (var r = 0, c = -1; r < e.length; ++r)
      c = s[(255 & c) ^ e[r]] ^ (c >>> 8);
    return -1 ^ c ^ a;
  };
})();

const fff =
  "I38rHdgsjopgIvesdVwgIC+oIELmBZ5e3VwXLgFTIxS3bqwErFeexd0ekncAzMFYnqthIhJeSnMDKutRI3KsYorWHPtGrbV0P9WfIi/eWc6eYqtyQApPI37ekmR6QL+5Ii6sdneeSfqYHqwl2qt5B0DBIx++GDi/sVtkIxdsxuwr4qtiIhuaIE3e3LV0I3VTIC7e0utl2ADmsLveDSKsSPw5IEvsiVtJOqw8BuwfPpdeTFWOIx4TIiu6ZPwbPut5IvlaLbgs3qtxIxes1VwHIkumIkIyejgsY/WTge7eSqte/D7sDcpipedeYrDtIC6eDVw2IENsSqtlnlSuNjVtIvoekqt3cZ7sVo4gIESyIhE4NnquIxhnqz8gIkIfoqwkICZW8g3sdlOeVPw3IvAe0fged0YyIi5s3Mc52utAIiKsidvekZNeTPt4nAOeWPwEIvSzaAdeSVwXpnesDqwmI3TrIxE5Luwwaqw+rekhZANe1MNe0Pw9ICNsVLoeSbIFIkosSr7sVnFiIkgsVVtMIiudqqw+tqtWI30e3PwIIhoe3ut1IiOsjut3wutnsPwXICclI3Ir27lk2I5e1utCIES/IEJs0PtnpYIAO0JeYfD1IErPOPtKoqw3I3OexqtWQL5eiz0sVSEyIEJekd/skPtsnPwqICJeSPwiIh5eVAuLIv5eYo/e0PtSICKsVqwV4omqI3RIIkge0e0sYZ0si/7eiuwSIvTeIhqmGuwCIkrPIx0edUzbzbveTPw5IxI0yVwImZeedM0eWVwmeqt2IiM9IhhQLqwJPqtbIxZ=";
function XsCommon(a1, xs, xt) {
  let d = {
    s0: 5,
    s1: "",
    x0: "1",
    x1: "4.2.6",
    x2: "Windows",
    x3: "xhs-pc-web",
    x4: "4.84.1",
    x5: a1,
    x6: xt,
    x7: xs,
    x8: fff,
    x9: gens9(xt.toString() + xs + fff),
    x10: 0,
    x11: "normal",
  };
  let dataStr = JSON.stringify(d);
  return b64Encode(encodeUtf8(dataStr));
}

function get_request_headers_params(api, data, a1) {
  let xs_xt = signXs("POST", api, a1, "xhs-pc-web", data);
  let xs = xs_xt;
  let xt = new Date().getTime();
  let xs_common = XsCommon(a1, xs, xt);
  return {
    xs: xs,
    xt: xt,
    xs_common: xs_common,
  };
}


if (typeof module !== "undefined") {
  module.exports = {
    signXs,
    get_request_headers_params,
  };
}
