// home-bg.js — Animated background for the home page
(function() {
  const canvas = document.getElementById('bg-canvas');
  if (canvas) {
    const ctx = canvas.getContext('2d');
    let W, H;
    const ASH_COUNT = 80;
    const ashes = [];
    function resize() {
      W = canvas.width = window.innerWidth;
      H = canvas.height = window.innerHeight;
    }
    resize();
    window.addEventListener('resize', resize);
    for (let i = 0; i < ASH_COUNT; i++) {
      ashes.push({
        x: Math.random() * W,
        y: Math.random() * H,
        vx: (Math.random() - 0.5) * 0.15,
        vy: -Math.random() * 0.5 - 0.1,
        r: Math.random() * 1.4 + 0.4,
        opacity: Math.random() * 0.4 + 0.1,
        isGold: Math.random() < 0.3,
        phase: Math.random() * Math.PI * 2
      });
    }
    function drawAsh() {
      ctx.clearRect(0, 0, W, H);
      for (const a of ashes) {
        a.x += a.vx + Math.sin(a.phase + performance.now() / 2000) * 0.3;
        a.y += a.vy;
        if (a.y < -10) { a.y = H + 10; a.x = Math.random() * W; }
        if (a.x < -10) a.x = W + 10;
        if (a.x > W + 10) a.x = -10;
        const color = a.isGold
          ? 'rgba(200, 164, 74, ' + a.opacity + ')'
          : 'rgba(214, 58, 46, ' + a.opacity + ')';
        ctx.beginPath();
        ctx.arc(a.x, a.y, a.r, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
        const grad = ctx.createRadialGradient(a.x, a.y, 0, a.x, a.y, a.r * 2.5);
        grad.addColorStop(0, color);
        grad.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.fillStyle = grad;
        ctx.fill();
      }
      requestAnimationFrame(drawAsh);
    }
    drawAsh();
  }
  document.querySelectorAll('.home-tile').forEach(function(card) {
    card.addEventListener('click', function() {
      var href = card.getAttribute('href');
      if (href && href !== '#') window.location.href = href;
    });
  });
})();
