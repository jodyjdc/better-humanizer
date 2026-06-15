// score.js — a faithful, dependency-free port of scripts/stylo.py `score()`.
// Pure (no DOM). Reads bands/lexicon/constants from globalThis.HP_DATA (web/data.js).
// Runs in the browser AND in node, so it can be validated against the Python scorer.
//
// Fidelity note: this mirrors stylo.py's algorithms and weights exactly. The only
// places it can differ slightly are (a) half-even vs half-up rounding at the 4th
// decimal, and (b) lexicon regexes that use Python-only syntax (wrapped in try/catch
// and skipped). Both have negligible effect on the composite distance. The canonical
// scorer is always scripts/stylo.py.
(function (root) {
  "use strict";

  var WORD_RE = /[A-Za-z]+(?:'[A-Za-z]+)?/g;
  var SENT_SPLIT_RE = /(?<=[.!?])\s+/;
  var EMOJI_RE = /[\u{1f000}-\u{1faff}\u{2600}-\u{27bf}\u{1f1e6}-\u{1f1ff}\u{2b00}-\u{2bff}]/gu;
  var BOLD_RE = /\*\*[^*\n]+\*\*/g;
  var RULE_OF_THREE_RE = /\b[\w']+,\s+[\w']+,?\s+and\s+[\w']+\b/gi;

  function D() { return root.HP_DATA; }
  function tokenize(t) { return t.toLowerCase().match(WORD_RE) || []; }
  function hasWord(s) { return /[A-Za-z]/.test(s); }
  function splitSentences(t) {
    return t.trim().split(SENT_SPLIT_RE).map(function (s) { return s.trim(); }).filter(hasWord);
  }
  function fmean(a) { return a.length ? a.reduce(function (x, y) { return x + y; }, 0) / a.length : 0; }
  function pstdev(a) {
    if (a.length <= 1) return 0;
    var m = fmean(a);
    return Math.sqrt(fmean(a.map(function (x) { return (x - m) * (x - m); })));
  }
  function round(x, n) { var f = Math.pow(10, n); return Math.round(x * f) / f; }

  function sentenceLengths(t) { return splitSentences(t).map(function (s) { return tokenize(s).length; }); }
  function burstiness(t) {
    var L = sentenceLengths(t);
    if (!L.length) return { mean: 0, sd: 0, cv: 0 };
    var mean = fmean(L), sd = L.length > 1 ? pstdev(L) : 0;
    return { mean: mean, sd: sd, cv: mean ? sd / mean : 0 };
  }

  function mtldOneDir(tokens, threshold) {
    if (!tokens.length) return 0;
    var factors = 0, types = new Set(), count = 0, ttr = 1.0, i, tok;
    for (i = 0; i < tokens.length; i++) {
      tok = tokens[i]; types.add(tok); count++; ttr = types.size / count;
      if (ttr <= threshold) { factors += 1; types = new Set(); count = 0; ttr = 1.0; }
    }
    if (count > 0) { var denom = 1 - threshold; factors += denom ? (1 - ttr) / denom : 0; }
    return factors > 0 ? tokens.length / factors : tokens.length;
  }
  function mtld(tokens) {
    if (!tokens.length) return 0;
    return (mtldOneDir(tokens, 0.72) + mtldOneDir(tokens.slice().reverse(), 0.72)) / 2;
  }
  function lexical(t) {
    var tokens = tokenize(t);
    if (!tokens.length) return { ttr: 0, mtld: 0, hapax_ratio: 0, mean_word_len: 0 };
    var types = {}, i;
    for (i = 0; i < tokens.length; i++) types[tokens[i]] = (types[tokens[i]] || 0) + 1;
    var nTypes = Object.keys(types).length;
    var hapax = Object.keys(types).filter(function (k) { return types[k] === 1; }).length;
    return {
      ttr: nTypes / tokens.length,
      mtld: mtld(tokens),
      hapax_ratio: nTypes ? hapax / nTypes : 0,
      mean_word_len: fmean(tokens.map(function (x) { return x.length; })),
    };
  }

  function countOcc(text, sub) {
    if (!sub) return 0;
    var c = 0, i = 0;
    while ((i = text.indexOf(sub, i)) !== -1) { c++; i += sub.length; }
    return c;
  }
  function per100(count, text) { var n = tokenize(text).length || 1; return count / n * 100; }
  function punctuation(text) {
    var em = countOcc(text, "—") + countOcc(text, " -- ");
    var raw = {
      comma: countOcc(text, ","), period: countOcc(text, "."), em_dash: em,
      en_dash: countOcc(text, "–"), semicolon: countOcc(text, ";"), colon: countOcc(text, ":"),
      paren: countOcc(text, "("), question: countOcc(text, "?"), exclaim: countOcc(text, "!"),
    };
    var out = {}, k;
    for (k in raw) out[k] = per100(raw[k], text);
    return out;
  }
  function contractionRate(text) {
    var t = tokenize(text), n = t.length || 1;
    return t.filter(function (x) { return x.indexOf("'") !== -1; }).length / n * 100;
  }
  function boldEmoji(text) {
    return { bold: (text.match(BOLD_RE) || []).length, emoji: (text.match(EMOJI_RE) || []).length };
  }
  function ruleOfThree(text) { return (text.match(RULE_OF_THREE_RE) || []).length; }

  function escapeRe(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }
  function countMatches(re, text) { var m = text.match(re); return m ? m.length : 0; }
  function tellHits(text, lexicon) {
    var low = text.toLowerCase(), out = {}, i, j, entry, count, term, rx, re;
    for (i = 0; i < lexicon.length; i++) {
      entry = lexicon[i]; count = 0;
      for (j = 0; j < (entry.terms || []).length; j++) {
        term = entry.terms[j];
        try { count += countMatches(new RegExp("(?<!\\w)" + escapeRe(term.toLowerCase()) + "(?!\\w)", "g"), low); } catch (e) {}
      }
      for (j = 0; j < (entry.regexes || []).length; j++) {
        rx = entry.regexes[j];
        try { re = new RegExp(rx, "gim"); count += countMatches(re, text); } catch (e) {}
      }
      out[entry.name] = count;
    }
    return out;
  }

  var PARA_SPLIT_RE = /\n\s*\n+/;
  function startsWith(sentence, phrases) {
    var s = sentence.replace(/^[ \t"'“‘(]+/, "").toLowerCase(), i, p;
    for (i = 0; i < phrases.length; i++) {
      p = phrases[i];
      if (s.lastIndexOf(p, 0) === 0 && (s.length === p.length || !/[a-z]/.test(s[p.length]))) return true;
    }
    return false;
  }
  function paragraphs(text) { return text.trim().split(PARA_SPLIT_RE).filter(hasWord); }
  function discourse(text) {
    var sents = splitSentences(text), nTok = tokenize(text).length || 1;
    var TO = D().constants.TRANSITION_OPENERS, SO = D().constants.STRUCTURAL_OPENERS;
    var trans = sents.filter(function (s) { return startsWith(s, TO); }).length;
    var struct = sents.filter(function (s) { return startsWith(s, SO); }).length;
    var paras = paragraphs(text), pcv = null;
    if (paras.length >= 2) {
      var plens = paras.map(function (p) { return tokenize(p).length; });
      var pmean = fmean(plens);
      pcv = pmean ? pstdev(plens) / pmean : 0;
    }
    return {
      transition_density: trans / nTok * 100,
      structural_opener_rate: sents.length ? struct / sents.length : 0,
      paragraph_cv: pcv,
    };
  }

  function fwVector(text) {
    var toks = tokenize(text), n = toks.length || 1;
    var fwset = new Set(D().constants.FUNCTION_WORDS), counts = {}, i, out = {}, k;
    for (i = 0; i < toks.length; i++) if (fwset.has(toks[i])) counts[toks[i]] = (counts[toks[i]] || 0) + 1;
    for (k in counts) out[k] = counts[k] / n;
    return out;
  }
  function cosineDistance(a, b) {
    var keys = {}, k, dot = 0;
    for (k in a) keys[k] = 1;
    for (k in b) keys[k] = 1;
    for (k in keys) dot += (a[k] || 0) * (b[k] || 0);
    var na = Math.sqrt(Object.keys(a).reduce(function (s, kk) { return s + a[kk] * a[kk]; }, 0));
    var nb = Math.sqrt(Object.keys(b).reduce(function (s, kk) { return s + b[kk] * b[kk]; }, 0));
    if (na === 0 || nb === 0) return 1.0;
    return 1 - dot / (na * nb);
  }

  function extractFeatures(text) {
    var b = burstiness(text), lx = lexical(text), p = punctuation(text), s = boldEmoji(text);
    return {
      sentence_length_mean: b.mean, sentence_length_cv: b.cv,
      mtld: lx.mtld, ttr: lx.ttr, hapax_ratio: lx.hapax_ratio,
      em_dash_rate: p.em_dash, comma_rate: p.comma, contraction_rate: contractionRate(text),
      rule_of_three: ruleOfThree(text), exclaim: p.exclaim,
      bold: s.bold, emoji: s.emoji,
    };
  }

  function score(text, register) {
    register = register || "spontaneous";
    var data = D(), reg = data.registers[register], bands = reg.bands || {}, C = data.constants;
    var OVER = new Set(C.OVER_CORRECTION);
    var feats = extractFeatures(text);
    var features = {}, selfTells = [], zs = [], name, floor, ceiling, width, val, status, z;

    for (name in feats) {
      if (!(name in bands)) continue;
      floor = bands[name].floor; ceiling = bands[name].ceiling;
      width = (ceiling - floor) || 1.0; val = feats[name];
      if (val < floor) { status = "below"; z = (val - floor) / width; }
      else if (val > ceiling) { status = "above"; z = (val - ceiling) / width; }
      else { status = "in"; z = 0.0; }
      features[name] = { value: round(val, 4), floor: floor, ceiling: ceiling, status: status, z: round(z, 4) };
      zs.push(Math.abs(z));
      if (status === "below" && OVER.has(name)) selfTells.push(name);
    }

    var fwDist = 0.0, refFw = reg.fw || {};
    if (Object.keys(refFw).length) fwDist = cosineDistance(fwVector(text), refFw);
    var styloOutlier = Object.keys(features).some(function (k) { return Math.abs(features[k].z) > 3; });

    var tells = tellHits(text, data.lexicon);
    var nTok = tokenize(text).length || 1;
    var tr = Object.keys(tells).reduce(function (a, k) { return a + tells[k]; }, 0) / nTok * 100;
    var trCeiling = (bands.tell_rate && bands.tell_rate.ceiling != null) ? bands.tell_rate.ceiling : 0.5;
    var trWidth = trCeiling || 1.0;
    features.tell_rate = {
      value: round(tr, 4), floor: 0.0, ceiling: trCeiling,
      status: tr > trCeiling ? "above" : "in", z: tr > trCeiling ? round((tr - trCeiling) / trWidth, 4) : 0.0,
    };
    var tellExcess = Math.max(0.0, tr - trCeiling);

    var disc = discourse(text);
    var regDefaults = C.DEFAULT_DISCOURSE_BANDS[register] || C.DEFAULT_DISCOURSE_BANDS._default;
    var discourseExcess = 0.0, i, band;
    for (i = 0; i < C.DISCOURSE_KEYS.length; i++) {
      name = C.DISCOURSE_KEYS[i]; val = disc[name];
      if (val === null || val === undefined) continue;
      band = bands[name] || regDefaults[name];
      floor = band.floor != null ? band.floor : 0.0;
      ceiling = band.ceiling;
      if (name === "paragraph_cv") {
        width = floor || 1.0;
        if (val < floor) { status = "below"; z = (floor - val) / width; discourseExcess += z; }
        else { status = "in"; z = 0.0; }
      } else {
        if (ceiling != null && val > ceiling) { width = ceiling || 1.0; status = "above"; z = (val - ceiling) / width; discourseExcess += z; }
        else { status = "in"; z = 0.0; }
      }
      features[name] = { value: round(val, 4), floor: floor, ceiling: (ceiling == null ? null : ceiling), status: status, z: round(z, 4) };
    }

    var base = zs.length ? fmean(zs) : 0.0;
    var styloDistance = base + fwDist + C.TELL_WEIGHT * tellExcess + C.SELF_TELL_WEIGHT * selfTells.length + C.DISCOURSE_WEIGHT * discourseExcess;

    return {
      register: register, calibrated: reg.calibrated || false,
      features: features, tells: tells, self_tell_flags: selfTells,
      stylo_distance: round(styloDistance, 4), stylo_outlier: styloOutlier,
    };
  }

  var api = { score: score, tokenize: tokenize };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  root.HPScore = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
