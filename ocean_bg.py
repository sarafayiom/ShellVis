import math
def _scallop():
    n = 9
    angs = [math.radians(-62 + 124 * i / n) for i in range(n + 1)]
    pts = [(50 + 46 * math.sin(a), 90 - 72 * math.cos(a)) for a in angs]
    d = f"M50 90 L{pts[0][0]:.1f} {pts[0][1]:.1f} "
    for i in range(1, n + 1):
        am = (angs[i - 1] + angs[i]) / 2
        cx, cy = 50 + 56 * math.sin(am), 90 - 88 * math.cos(am)
        d += f"Q{cx:.1f} {cy:.1f} {pts[i][0]:.1f} {pts[i][1]:.1f} "
    d += "Z"
    ribs = "".join(f"<path d='M50 88 L{x:.1f} {y:.1f}'/>" for x, y in pts)
    return (f"<symbol id='sh-scallop' viewBox='0 0 100 100'>"
            f"<path d='{d}' fill='url(#g-coral)' stroke='#b4553f' stroke-width='1.5'/>"
            f"<g stroke='#b4553f' stroke-opacity='.55' stroke-width='1.6' fill='none'>{ribs}</g>"
            f"<path d='M34 84 L66 84 L61 97 L39 97Z' fill='#f0c9a8' stroke='#b4553f' stroke-width='1'/>"
            f"</symbol>")

def _spiral():
    pts = " ".join(
        f"{50 + 3 * (i * .08) * math.cos(i * .08):.1f},{50 + 3 * (i * .08) * math.sin(i * .08):.1f}"
        for i in range(160))
    return (f"<symbol id='sh-spiral' viewBox='0 0 100 100'>"
            f"<circle cx='50' cy='50' r='43' fill='url(#g-spiral)' stroke='#8a6a3c' stroke-width='1.5'/>"
            f"<polyline points='{pts}' fill='none' stroke='#8a6a3c' stroke-opacity='.75' stroke-width='2.2' "
            f"stroke-linecap='round'/></symbol>")


def _cone():
    bands = ""
    for y in range(22, 100, 14):
        hw = 20 * (y - 4) / 96
        bands += f"<path d='M{30 - hw:.1f} {y} Q30 {y + 7} {30 + hw:.1f} {y}'/>"
    spots = "".join(
        f"<circle cx='{30 + dx}' cy='{y + 3}' r='1.4' fill='#fff8ea'/>"
        for y in range(28, 96, 14) for dx in (-6, 5))
    return (f"<symbol id='sh-cone' viewBox='0 0 60 120'>"
            f"<path d='M30 4 L50 100 Q30 118 10 100 Z' fill='url(#g-cone)' stroke='#7b4b26' stroke-width='1.4'/>"
            f"<g fill='none' stroke='#7b4b26' stroke-opacity='.6' stroke-width='1.6'>{bands}</g>{spots}</symbol>")


def _cowrie():
    spots = "".join(
        f"<circle cx='{x}' cy='{y}' r='{r}' fill='#7a4a28' fill-opacity='.35'/>"
        for x, y, r in [(26, 22, 3), (40, 14, 2.4), (62, 15, 3), (76, 24, 2.4), (30, 50, 2.6),
                        (50, 56, 3), (70, 50, 2.6), (50, 10, 2)])
    teeth = "".join(f"<path d='M{x} 30 L{x} 40' stroke='#6a3d1e' stroke-width='1'/>" for x in range(24, 78, 5))
    return (f"<symbol id='sh-cowrie' viewBox='0 0 100 70'>"
            f"<ellipse cx='50' cy='35' rx='45' ry='29' fill='url(#g-cow)' stroke='#8a5430' stroke-width='1.5'/>"
            f"{spots}<path d='M17 35 Q50 27 83 35 Q50 43 17 35Z' fill='#4a2a14'/>{teeth}</symbol>")


