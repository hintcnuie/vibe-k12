/* ============================================================
   场景模板库
   每个模板 = (props) => { el, update(local, dur) }
   update 必须是纯函数：给定 local 时间，画面状态唯一确定
   —— 这样 Playwright 才能任意跳帧，渲染可断点续跑
   ============================================================ */
(function () {
  const clamp01 = v => v < 0 ? 0 : v > 1 ? 1 : v;
  const eOut = t => 1 - Math.pow(1 - t, 3);
  const eInOut = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  // 轻微回弹，只用于"切片长出来"这类有体积感的动作
  const c1 = 1.70158, c3 = c1 + 1;
  const eBack = t => 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2);
  const p = (l, s, d) => clamp01((l - s) / d);
  const eo = (l, s, d) => eOut(p(l, s, d));
  const ei = (l, s, d) => eInOut(p(l, s, d));

  const mk = (tag, cls, html) => {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html != null) e.innerHTML = html;
    return e;
  };
  const rise = (n, pr, dist = 34) => {
    n.style.opacity = pr.toFixed(3);
    n.style.transform = `translateY(${(1 - pr) * dist}px)`;
  };
  const pop = (n, pr, from = .88) => {
    const s = from + (1 - from) * pr;
    n.style.opacity = pr.toFixed(3);
    n.style.transform = `scale(${s.toFixed(3)})`;
  };
  const wipeDown = (n, pr) => {
    n.style.clipPath = `inset(0 0 ${((1 - pr) * 100).toFixed(2)}% 0)`;
  };

  window.SCENES = {

    /* 01 封面 */
    cover(p_) {
      const el = mk('div', 'cover', `
        <div class="cv-kicker">${p_.kicker || ''}</div>
        <div class="cv-title">${p_.title || ''}</div>
        <div class="cv-rule"></div>
        <div class="cv-sub">${p_.sub || ''}</div>
        <div class="cv-seal seal" style="width:74px;height:118px;">${p_.seal || ''}</div>
        <div class="cv-corner">${p_.corner || ''}</div>`);
      const q = s => el.querySelector(s);
      const kicker = q('.cv-kicker'), title = q('.cv-title'),
            rule = q('.cv-rule'), sub = q('.cv-sub'), seal = q('.cv-seal');
      return {
        el, update(l) {
          kicker.style.opacity = eo(l, 0, .6).toFixed(3);
          const tp = eo(l, .18, 1.0);
          title.style.opacity = tp.toFixed(3);
          title.style.transform = `translateY(${(1 - tp) * 22}px)`;
          rule.style.width = (ei(l, 1.05, .9) * 320).toFixed(1) + 'px';
          sub.style.opacity = eo(l, 1.3, .7).toFixed(3);
          const sp = eo(l, 1.75, .65);
          seal.style.opacity = (sp * .92).toFixed(3);
          seal.style.transform = `scale(${(1.14 - .14 * sp).toFixed(3)}) rotate(${(-7 + 7 * sp).toFixed(2)}deg)`;
        }
      };
    },

    /* 02 四季 */
    seasons(p_) {
      const items = p_.items || [];
      const el = mk('div', 'seasons', `
        <div class="sz-head">${p_.head || '一年四季'}</div>
        <div class="sz-row">${items.map(it => `
          <div class="sz-item"><div class="sz-c">${it.t}</div><div class="sz-s">${it.s}</div></div>`).join('')}
        </div>
        <div class="sz-baseline"></div>`);
      const head = el.querySelector('.sz-head');
      const nodes = [...el.querySelectorAll('.sz-item')];
      const base = el.querySelector('.sz-baseline');
      const act = typeof p_.active === 'number' ? p_.active : -1;
      const actAt = .35 + Math.max(0, act) * .28 + 1.0;
      return {
        el, update(l) {
          head.style.opacity = eo(l, 0, .55).toFixed(3);
          nodes.forEach((n, i) => {
            const pr = eo(l, .35 + i * .28, .7);
            pop(n, pr, .9);
            n.classList.toggle('on', i === act && l >= actAt);
          });
          base.style.opacity = ei(l, .1, 1.1).toFixed(3);
        }
      };
    },

    /* 02b 四季披萨：四块 90° 扇形依次生长（几何由时间直接算出） */
    seasons_pie(p_) {
      const items = (p_.items || []).slice(0, 4);
      const R = 268, CX = 300, CY = 300;
      const midOf = i => (-45 + 90 * i) * Math.PI / 180;
      const labs = items.map((it, i) => {
        const a = midOf(i), lx = CX + .60 * R * Math.cos(a), ly = CY + .60 * R * Math.sin(a);
        return `<g class="pie-lab"><text class="pie-l-c" x="${lx.toFixed(1)}" y="${(ly - 16).toFixed(1)}">${it.t || ''}</text>
                <text class="pie-l-s" x="${lx.toFixed(1)}" y="${(ly + 40).toFixed(1)}">${it.s || ''}</text></g>`;
      }).join('');
      const el = mk('div', 'pie', `
        <div class="pie-head">${p_.head || '一年四季'}</div>
        <div class="pie-dial">
          <svg class="pie-svg" viewBox="0 0 600 600">
            <circle class="pie-ring" cx="300" cy="300" r="292"></circle>
            ${items.map((_, i) => `<path class="pie-slice s${i}" d=""></path>`).join('')}
            <path class="pie-arc" d=""></path>
            <circle class="pie-hub" cx="300" cy="300" r="36"></circle>
            <text class="pie-hub-t" x="300" y="300">年</text>
            ${labs}
          </svg>
        </div>`);
      const head = el.querySelector('.pie-head');
      const ring = el.querySelector('.pie-ring');
      const hub = el.querySelector('.pie-hub');
      const hubT = el.querySelector('.pie-hub-t');
      const slices = [...el.querySelectorAll('.pie-slice')];
      const labels = [...el.querySelectorAll('.pie-lab')];
      const harc = el.querySelector('.pie-arc');

      const arc = (i, r) => {
        const a0 = (-90 + 90 * i) * Math.PI / 180;
        const a1 = (-90 + 90 * (i + 1)) * Math.PI / 180;
        const x0 = (CX + r * Math.cos(a0)).toFixed(2), y0 = (CY + r * Math.sin(a0)).toFixed(2);
        const x1 = (CX + r * Math.cos(a1)).toFixed(2), y1 = (CY + r * Math.sin(a1)).toFixed(2);
        return `M${CX},${CY} L${x0},${y0} A${r},${r} 0 0,1 ${x1},${y1} Z`;
      };

      return {
        el, update(l) {
          head.style.opacity = eo(l, 0, .55).toFixed(3);
          ring.style.opacity = ei(l, 0, .9).toFixed(3);
          slices.forEach((n, i) => {
            const st = .32 + i * .42;
            const r = R * Math.min(1, eBack(p(l, st, .95)));
            n.setAttribute('d', arc(i, Math.max(r, .5)));
            n.style.opacity = eo(l, st, .2) > 0 ? 1 : 0;
            labels[i].style.opacity = eo(l, st + .45, .6).toFixed(3);
          });
          const hp = eo(l, 2.45, .7);          // 冬至那块收尾高亮
          const A0 = 180 * Math.PI / 180, A1 = 270 * Math.PI / 180;
          const hr = R * 1.002;
          const hx0 = (CX + hr * Math.cos(A0)), hy0 = (CY + hr * Math.sin(A0));
          const hx1 = (CX + hr * Math.cos(A1)), hy1 = (CY + hr * Math.sin(A1));
          harc.setAttribute('d', `M${hx0.toFixed(1)},${hy0.toFixed(1)} A${hr},${hr} 0 0,1 ${hx1.toFixed(1)},${hy1.toFixed(1)}`);
          const arcLen = Math.PI / 2 * hr;
          harc.style.strokeDasharray = `${(arcLen * hp).toFixed(1)} 999`;
          harc.style.opacity = hp > 0 ? 1 : 0;
          if (hp > 0) {
            labels[3].style.transform = `scale(${(1 + .08 * hp).toFixed(3)})`;
            labels[3].style.transformOrigin = `${CX}px ${CY}px`;
          }
          hub.style.opacity = ei(l, 2.1, .6).toFixed(3);
          hubT.style.opacity = ei(l, 2.15, .6).toFixed(3);
        }
      };
    },

    /* 03 陈述 */
    statement(p_) {
      const lines = p_.lines || [];
      const el = mk('div', 'stmt', `
        <div class="st-l1">${lines[0] || ''}</div>
        <div class="st-l2">${lines[1] || ''}</div>
        <div class="st-line"></div>
        <div class="st-foot">${p_.foot || ''}</div>`);
      const l1 = el.querySelector('.st-l1'), l2 = el.querySelector('.st-l2'),
            line = el.querySelector('.st-line'), foot = el.querySelector('.st-foot');
      return {
        el, update(l) {
          rise(l1, eo(l, 0, .85), 26);
          rise(l2, eo(l, .55, .95), 34);
          line.style.width = (ei(l, 1.35, .8) * 420).toFixed(1) + 'px';
          foot.style.opacity = eo(l, 1.8, .8).toFixed(3);
        }
      };
    },

    /* 04 单字 */
    bigchar(p_) {
      const el = mk('div', 'bc', `
        <div class="bc-left">
          <div class="bc-char">${p_.char || ''}</div>
          <div class="bc-py">${p_.pinyin || ''}</div>
          <div class="bc-gloss">${p_.gloss || ''}</div>
        </div>
        <div class="bc-right">${(p_.pairs || []).map(x => `
          <div class="bc-pair"><span class="bc-k">${x.k}</span><span class="bc-v">${x.v}</span></div>`).join('')}
        </div>`);
      const ch = el.querySelector('.bc-char'), py = el.querySelector('.bc-py'),
            gl = el.querySelector('.bc-gloss'),
            pairs = [...el.querySelectorAll('.bc-pair')];
      return {
        el, update(l) {
          wipeDown(ch, eo(l, 0, .95));
          py.style.opacity = eo(l, .8, .6).toFixed(3);
          gl.style.opacity = eo(l, 1.05, .75).toFixed(3);
          pairs.forEach((n, i) => rise(n, eo(l, 1.35 + i * .35, .8), 30));
        }
      };
    },

    /* 05 引文 */
    quote(p_) {
      const lines = p_.lines || [];
      const el = mk('div', 'quote-wrap', `
        <div class="q-rule"></div>
        <div class="q-body">${lines.map(t => `<div class="q-line">${t}</div>`).join('')}</div>
        <div class="q-source">——${p_.source || ''}</div>`);
      const rule = el.querySelector('.q-rule');
      const ls = [...el.querySelectorAll('.q-line')];
      const src = el.querySelector('.q-source');
      return {
        el, update(l) {
          rule.style.width = (ei(l, 0, .8) * 210).toFixed(1) + 'px';
          ls.forEach((n, i) => wipeDown(n, eo(l, .3 + i * .7, 1.1)));
          src.style.opacity = eo(l, 1.95, .7).toFixed(3);
        }
      };
    },

    /* 06 对比 */
    compare(p_) {
      const col = c => `
        <div class="cmp-col">
          <div class="cmp-t">${c.title || ''}</div>
          <ul class="cmp-list">${(c.items || []).map(t => `<li><span class="cmp-dot"></span>${t}</li>`).join('')}</ul>
        </div>`;
      const el = mk('div', 'cmp',
        col(p_.left || {}) + `<div class="cmp-div"></div>` + col(p_.right || {}));
      const cols = [...el.querySelectorAll('.cmp-col')];
      const titles = [...el.querySelectorAll('.cmp-t')];
      const div = el.querySelector('.cmp-div');
      const lis = [...el.querySelectorAll('.cmp-list li')];
      const n = (p_.left.items || []).length;
      return {
        el, update(l) {
          titles.forEach((t, i) => t.style.opacity = eo(l, i * .3, .6).toFixed(3));
          div.style.height = (ei(l, .2, .9) * 470).toFixed(1) + 'px';
          lis.forEach((li, i) => {
            const col_ = i < n ? 0 : 1;
            const idx = i < n ? i : i - n;
            rise(li, eo(l, .55 + col_ * .3 + idx * .3, .7), 26);
          });
        }
      };
    },

    /* 07 时间线 */
    timeline(p_) {
      const pts = p_.points || [];
      const act = typeof p_.active === 'number' ? p_.active : -1;
      const el = mk('div', 'tl', `
        <div class="tl-badge">${p_.badge || ''}</div>
        <div class="tl-axis"></div>
        <div class="tl-nodes"><span class="tl-run"></span>${pts.map(t => `
          <div class="tl-node"><span class="tl-dot"></span><span class="tl-name">${t}</span></div>`).join('')}
        </div>
        <div class="tl-fact">${p_.fact || ''}</div>`);
      const badge = el.querySelector('.tl-badge'), axis = el.querySelector('.tl-axis'),
            nodes = [...el.querySelectorAll('.tl-node')], fact = el.querySelector('.tl-fact'),
            run = el.querySelector('.tl-run');
      return {
        el, update(l) {
          badge.style.opacity = eo(l, 0, .55).toFixed(3);
          axis.style.transform = `scaleX(${ei(l, .25, 1.0).toFixed(3)})`;
          nodes.forEach((n, i) => {
            const pr = eo(l, .9 + i * .35, .65);
            n.style.opacity = pr.toFixed(3);
            n.style.transform = `translateY(${(1 - pr) * 22}px)`;
            n.classList.toggle('on', i === act && l >= 2.3);
          });
          /* 红色游标沿轴走一遍，停在当前节点上（时间在流动的视觉锚点） */
          const gi = Math.max(0, act), span = 1120 / Math.max(1, pts.length - 1);
          const prog = eInOut(p(l, 1.0, 1.3));
          run.style.left = `${(60 + span * gi * prog - 6).toFixed(1)}px`;
          run.style.opacity = p(l, 1.0, 1.5) > 0 ? 1 : 0;
          fact.style.opacity = eo(l, 2.5, .8).toFixed(3);
        }
      };
    },

    /* 08 仪式 */
    ritual(p_) {
      const steps = p_.steps || [];
      const el = mk('div', 'rt', `
        <div class="rt-head">
          <div class="rt-kicker">${p_.kicker || ''}</div>
          <div class="rt-title">${p_.title || ''}</div>
        </div>
        <div class="rt-steps">${steps.map(s => `
          <div class="rt-step"><div class="rt-n">${s.n}</div><div class="rt-t">${s.t}</div></div>`).join('')}
        </div>
        <div class="rt-ring"></div>`);
      const head = el.querySelector('.rt-head');
      const st = [...el.querySelectorAll('.rt-step')];
      const ring = el.querySelector('.rt-ring');
      return {
        el, update(l) {
          head.style.opacity = eo(l, 0, .8).toFixed(3);
          head.style.transform = `translateY(${(1 - eo(l, 0, .8)) * 16}px)`;
          st.forEach((n, i) => rise(n, eo(l, 1.0 + i * .45, .75), 28));
          const rp = ei(l, 0, 3.2);
          ring.style.transform = `rotate(${(rp * 40).toFixed(2)}deg)`;
          ring.style.opacity = (0.5 + 0.3 * rp).toFixed(3);
        }
      };
    },

    /* 09 补冬 */
    food(p_) {
      const cards = p_.items || [];
      const el = mk('div', 'fd', `
        <div class="fd-title">${p_.title || ''}</div>
        <div class="fd-cards">${cards.map(c => `
          <div class="fd-card">
            <div class="fd-icon">${c.e}</div>
            <div class="fd-name">${c.n}</div>
            <div class="fd-desc">${c.d}</div>
          </div>`).join('')}
        </div>
        <div class="fd-note">${p_.note || ''}</div>`);
      const title = el.querySelector('.fd-title');
      const cs = [...el.querySelectorAll('.fd-card')];
      const note = el.querySelector('.fd-note');
      return {
        el, update(l) {
          title.style.opacity = eo(l, 0, .6).toFixed(3);
          cs.forEach((n, i) => pop(n, eo(l, .75 + i * .3, .8), .9));
          note.style.opacity = eo(l, 1.95, .8).toFixed(3);
        }
      };
    },

    /* 10 结尾 */
    outro(p_) {
      const lines = p_.lines || [];
      const el = mk('div', 'out', `
        ${lines.map((t, i) => `<div class="out-line${i === lines.length - 1 ? ' big' : ''}">${t}</div>`).join('')}
        <div class="out-seal seal" style="width:82px;height:118px;">${p_.tag || ''}</div>`);
      const ls = [...el.querySelectorAll('.out-line')];
      const seal = el.querySelector('.out-seal');
      return {
        el, update(l) {
          ls.forEach((n, i) => rise(n, eo(l, .15 + i * .6, .85), 30));
          const sp = eo(l, 2.35, .7);
          seal.style.opacity = sp.toFixed(3);
          seal.style.transform = `scale(${(1.3 - .3 * sp).toFixed(3)}) rotate(${(-8 + 8 * sp).toFixed(2)}deg)`;
        }
      };
    }
  };
})();
