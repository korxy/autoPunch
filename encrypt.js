function encrypt(r) {
	var n = 8
	  , t = 0;
	function e(r, n) {
		var t = (65535 & r) + (65535 & n), e;
		return (r >> 16) + (n >> 16) + (t >> 16) << 16 | 65535 & t
	}
	function o(r, n) {
		return r >>> n | r << 32 - n
	}
	function a(r, n) {
		return r >>> n
	}
	function u(r, n, t) {
		return r & n ^ ~r & t
	}
	function f(r, n, t) {
		return r & n ^ r & t ^ n & t
	}
	function c(r) {
		return o(r, 2) ^ o(r, 13) ^ o(r, 22)
	}
	function i(r) {
		return o(r, 6) ^ o(r, 11) ^ o(r, 25)
	}
	function h(r) {
		return o(r, 7) ^ o(r, 18) ^ a(r, 3)
	}
	function g(r) {
		return o(r, 17) ^ o(r, 19) ^ a(r, 10)
	}
	function C(r, n) {
		var t = new Array(1116352408,1899447441,3049323471,3921009573,961987163,1508970993,2453635748,2870763221,3624381080,310598401,607225278,1426881987,1925078388,2162078206,2614888103,3248222580,3835390401,4022224774,264347078,604807628,770255983,1249150122,1555081692,1996064986,2554220882,2821834349,2952996808,3210313671,3336571891,3584528711,113926993,338241895,666307205,773529912,1294757372,1396182291,1695183700,1986661051,2177026350,2456956037,2730485921,2820302411,3259730800,3345764771,3516065817,3600352804,4094571909,275423344,430227734,506948616,659060556,883997877,958139571,1322822218,1537002063,1747873779,1955562222,2024104815,2227730452,2361852424,2428436474,2756734187,3204031479,3329325298), o = new Array(1779033703,3144134277,1013904242,2773480762,1359893119,2600822924,528734635,1541459225), a = new Array(64), C, v, d, m, A, l, S, k, y, P, w, b;
		r[n >> 5] |= 128 << 24 - n % 32,
		r[15 + (n + 64 >> 9 << 4)] = n;
		for (var y = 0; y < r.length; y += 16) {
			C = o[0],
			v = o[1],
			d = o[2],
			m = o[3],
			A = o[4],
			l = o[5],
			S = o[6],
			k = o[7];
			for (var P = 0; P < 64; P++)
				a[P] = P < 16 ? r[P + y] : e(e(e(g(a[P - 2]), a[P - 7]), h(a[P - 15])), a[P - 16]),
				w = e(e(e(e(k, i(A)), u(A, l, S)), t[P]), a[P]),
				b = e(c(C), f(C, v, d)),
				k = S,
				S = l,
				l = A,
				A = e(m, w),
				m = d,
				d = v,
				v = C,
				C = e(w, b);
			o[0] = e(C, o[0]),
			o[1] = e(v, o[1]),
			o[2] = e(d, o[2]),
			o[3] = e(m, o[3]),
			o[4] = e(A, o[4]),
			o[5] = e(l, o[5]),
			o[6] = e(S, o[6]),
			o[7] = e(k, o[7])
		}
		return o
	}
	function v(r) {
		for (var t = Array(), e = (1 << n) - 1, o = 0; o < r.length * n; o += n)
			t[o >> 5] |= (r.charCodeAt(o / n) & e) << 24 - o % 32;
		return t
	}
	function d(r) {
		for (var n = "", t = 0; t < r.length; t++) {
			var e = r.charCodeAt(t);
			e < 128 ? n += String.fromCharCode(e) : e > 127 && e < 2048 ? (n += String.fromCharCode(e >> 6 | 192),
			n += String.fromCharCode(63 & e | 128)) : (n += String.fromCharCode(e >> 12 | 224),
			n += String.fromCharCode(e >> 6 & 63 | 128),
			n += String.fromCharCode(63 & e | 128))
		}
		return n
	}
	function m(r) {
		for (var n = t ? "0123456789ABCDEF" : "0123456789abcdef", e = "", o = 0; o < 4 * r.length; o++)
			e += n.charAt(r[o >> 2] >> 8 * (3 - o % 4) + 4 & 15) + n.charAt(r[o >> 2] >> 8 * (3 - o % 4) & 15);
		return e
	}
	return m(C(v(r = d(r)), r.length * n))
}