DEFS = (
    "<svg width='0' height='0' style='position:absolute'><defs>"
    "<radialGradient id='g-coral' cx='.5' cy='.85' r='.9'><stop offset='0' stop-color='#ffdcc6'/>"
    "<stop offset='.6' stop-color='#f0956f'/><stop offset='1' stop-color='#c9654a'/></radialGradient>"
    "<radialGradient id='g-spiral' cx='.4' cy='.35' r='.8'><stop offset='0' stop-color='#fff3da'/>"
    "<stop offset='.6' stop-color='#e2c08a'/><stop offset='1' stop-color='#b78a4e'/></radialGradient>"
    "<linearGradient id='g-cone' x1='0' x2='1'><stop offset='0' stop-color='#f8e6c8'/>"
    "<stop offset='.55' stop-color='#d9a06a'/><stop offset='1' stop-color='#a8683a'/></linearGradient>"
    "<radialGradient id='g-cow' cx='.45' cy='.3' r='.85'><stop offset='0' stop-color='#fff6e6'/>"
    "<stop offset='.6' stop-color='#e8b98a'/><stop offset='1' stop-color='#a8683a'/></radialGradient>"
    f"{_scallop()}{_spiral()}{_cone()}{_cowrie()}"
    "</defs></svg>"
)

_ASPECT = {"scallop": 1.0, "spiral": 1.0, "cone": 2.0, "cowrie": 0.7}
_SHELLS = [
    ("scallop", 5, 8, 78, -18), ("spiral", 89, 14, 60, 25), ("cone", 13, 22, 40, 68),
    ("cowrie", 80, 4, 56, -10), ("scallop", 92, 24, 46, 30), ("cowrie", 3, 27, 38, 15),
    ("spiral", 71, 24, 36, -30), ("cone", 95, 6, 30, -52), ("scallop", 28, 3, 48, 8),
    ("cowrie", 58, 5, 40, 20), ("spiral", 40, 22, 34, 40),
]


def _shell_html():
    out = []
    for i, (t, l, b, w, r) in enumerate(_SHELLS):
        h = w * _ASPECT[t]
        out.append(
            f"<svg class='shell' style='left:{l}%;bottom:{b}%;width:{w}px;height:{h:.0f}px;"
            f"--r:{r}deg;animation-delay:-{i * 1.3:.1f}s'>"
            f"<use href='#sh-{t}' width='100%' height='100%'/></svg>")
    return "".join(out)


BG_HTML = f"""
{DEFS}
<div class='sea' aria-hidden='true'></div>
<div class='shells' aria-hidden='true'>{_shell_html()}</div>
"""

EXTRA_CSS = """
/* احتياطي لو WebGL مو شغال */
.sea { position:fixed; inset:0; z-index:0; display:none;
  background: linear-gradient(180deg,#1b8f98 0%,#5fd0c4 38%,#ffffff 44%,#cfa96a 48%,#e6c98f 100%); }
body.no-gl .sea { display:block; }
#glsea { position:fixed; inset:0; width:100%; height:100%; z-index:0; pointer-events:none; display:block; }
.shells { position:fixed; inset:0; z-index:1; pointer-events:none; }
.shell { position:absolute; overflow:visible; transform: rotate(var(--r));
  filter: drop-shadow(3px 6px 5px rgba(80,50,10,.5));
  animation: rock 7s ease-in-out infinite; }
@keyframes rock { 50% { transform: rotate(calc(var(--r) + 4deg)) translateY(-1px); } }
#snd { position:fixed; top:12px; inset-inline-start:12px; z-index:60; border:1px solid rgba(255,255,255,.5);
  background: rgba(6,45,58,.6); color:#fff; padding:8px 14px; border-radius:999px; cursor:pointer;
  backdrop-filter: blur(8px); font: 600 .95rem 'Cairo','Segoe UI',Tahoma,sans-serif; }
#snd:hover { background: rgba(6,45,58,.8); }
@media (prefers-reduced-motion: reduce) { .shell { animation:none !important; } }
"""

