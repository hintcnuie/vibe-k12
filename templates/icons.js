/* ============================================================
   简笔画图标库（SVG 线稿）
   原则：单色线稿 + currentColor，由外部 CSS 上色；
   尺寸统一在 100×100 视口里画，用的时候按容器缩放。
   用法：window.ICONS.rabbit 取到一段 <svg> 字符串
   ============================================================ */
(function () {
  const wrap = inner => `<svg viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round">${inner}</svg>`;

  const ICONS = {
    /* 小兔：长耳朵 + 圆头 + 圆身子 + 短尾 */
    rabbit: wrap(`
      <ellipse cx="54" cy="66" rx="26" ry="18"/>
      <circle cx="54" cy="38" r="15"/>
      <ellipse cx="47" cy="17" rx="5.2" ry="12" transform="rotate(-14 47 17)"/>
      <ellipse cx="62" cy="16" rx="5.2" ry="12" transform="rotate(10 62 16)"/>
      <circle cx="26" cy="60" r="6.5"/>
      <circle cx="50" cy="38" r="1.6" fill="currentColor" stroke="none"/>
      <path d="M38 82 v7 M54 84 v5 M68 80 v7"/>`),

    /* 松鼠：大尾巴 + 竖耳 + 尖脸 */
    squirrel: wrap(`
      <path d="M70 62 q26 -6 24 -30 q-2 -18 -18 -16 q-12 2 -10 14"/>
      <ellipse cx="51" cy="62" rx="20" ry="17"/>
      <circle cx="53" cy="36" r="13"/>
      <path d="M48 24 l-3 -9 l9 4 Z"/>
      <circle cx="58" cy="35" r="1.6" fill="currentColor" stroke="none"/>
      <path d="M33 66 q-6 4 -2 10 M52 79 v8"/>`),

    /* 猴子：圆脸 + 两只大耳朵 + 卷尾巴 */
    monkey: wrap(`
      <circle cx="52" cy="38" r="15"/>
      <circle cx="33" cy="40" r="6.5"/>
      <circle cx="71" cy="40" r="6.5"/>
      <ellipse cx="52" cy="68" rx="17" ry="15"/>
      <path d="M69 74 q14 2 12 16 q-2 8 -8 6"/>
      <circle cx="56" cy="38" r="1.6" fill="currentColor" stroke="none"/>
      <path d="M40 86 v7 M60 86 v7"/>`),

    /* 人步行：圆头 + 迈步 + 摆臂 */
    walker: wrap(`
      <circle cx="48" cy="20" r="10"/>
      <path d="M48 30 v22"/>
      <path d="M48 38 l-14 10 M48 38 l13 8"/>
      <path d="M48 52 l-11 24 M48 52 l12 18 l8 6"/>`),

    /* 飞机：机身 + 后掠翼 */
    plane: wrap(`
      <path d="M18 56 q22 -6 52 -4 l16 -14 l6 2 -8 16 q14 2 18 6 q-16 6 -34 6 q-18 0 -32 -4 Z"/>
      <path d="M40 52 l-8 18 M30 62 h10"/>`),

    /* 声音：喇叭 + 声波 */
    sound: wrap(`
      <path d="M20 40 v18 h12 l16 12 V28 l-16 12 Z"/>
      <path d="M60 34 q10 12 0 24" stroke-dasharray="none"/>
      <path d="M72 28 q16 18 0 36"/>
      <path d="M84 20 q24 26 0 52"/>`),

    /* 光：闪电 */
    light: wrap(`
      <path d="M56 12 l-26 42 h18 l-8 34 30 -46 h-19 Z"/>`),

    /* 面包车 */
    van: wrap(`
      <path d="M16 66 V44 h34 l14 12 h14 v10"/>
      <path d="M16 66 h64"/>
      <circle cx="34" cy="70" r="7"/>
      <circle cx="66" cy="70" r="7"/>
      <path d="M30 44 v-8 h16 v8"/>`),

    /* 小汽车 */
    car: wrap(`
      <path d="M14 66 V54 l10 -2 l10 -12 h26 l12 12 l12 2 v12"/>
      <path d="M14 66 h64"/>
      <circle cx="32" cy="70" r="7"/>
      <circle cx="64" cy="70" r="7"/>`),

    /* 秒表（计时用） */
    clock: wrap(`
      <circle cx="50" cy="56" r="26"/>
      <path d="M50 40 v16 l11 7 M50 24 v-8 M42 16 h16"/>`),
  };

  window.ICONS = ICONS;
})();
