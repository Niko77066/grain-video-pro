# 引擎知识包 · GSAP 供给纪律 + fallback shim（seek 驱动生命周期全表）

> 何时读我：compose 用到 `gsap.timeline()` / 往 `window.__timelines` 注册时钟时。
> 白板类（whiteboard-generalist / typography-led）兜底合成尤其必读——本文件是
> `e2e-post-less` 那次 `n.timeScale is not a function`（capture rc=1）的根因收口。

## 0. 根因（先读，别再犯）

渲染机的 **seek 驱动**会对注册到 `window.__timelines[compositionId]` 的每条时间线
**逐帧寻位**，并在寻位前后调用一批**生命周期方法做归一**（把 timeScale 归 1、pause、
必要时 invalidate/eventCallback）。真 GSAP 时间线实现了全部这些方法，所以自带真
`gsap.min.js` 的片子从不踩坑。

**手搓的 `window.gsap` shim（如临时写的 `MiniTimeline`）一旦漏实现其中任一方法**，
渲染机在 `capture_disk` 阶段调到它就崩：

```
[Browser:PAGEERROR] n.timeScale is not a function   → exitCode 1，整条渲染报废
```

不同 `hyperframesVersion` 调的方法集会变（0.7.3 实测会调 `timeScale`），所以
**"补齐当前报错的那一个方法"不是修复**——下个版本换调别的方法又崩。真正的收口是
下面两条纪律之一，二选一，`tools/lint.py` 的 `compose.lint` 门机械把关（缺则 error、禁渲染）。

## 1. 首选：自带真 GSAP（版本无关，golden 全走这条）

所有 golden 合成与 `projects/ac-26-live` 都是这么做的——**版本无关，永不因引擎升级而崩**：

```html
<!-- <head> 里，早于所有时间线脚本 -->
<script src="assets/gsap.min.js"></script>
```

把真 gsap.min.js 拷进 compose 资产目录（仓内规范来源 `assets/gsap.min.js`，GSAP 3.14.2，72KB）：

```bash
cp assets/gsap.min.js <你的project>/compose/assets/gsap.min.js
```

渲染机 tar 只带 compose 目录 → 用**相对路径** `assets/gsap.min.js`，禁 CDN。
72KB 打进 tar 完全在预算内（渲染契约 11M 级 tar 实测可用）。

## 2. 兜底：完整 fallback shim（万不得已自包含时用整块，别删方法）

只有在**确实不能自带 gsap.min.js**（极致自包含场景）时才用 shim。用就用**下面这一整块**，
它实现了 seek 驱动会调的**生命周期全表**（寻位 `seek/totalTime/time`；归一
`timeScale/pause/paused/play/resume/restart/kill/invalidate/eventCallback/progress/duration`）。
**任何一个方法都不许删**——删哪个，渲染机某个版本调到就崩。

shim 覆盖白板类常用属性：`opacity` / `x` / `y` / `z` / `scale(XY)` / `rotation` /
`skew(XY)` / 任意数值 style（width/height/top/left/blur…）。颜色/路径类补间用真 GSAP。

```html
<!-- ══════════════════════════════════════════════════════════════════════════
     GSAP fallback shim（seek-safe / 确定性）· 仅当 compose 未自带真 gsap.min.js 时兜底。
     渲染机 seek 驱动会对 window.__timelines[...] 的时间线逐帧调用下列方法，
     缺任一即 [Browser:PAGEERROR] …is not a function → capture_disk 阶段 rc=1：
       寻位：   seek(t) / totalTime(t) / time(t)
       生命周期：timeScale(v) / pause() / paused() / play() / resume() /
                restart() / kill() / invalidate() / eventCallback() / progress() / duration()
     ══════════════════════════════════════════════════════════════════════════ -->
<script>
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
</script>
```

### shim 已知边界（越界就必须走第 1 节自带真 GSAP）

- 只插值**数值**属性（transform / opacity / 数值 style）；颜色、路径 `d`、SVG morph、
  文字逐字打字机等**非数值补间**不支持。
- 同一元素同一属性被**多条 tween 链式接力**（后一条从前一条落点续）时，本 shim 的起点在
  构造期一次性从 CSS 基线解析，不会自动接力——链式接力需求请自带真 GSAP。
- 不支持 `repeat` / `yoyo` / 物理插件 / MotionPath。

## 3. 机械门（`tools/lint.py` · compose.lint）

`compose.lint` 门在渲染前机械检查：**compose 用了 gsap / 注册了 `__timelines`**，就必须
**要么**自带在盘的真 `assets/gsap.min.js`，**要么**内联 shim 且实现生命周期全表；
两者皆无、或 shim 漏方法 → **error，禁渲染**（不浪费一次远端渲染才发现 PAGEERROR）。
本文件第 1/2 节任一条做到位即过门。
