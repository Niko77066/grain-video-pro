// GSAP fallback shim（seek-safe / 确定性）——仅当 compose 无法自带真 assets/gsap.min.js 时兜底。
// 首选永远是自带真 GSAP（版本无关，golden 全走那条）；本文件是万不得已自包含那条路的整块实现。
// 用法：整块内联进 composition 的 <script> 里。**别删任何方法**——渲染机 seek 驱动会调生命周期全表：
//   寻位 seek/totalTime/time；生命周期 timeScale/pause/paused/play/resume/restart/kill/
//   invalidate/eventCallback/progress/duration。漏一个 → [Browser:PAGEERROR] → capture rc=1。
// 覆盖：opacity / x / y / z / scale(XY) / rotation / skew(XY) / 任意数值 style；
//   颜色与路径类补间不支持——那些必须用真 GSAP。
// 机器门：tools/kuleshov-lint.py ⑥。说明与验收见 .claude/skills/produce/references/gsap-fallback-shim.md

(function () {
  if (window.gsap && window.gsap.timeline) return;          // 真 GSAP 在场则让位，不覆盖

  var TRANSFORM = { x:1, y:1, z:1, rotation:1, rotationX:1, rotationY:1,
                    scale:1, scaleX:1, scaleY:1, skewX:1, skewY:1 };
  var EASE = {
    none:         function (p){ return p; },
    linear:       function (p){ return p; },
    'power1.out': function (p){ return 1 - Math.pow(1 - p, 2); },
    'power2.out': function (p){ return 1 - Math.pow(1 - p, 3); },
    'power3.out': function (p){ return 1 - Math.pow(1 - p, 4); },
    'power4.out': function (p){ return 1 - Math.pow(1 - p, 5); },
    'power1.in':  function (p){ return p * p; },
    'power2.in':  function (p){ return p * p * p; },
    'power2.inOut': function (p){ return p < .5 ? 2*p*p : 1 - Math.pow(-2*p + 2, 2) / 2; },
    'sine.inOut':   function (p){ return -(Math.cos(Math.PI * p) - 1) / 2; },
    'back.out':     function (p){ var c = 1.70158, c3 = c + 1;
                                  return 1 + c3 * Math.pow(p - 1, 3) + c * Math.pow(p - 1, 2); }
  };
  function ease(e){ return typeof e === 'function' ? e : (EASE[e] || EASE['power2.out']); }
  function nodes(t){
    if (!t) return [];
    if (typeof t === 'string') return [].slice.call(document.querySelectorAll(t));
    if (t.nodeType) return [t];
    if (t.length != null && typeof t.length === 'number') return [].slice.call(t);
    return [t];
  }
  function readProp(el, k){
    var d = el.__mt || (el.__mt = {});
    if (k in TRANSFORM){
      if (d[k] != null) return d[k];
      return (k === 'scale' || k === 'scaleX' || k === 'scaleY') ? 1 : 0;
    }
    if (k === 'opacity'){ var o = getComputedStyle(el).opacity; return o === '' ? 1 : parseFloat(o); }
    var cs = parseFloat(getComputedStyle(el)[k]);
    return isNaN(cs) ? 0 : cs;
  }
  function writeTransform(el){
    var d = el.__mt || {}, p = [];
    if (d.x || d.y || d.z) p.push('translate3d(' + (d.x||0) + 'px,' + (d.y||0) + 'px,' + (d.z||0) + 'px)');
    if (d.rotation)  p.push('rotate('  + d.rotation  + 'deg)');
    if (d.rotationX) p.push('rotateX(' + d.rotationX + 'deg)');
    if (d.rotationY) p.push('rotateY(' + d.rotationY + 'deg)');
    if (d.skewX)     p.push('skewX('   + d.skewX     + 'deg)');
    if (d.skewY)     p.push('skewY('   + d.skewY     + 'deg)');
    var sx = d.scaleX != null ? d.scaleX : (d.scale != null ? d.scale : 1);
    var sy = d.scaleY != null ? d.scaleY : (d.scale != null ? d.scale : 1);
    if (sx !== 1 || sy !== 1) p.push('scale(' + sx + ',' + sy + ')');
    el.style.transform = p.join(' ');
  }
  function applyProp(el, k, v){
    if (k in TRANSFORM){ (el.__mt || (el.__mt = {}))[k] = v; writeTransform(el); }
    else if (k === 'opacity') el.style.opacity = v;
    else el.style[k] = /zIndex|opacity|lineHeight|fontWeight|order|flexGrow|zoom/i.test(k) ? v : v + 'px';
  }

  var CTRL = { duration:1, ease:1, delay:1, stagger:1, paused:1, defaults:1, repeat:1,
               yoyo:1, immediateRender:1, onComplete:1, onStart:1, onUpdate:1, id:1 };

  function Timeline(vars){
    vars = vars || {};
    this.tweens = []; this.cursor = 0; this.dur = 0; this._t = 0; this._ts = 1;
    this._paused = !!vars.paused; this.defaults = vars.defaults || {};
    this.labels = {}; this._lastStart = 0;
  }
  Timeline.prototype._pos = function (position){
    if (position == null) return this.cursor;
    if (typeof position === 'number') return position;
    if (position === '<') return this._lastStart;
    if (position === '>') return this.cursor;
    var m = /^([+-])=([0-9.]+)/.exec(position);
    if (m) return this.cursor + (m[1] === '-' ? -1 : 1) * parseFloat(m[2]);
    if (this.labels[position] != null) return this.labels[position];
    return this.cursor;
  };
  Timeline.prototype._add = function (targets, varsA, varsB, position){
    var v = varsB || varsA;
    var dur = v.duration != null ? v.duration
            : (this.defaults.duration != null ? this.defaults.duration : 0.5);
    var eas = ease(v.ease || this.defaults.ease);
    var stg = typeof v.stagger === 'number' ? v.stagger : 0;
    var from = {}, to = {}, k;
    if (varsB){                                   // fromTo(a, b)
      for (k in varsA) if (!(k in CTRL)) from[k] = varsA[k];
      for (k in varsB) if (!(k in CTRL)) to[k]   = varsB[k];
    } else if (v.__from){                         // from(vars)：vars 是起点，终点=元素基线
      for (k in varsA) if (!(k in CTRL)) from[k] = varsA[k];
    } else {                                       // to(vars) / set(vars)：起点=基线，终点=vars
      for (k in varsA) if (!(k in CTRL)) to[k]   = varsA[k];
    }
    var st = this._pos(position) + (v.delay || 0);
    this._lastStart = st;
    var els = nodes(targets), base = [];
    els.forEach(function (el, i){
      var seg = {}, props = {}, p;
      for (p in from) props[p] = 1;
      for (p in to)   props[p] = 1;
      for (p in props){
        var b = readProp(el, p);
        seg[p] = { f: (p in from ? from[p] : b), t: (p in to ? to[p] : b) };
      }
      base[i] = seg;
    });
    var tw = { els: els, base: base, start: st, dur: dur, ease: eas, stagger: stg };
    this.tweens.push(tw);
    var end = st + dur + Math.max(0, els.length - 1) * stg;
    this.cursor = end; if (end > this.dur) this.dur = end;
    return this;
  };
  Timeline.prototype.to     = function (t, v, p){ return this._add(t, v, null, p); };
  Timeline.prototype.from   = function (t, v, p){ v = v || {}; v.__from = 1; return this._add(t, v, null, p); };
  Timeline.prototype.fromTo = function (t, a, b, p){ return this._add(t, a, b, p); };
  Timeline.prototype.set    = function (t, v, p){ v = v || {}; v.duration = 0; return this._add(t, v, null, p); };
  Timeline.prototype.add    = function (label, p){ if (typeof label === 'string') this.labels[label] = this._pos(p); return this; };
  Timeline.prototype.addLabel = Timeline.prototype.add;
  Timeline.prototype.call   = function (){ return this; };   // 确定性渲染下不派发运行时回调

  // ── seek 驱动核心：从每条 tween 的 from/to 全量重算，幂等、支持任意顺序 seek ──
  Timeline.prototype.seek = function (t){
    this._t = t;
    for (var n = 0; n < this.tweens.length; n++){
      var tw = this.tweens[n];
      for (var i = 0; i < tw.els.length; i++){
        var el = tw.els[i], seg = tw.base[i] || {}, st = tw.start + i * tw.stagger;
        var raw = tw.dur > 0 ? (t - st) / tw.dur : (t >= st ? 1 : 0);
        var p = raw < 0 ? 0 : (raw > 1 ? 1 : raw);   // clamp：起点前=f、终点后=t，全程幂等
        p = tw.ease(p);
        for (var prop in seg) applyProp(el, prop, seg[prop].f + (seg[prop].t - seg[prop].f) * p);
      }
    }
    return this;
  };
  // 寻位别名 + 生命周期全表（渲染机 seek 驱动会调；缺一即 PAGEERROR）——一律链式返回 this
  Timeline.prototype.time      = function (t){ return arguments.length ? this.seek(t) : this._t; };
  Timeline.prototype.totalTime = function (t){ return arguments.length ? this.seek(t) : this._t; };
  Timeline.prototype.progress  = function (v){ return arguments.length ? this.seek((v || 0) * this.dur) : (this.dur ? this._t / this.dur : 0); };
  Timeline.prototype.duration      = function (){ return this.dur; };
  Timeline.prototype.totalDuration = function (){ return this.dur; };
  Timeline.prototype.timeScale = function (v){ return arguments.length ? this : this._ts; };  // 确定性渲染忽略变速；带参返回 this 保链式
  Timeline.prototype.pause     = function (){ this._paused = true;  return this; };
  Timeline.prototype.play      = function (){ this._paused = false; return this; };
  Timeline.prototype.resume    = function (){ this._paused = false; return this; };
  Timeline.prototype.paused    = function (v){ return arguments.length ? (this._paused = !!v, this) : this._paused; };
  Timeline.prototype.restart   = function (){ return this.seek(0); };
  Timeline.prototype.kill      = function (){ return this; };
  Timeline.prototype.invalidate   = function (){ return this; };
  Timeline.prototype.eventCallback = function (){ return this; };
  Timeline.prototype.then      = function (){ return Promise.resolve(this); };

  var gsap = {
    timeline: function (vars){ return new Timeline(vars); },
    to:     function (t, v){ return new Timeline().to(t, v); },
    from:   function (t, v){ return new Timeline().from(t, v); },
    fromTo: function (t, a, b){ return new Timeline().fromTo(t, a, b); },
    set:    function (t, v){ var tl = new Timeline(); tl.set(t, v); return tl.seek(0); },
    registerPlugin: function (){}, config: function (){}, defaults: function (){},
    getProperty: function (el, k){ return readProp(nodes(el)[0], k); },
    utils: { toArray: nodes, clamp: function (a, b, v){ return Math.max(a, Math.min(b, v)); } }
  };
  window.gsap = gsap;
})();