HEAD = r"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap" rel="stylesheet">
<script>
(function () {
  document.documentElement.lang = 'ar';
  document.documentElement.dir = 'rtl';

  var FRAG = `
#ifdef GL_FRAGMENT_PRECISION_HIGH
precision highp float;
#else
precision mediump float;
#endif
uniform vec2 uRes; uniform float uT;
const float PER = 12.;     // ثواني لوصول الموجة للشاطئ
const float S0  = .40;     // مكان خط الشاطئ الأساسي
const float RU  = .075;    // أقصى صعود للموجة على الرمل

float hash(vec2 p){ p = fract(p*vec2(123.34,456.21)); p += dot(p,p+45.32); return fract(p.x*p.y); }
float noise(vec2 p){
  vec2 i = floor(p), f = fract(p); f = f*f*(3.-2.*f);
  return mix(mix(hash(i),hash(i+vec2(1.,0.)),f.x), mix(hash(i+vec2(0.,1.)),hash(i+vec2(1.,1.)),f.x), f.y);
}
float fbm(vec2 p){
  float a=.5, s=0.;
  for(int i=0;i<4;i++){ s += a*noise(p); p = p*2.03+vec2(17.1,9.2); a *= .5; }
  return s;
}
mat2 rot(float a){ float c=cos(a), s=sin(a); return mat2(c,-s,s,c); }

// صعود الموجة على الرمل ثم رجوعها (متصل عند اللفة)
float runup(float ph){
  float a = smoothstep(.915, 1., ph);
  float b = 1. - smoothstep(0., .17, ph);
  return ph > .5 ? a : b;
}

vec3 sandCol(vec2 p){
  float g  = hash(floor(gl_FragCoord.xy))*.05;
  float m  = fbm(p*14.) - .5;
  float m2 = fbm(p*3.+7.) - .5;
  float rip = sin(p.y*55. + m2*9.)*.014;
  return vec3(.91,.78,.55)*(1. + m*.20 + m2*.16 + rip) - g;
}

void main(){
  vec2 uv = gl_FragCoord.xy/uRes;
  float asp = uRes.x/uRes.y;
  vec2 c0 = vec2(asp*.5, .5);
  vec2 p = rot(.07)*(vec2(uv.x*asp, uv.y) - c0) + c0;   // الشاطئ مايل شوي

  float setA = .78 + .22*sin(uT*.11 + 1.);              // مجموعات موجات أكبر/أصغر
  float s0 = S0 + .030*sin(p.x*1.9 + uT*.05) + .014*sin(p.x*5.1 - uT*.09);
  float ds = p.y - s0;                                  // المسافة من الشاطئ الثابت

  float lace = fbm(vec2(p.x*13., ds*34.) + vec2(uT*.04, 0.));
  float R = 0., hgt = 0., slope = 0., ffoam = 0.;
  for(int k=0;k<3;k++){
    float ph = fract(uT/PER + float(k)/3.);
    float df = .95*pow(1.-ph, 1.7);                     // موقع قمة الموجة
    R = max(R, runup(ph));
    float amp = (.35 + .65*(1. - smoothstep(.18,.9,df)))*setA;
    float rel = ds - df;
    float w = .014 + .02*df;
    float u = rel/w;
    float c = exp(-u*u);
    hgt   += c*amp;
    slope += -2.*u*c*amp;
    float br = (1. - smoothstep(.14,.50,df))*(1. - smoothstep(.90,1.,ph));   // قوة الانكسار
    float tl = .015 + .18*br;
    float trail = rel > 0. ? exp(-rel/tl) : exp(rel/.008);
    ffoam = max(ffoam, trail*br*smoothstep(.30,.68, lace + trail*.5 - .15));
  }

  float s = s0 + RU*setA*R + (noise(vec2(p.x*7., uT*.15)) - .5)*.03*R;   // خط الماء الفعلي
  float d = p.y - s;                                                     // >0 ماء ، <0 رمل

  // ---------- الرمل ----------
  vec3 sand = sandCol(p);
  float wetUp = s0 + RU*setA*.9;
  float wet = smoothstep(wetUp-.20, wetUp-.01, p.y);
  sand *= mix(1., .58, wet*.9);
  sand += vec3(.45,.55,.60)*.07*wet*noise(p*vec2(40.) + uT*.15);
  vec3 col = sand;

  // ---------- الماء ----------
  float wm = smoothstep(-.003, .004, d);
  if (wm > 0.) {
    float dep = max(ds, 0.);
    vec2 pp = vec2(p.x*9., ds*22.) + vec2(uT*.05, -uT*.22);
    float h0 = fbm(pp);
    float hx = fbm(pp + vec2(.06,0.));
    float hy = fbm(pp + vec2(0.,.06));
    vec2 g = vec2(hx-h0, hy-h0)/.06;

    vec3 bed = sandCol(p + g*.008)*vec3(.80,.90,.86)*.88;
    vec3 shallow = vec3(.58,.84,.72), mid = vec3(.05,.58,.60), deep = vec3(.015,.25,.41);
    vec3 wc = mix(shallow, mid, smoothstep(.02,.22,dep));
    wc = mix(wc, deep, smoothstep(.22,.70,dep));
    float vis = max((1. - smoothstep(0.,.20,dep))*.85, 1. - smoothstep(0.,.07,d));
    vec3 wcol = mix(wc, bed, vis*.88);

    // كوستيكس (خطوط ضوء) بالمية الضحلة
    float c1 = noise(pp*.55 + vec2(uT*.30, uT*.20));
    float c2 = noise(pp*.70 - vec2(uT*.25, -uT*.20) + 5.);
    float ca = 1. - abs(c1 + c2 - 1.);
    ca *= ca; ca *= ca; ca *= ca;
    wcol += vec3(1.,.97,.85)*ca*vis*.55;

    // إضاءة الموجات (قمة فاتحة + ميل)
    wcol += vec3(.40,.80,.76)*hgt*.14*(.35 + .65*(1. - vis));
    wcol += vec3(.9,1.,1.)*slope*.06;

    // لمعان الشمس
    vec3 n = normalize(vec3(-g*.35, 1.));
    float spec = pow(max(dot(n, normalize(vec3(.35,.45,1.))), 0.), 90.);
    wcol += vec3(1.,.96,.85)*spec*.8*(1. - vis*.5);

    col = mix(sand, wcol, wm);
  }

  // ---------- الرغوة ----------
  float lace2 = fbm(vec2(p.x*20., d*50.) + vec2(0., -uT*.2));
  float wz = .025 + .10*R;
  float sh = exp(-max(d,0.)/wz);
  float wash = R*sh*smoothstep(.30,.65, lace2 + .35*sh);                    // رغوة الرجوع
  float e = (d - .003)/.009;
  float edge = exp(-e*e)*(.55 + .45*noise(vec2(p.x*45., uT*.3)))*(.45 + .55*R);   // خط الحافة
  float res = (1. - wm)*smoothstep(.56,.78, noise(p*60. + uT*.1))
              *(1. - smoothstep(0.,.05,-d))*R*.8;                           // فقاعات على الرمل
  float F = (ffoam + wash)*wm + edge + res;
  col = mix(col, vec3(.98,1.,.98)*(.92 + .08*lace), clamp(F, 0., .95));

  col *= 1. - .20*length((uv - .5)*vec2(.8,.6));
  col = pow(max(col, 0.), vec3(.96));
  gl_FragColor = vec4(col, 1.);
}`;
  var VERT = 'attribute vec2 a;void main(){gl_Position=vec4(a,0.,1.);}';
  var still = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var t0 = performance.now();
  function T(){ return still ? 3. : (performance.now() - t0) / 1000.; }

  /* ================= الصوت ================= */
  var ctx = null, A = null, enabled = false, btn = null, auto = true;

  function pinkBuffer(c, secs){            // ستيريو، لوب بدون طقة
    var sr = c.sampleRate, L = Math.floor(sr*secs), N = Math.floor(sr*.25);
    var buf = c.createBuffer(2, L, sr);
    for (var ch = 0; ch < 2; ch++){
      var g = new Float32Array(L + N), b0=0,b1=0,b2=0,b3=0,b4=0,b5=0,b6=0, i;
      for (i = 0; i < L + N; i++){
        var w = Math.random()*2 - 1;
        b0 = .99886*b0 + w*.0555179; b1 = .99332*b1 + w*.0750759; b2 = .96900*b2 + w*.1538520;
        b3 = .86650*b3 + w*.3104856; b4 = .55000*b4 + w*.5329522; b5 = -.7616*b5 - w*.0168980;
        g[i] = (b0+b1+b2+b3+b4+b5+b6 + w*.5362)*.11; b6 = w*.115926;
      }
      var d = buf.getChannelData(ch);
      for (i = 0; i < L; i++) d[i] = g[i];
      for (i = 0; i < N; i++){ var k = i/N; d[i] = g[i]*k + g[L+i]*(1-k); }
    }
    return buf;
  }
  function crackleBuffer(c, secs){         // فقاعات الرغوة: نقرات صغيرة عشوائية
    var sr = c.sampleRate, L = Math.floor(sr*secs), buf = c.createBuffer(2, L, sr);
    for (var ch = 0; ch < 2; ch++){
      var d = buf.getChannelData(ch);
      for (var i = 0; i < L; i++){
        if (Math.random() < .0035){
          var len = 10 + Math.floor(Math.random()*50), a = (Math.random()*.8 + .2)*(Math.random()<.5?-1:1);
          for (var j = 0; j < len && i + j < L; j++) d[i+j] += a*Math.exp(-j/(len*.28))*(Math.random()*2-1);
        }
      }
    }
    return buf;
  }
  function loopSrc(c, buf){
    var s = c.createBufferSource(); s.buffer = buf; s.loop = true;
    s.start(0, Math.random()*(buf.duration - .5)); return s;
  }
  function initAudio(){
    var AC = window.AudioContext || window.webkitAudioContext; if (!AC) return false;
    ctx = new AC();
    var comp = ctx.createDynamicsCompressor();
    comp.threshold.value = -18; comp.ratio.value = 3;
    var master = ctx.createGain(); master.gain.value = 0;
    master.connect(comp); comp.connect(ctx.destination);

    var pink = pinkBuffer(ctx, 9), crk = crackleBuffer(ctx, 5);

    var rum = loopSrc(ctx, pink), lpR = ctx.createBiquadFilter(), gRum = ctx.createGain();
    lpR.type = 'lowpass'; lpR.frequency.value = 200; gRum.gain.value = .2;
    rum.connect(lpR); lpR.connect(gRum); gRum.connect(master);

    var body = loopSrc(ctx, pink), lpB = ctx.createBiquadFilter(), gBody = ctx.createGain();
    lpB.type = 'lowpass'; lpB.frequency.value = 600; lpB.Q.value = .5; gBody.gain.value = 0;
    body.connect(lpB); lpB.connect(gBody); gBody.connect(master);

    var cr = loopSrc(ctx, pink), bpC = ctx.createBiquadFilter(), gCr = ctx.createGain();
    bpC.type = 'bandpass'; bpC.frequency.value = 1600; bpC.Q.value = .45; gCr.gain.value = 0;
    cr.connect(bpC); bpC.connect(gCr); gCr.connect(master);

    var fz = loopSrc(ctx, crk), hpF = ctx.createBiquadFilter(), gFz = ctx.createGain();
    hpF.type = 'highpass'; hpF.frequency.value = 4200; gFz.gain.value = 0;
    fz.connect(hpF); hpF.connect(gFz); gFz.connect(master);

    A = {master:master, lpB:lpB, gRum:gRum, gBody:gBody, gCr:gCr, gFz:gFz};
    return true;
  }
  function sm(a, b, x){ x = Math.min(1, Math.max(0, (x-a)/(b-a))); return x*x*(3-2*x); }
  function tick(){
    if (!A || !enabled) return;
    var t = T(), u = (t/4) % 1, now = ctx.currentTime;
    var setA = .78 + .22*Math.sin(t*.11 + 1);
    var swell = Math.pow(sm(.35, 1, u), 2.2);              // موجة بتقرّب
    var wash  = Math.pow(1 - sm(0, .5, u), 1.3);           // الرجوع بعد الانكسار
    var env = (u < .5 ? wash : swell)*setA;
    var cu = (u < .5 ? u : u - 1) + .08;                   // الانكسار قبل الوصول بشوي
    var crash = Math.exp(-Math.pow(cu/.08, 2))*setA;
    A.gRum.gain.setTargetAtTime(.10 + .35*env, now, .12);
    A.gBody.gain.setTargetAtTime(.04 + .70*env, now, .10);
    A.lpB.frequency.setTargetAtTime(450 + 2600*env, now, .10);
    A.gCr.gain.setTargetAtTime(.60*crash, now, .05);
    A.gFz.gain.setTargetAtTime(.02 + .55*wash*setA, now, .12);
  }
  function lbl(){
    if (!btn) return;
    var ar = document.documentElement.lang === 'ar';
    btn.textContent = enabled ? (ar ? '🔊 صوت البحر' : '🔊 Sea sound') : (ar ? '🔇 صوت البحر' : '🔇 Sea sound');
  }
  function setOn(v){
    if (!ctx && !initAudio()) return;
    enabled = v;
    if (ctx.state === 'suspended') ctx.resume();
    A.master.gain.setTargetAtTime(v ? .85 : 0, ctx.currentTime, .4);
    lbl();
  }
  function setupAudio(){
    btn = document.createElement('button');
    btn.id = 'snd'; document.body.appendChild(btn); lbl();
    btn.onclick = function(){ auto = false; setOn(!enabled); };
    setInterval(tick, 60);
    new MutationObserver(lbl).observe(document.documentElement, {attributes:true, attributeFilter:['lang']});
    document.addEventListener('visibilitychange', function(){
      if (!ctx || !enabled) return;
      if (document.hidden) ctx.suspend(); else ctx.resume();
    });
    function first(e){
      document.removeEventListener('pointerdown', first); document.removeEventListener('keydown', first);
      var onBtn = e.target && e.target.closest && e.target.closest('#snd');
      if (auto && !enabled && !onBtn) setOn(true);
    }
    document.addEventListener('pointerdown', first);
    document.addEventListener('keydown', first);
  }

  /* ================= WebGL ================= */
  function start() {
    setupAudio();
    var c = document.createElement('canvas');
    c.id = 'glsea';
    document.body.appendChild(c);
    var gl = c.getContext('webgl', {antialias:false, alpha:false, powerPreference:'low-power'});
    function fail(){ document.body.classList.add('no-gl'); if (c.parentNode) c.parentNode.removeChild(c); }
    if (!gl) return fail();
    function sh(type, src){
      var s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) { console.error(gl.getShaderInfoLog(s)); return null; }
      return s;
    }
    var vs = sh(gl.VERTEX_SHADER, VERT), fs = sh(gl.FRAGMENT_SHADER, FRAG);
    if (!vs || !fs) return fail();
    var pr = gl.createProgram();
    gl.attachShader(pr, vs); gl.attachShader(pr, fs); gl.linkProgram(pr);
    if (!gl.getProgramParameter(pr, gl.LINK_STATUS)) return fail();
    gl.useProgram(pr);
    var buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 1,-1, -1,1, 1,1]), gl.STATIC_DRAW);
    var loc = gl.getAttribLocation(pr, 'a');
    gl.enableVertexAttribArray(loc);
    gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
    var uRes = gl.getUniformLocation(pr, 'uRes'), uT = gl.getUniformLocation(pr, 'uT');
    function resize(){
      var mobile = window.innerWidth < 700;
      var sc = Math.min(window.devicePixelRatio || 1, 1.5) * (mobile ? .55 : .8);
      c.width = Math.max(2, Math.floor(window.innerWidth * sc));
      c.height = Math.max(2, Math.floor(window.innerHeight * sc));
      gl.viewport(0, 0, c.width, c.height);
    }
    resize();
    window.addEventListener('resize', resize);
    function frame(){
      gl.uniform2f(uRes, c.width, c.height);
      gl.uniform1f(uT, T());
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      if (!still) requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
</script>
"""