// ============================================================
// ScaleUp — interactions
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
  const yearEl = document.getElementById('year');
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  // Header scroll state
  const header = document.getElementById('site-header');
  const onScroll = () => {
    if (header) header.classList.toggle('is-scrolled', window.scrollY > 12);
  };
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });

  // Mobile nav toggle
  const navToggle = document.getElementById('navToggle');
  const mobileNav = document.getElementById('mobileNav');
  if (navToggle && mobileNav) {
    navToggle.addEventListener('click', () => {
      const open = navToggle.classList.toggle('is-open');
      mobileNav.classList.toggle('is-open', open);
      navToggle.setAttribute('aria-expanded', String(open));
    });
    mobileNav.querySelectorAll('a').forEach(a => a.addEventListener('click', () => {
      navToggle.classList.remove('is-open');
      mobileNav.classList.remove('is-open');
    }));
  }

  // Scroll reveal
  const revealEls = document.querySelectorAll('.reveal, .tl-item');
  const io = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        io.unobserve(entry.target);
      }
    });
  }, { threshold: 0.15 });
  revealEls.forEach(el => io.observe(el));

  // Animated counters
  const counters = document.querySelectorAll('[data-counter]');
  const counterIO = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      const el = entry.target;
      const target = parseFloat(el.dataset.counter);
      const suffix = el.dataset.suffix || '';
      const decimals = el.dataset.counter.includes('.') ? 1 : 0;
      const duration = 1400;
      const start = performance.now();
      const tick = (now) => {
        const progress = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const value = target * eased;
        const formatted = decimals > 0
          ? value.toFixed(decimals)
          : Math.round(value).toLocaleString('fr-FR');
        el.textContent = formatted + suffix;
        if (progress < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
      counterIO.unobserve(el);
    });
  }, { threshold: 0.6 });
  counters.forEach(el => counterIO.observe(el));

  // App screenshot slider (carousel) — supports several sliders per page
  document.querySelectorAll('.app-slider, .promo-slider').forEach(slider => {
    const slides = Array.from(slider.querySelectorAll('.slide'));
    const dots = Array.from(slider.querySelectorAll('.slider-dots .dot'));
    const prevBtn = slider.querySelector('.slider-arrow.prev');
    const nextBtn = slider.querySelector('.slider-arrow.next');
    if (!slides.length) return;
    let index = 0;
    let timer = null;

    function show(i) {
      index = (i + slides.length) % slides.length;
      slides.forEach((s, n) => s.classList.toggle('is-active', n === index));
      dots.forEach((d, n) => d.classList.toggle('is-active', n === index));
    }
    function next() { show(index + 1); }
    function prev() { show(index - 1); }
    function startAutoplay() {
      if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
      timer = setInterval(next, 4500);
    }
    function stopAutoplay() { if (timer) clearInterval(timer); }

    if (prevBtn) prevBtn.addEventListener('click', () => { prev(); stopAutoplay(); startAutoplay(); });
    if (nextBtn) nextBtn.addEventListener('click', () => { next(); stopAutoplay(); startAutoplay(); });
    dots.forEach((d, n) => d.addEventListener('click', () => { show(n); stopAutoplay(); startAutoplay(); }));
    slider.addEventListener('mouseenter', stopAutoplay);
    slider.addEventListener('mouseleave', startAutoplay);

    show(0);
    startAutoplay();
  });

  // Démo interactive Khotwa : navigation entre les panneaux
  const demoNavItems = document.querySelectorAll('.demo-nav-item');
  if (demoNavItems.length) {
    demoNavItems.forEach(btn => {
      btn.addEventListener('click', () => {
        const target = btn.dataset.target;
        demoNavItems.forEach(b => b.classList.toggle('is-active', b === btn));
        document.querySelectorAll('.demo-panel').forEach(panel => {
          panel.classList.toggle('is-active', panel.id === `panel-${target}`);
        });
      });
    });
  }

  // FAQ accordion
  document.querySelectorAll('.faq-item').forEach(item => {
    const q = item.querySelector('.faq-q');
    const a = item.querySelector('.faq-a');
    if (!q || !a) return;
    q.addEventListener('click', () => {
      const isOpen = item.classList.contains('is-open');
      document.querySelectorAll('.faq-item.is-open').forEach(other => {
        if (other !== item) {
          other.classList.remove('is-open');
          other.querySelector('.faq-a').style.maxHeight = null;
        }
      });
      item.classList.toggle('is-open', !isOpen);
      a.style.maxHeight = !isOpen ? a.scrollHeight + 'px' : null;
    });
  });

  // Demo / contact form — envoie réellement la demande au serveur
  const demoForm = document.getElementById('demoForm');
  if (demoForm) {
    const statusEl = document.getElementById('demoFormStatus');
    demoForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = demoForm.querySelector('button[type="submit"]');
      const original = btn.textContent;
      btn.disabled = true;
      btn.textContent = 'Envoi en cours…';
      if (statusEl) { statusEl.textContent = ''; statusEl.style.color = ''; }

      const data = {
        name: document.getElementById('name').value,
        org: document.getElementById('org').value,
        email: document.getElementById('email').value,
        service: document.getElementById('service').value,
        message: document.getElementById('msg').value,
      };

      try {
        const res = await fetch('/api/demande', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data),
        });
        const result = await res.json();

        if (res.ok && result.success) {
          btn.textContent = 'Demande envoyée ✓';
          if (statusEl) {
            statusEl.style.color = '#34D399';
            statusEl.textContent = 'Merci ! Votre demande a bien été enregistrée, nous revenons vers vous sous 24h.';
          }
          demoForm.reset();
        } else {
          btn.textContent = original;
          if (statusEl) {
            statusEl.style.color = '#F87171';
            statusEl.textContent = result.error || "Une erreur est survenue, réessayez dans un instant.";
          }
        }
      } catch (err) {
        btn.textContent = original;
        if (statusEl) {
          statusEl.style.color = '#F87171';
          statusEl.textContent = 'Connexion impossible. Vérifiez votre réseau puis réessayez.';
        }
      } finally {
        setTimeout(() => { btn.disabled = false; if (btn.textContent !== original) btn.textContent = original; }, 3200);
      }
    });
  }

  // Illustration École : les yeux et les mains des 3 personnages suivent la souris sur la page
  const illoSvg = document.querySelector('.illustration-svg');
  if (illoSvg && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    const eyePupils = illoSvg.querySelectorAll('.eye-pupil');
    const handsGroups = illoSvg.querySelectorAll('.hands-follow');
    const EYE_MAX = 2.6;   // déplacement max de la pupille (unités SVG)
    const ARM_MAX_DEG = 9; // rotation max des bras vers la souris (degrés)
    let rafId = null;

    const trackPointer = (clientX, clientY) => {
      if (rafId) return;
      rafId = requestAnimationFrame(() => {
        rafId = null;
        const ctm = illoSvg.getScreenCTM();
        if (!ctm) return;
        const pt = illoSvg.createSVGPoint();
        pt.x = clientX; pt.y = clientY;
        const p = pt.matrixTransform(ctm.inverse());

        eyePupils.forEach(g => {
          const cx = parseFloat(g.dataset.cx), cy = parseFloat(g.dataset.cy);
          const dx = p.x - cx, dy = p.y - cy;
          const dist = Math.hypot(dx, dy) || 1;
          const r = Math.min(EYE_MAX, dist / 14);
          g.setAttribute('transform', `translate(${((dx / dist) * r).toFixed(2)} ${((dy / dist) * r).toFixed(2)})`);
        });

        handsGroups.forEach(g => {
          const px = parseFloat(g.dataset.pivotX), py = parseFloat(g.dataset.pivotY);
          const lean = Math.max(-1, Math.min(1, (p.x - px) / 260));
          g.setAttribute('transform', `rotate(${(lean * ARM_MAX_DEG).toFixed(2)} ${px} ${py})`);
        });
      });
    };

    document.addEventListener('mousemove', (e) => trackPointer(e.clientX, e.clientY), { passive: true });
  }

  // Transition 3D "page qui se tourne" au clic sur une carte de domaine
  const domainCards = document.querySelectorAll('.domain-card');
  if (domainCards.length && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    domainCards.forEach(card => {
      card.addEventListener('click', (e) => {
        // laisse le comportement natif pour ouverture dans un nouvel onglet / clic molette
        if (e.metaKey || e.ctrlKey || e.shiftKey || e.button === 1) return;
        e.preventDefault();
        const href = card.getAttribute('href');
        card.classList.add('is-flipping');
        document.body.classList.add('page-leaving');
        setTimeout(() => { window.location.href = href; }, 560);
      });
    });
  }

  // Pro micro-interactions: 3D tilt on mockups/screenshots, magnetic buttons
  const supportsFinePointer = window.matchMedia('(pointer: fine)').matches;
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  if (supportsFinePointer && !reduceMotion) {
    document.querySelectorAll('.tilt').forEach(el => {
      let raf = null;
      el.addEventListener('mousemove', (e) => {
        const rect = el.getBoundingClientRect();
        const px = (e.clientX - rect.left) / rect.width - 0.5;
        const py = (e.clientY - rect.top) / rect.height - 0.5;
        if (raf) cancelAnimationFrame(raf);
        raf = requestAnimationFrame(() => {
          el.style.transform = `perspective(1400px) rotateY(${px * 10}deg) rotateX(${-py * 10}deg) translateY(-4px)`;
        });
      });
      el.addEventListener('mouseleave', () => {
        el.style.transform = '';
      });
    });

    document.querySelectorAll('.btn-magnetic').forEach(btn => {
      btn.addEventListener('mousemove', (e) => {
        const rect = btn.getBoundingClientRect();
        const mx = (e.clientX - rect.left) / rect.width - 0.5;
        const my = (e.clientY - rect.top) / rect.height - 0.5;
        btn.style.transform = `translate(${mx * 10}px, ${my * 10 - 2}px)`;
      });
      btn.addEventListener('mouseleave', () => { btn.style.transform = ''; });
    });
  }

  // Ambient particle canvas
  const canvas = document.getElementById('particles');
  if (canvas && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    const ctx = canvas.getContext('2d');
    let w, h, particles;

    const resize = () => {
      w = canvas.width = window.innerWidth;
      h = canvas.height = Math.min(window.innerHeight * 1.4, 1400);
    };

    const colors = ['#2563EB', '#7C3AED', '#06B6D4', '#FF2FD1'];
    const init = () => {
      const count = Math.min(60, Math.floor((w * h) / 30000));
      particles = Array.from({ length: count }, () => ({
        x: Math.random() * w,
        y: Math.random() * h,
        r: Math.random() * 1.6 + 0.4,
        vx: (Math.random() - 0.5) * 0.15,
        vy: (Math.random() - 0.5) * 0.15,
        c: colors[Math.floor(Math.random() * colors.length)],
        a: Math.random() * 0.5 + 0.15,
      }));
    };

    const draw = () => {
      ctx.clearRect(0, 0, w, h);
      particles.forEach(p => {
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0) p.x = w; if (p.x > w) p.x = 0;
        if (p.y < 0) p.y = h; if (p.y > h) p.y = 0;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = p.c;
        ctx.globalAlpha = p.a;
        ctx.fill();
      });
      ctx.globalAlpha = 1;
      requestAnimationFrame(draw);
    };

    resize(); init(); draw();
    window.addEventListener('resize', () => { resize(); init(); }, { passive: true });
  }
});
