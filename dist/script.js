'use strict';
const root = document.documentElement;
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
const toggle = document.querySelector('.menu-toggle');
const navigation = document.getElementById('navigation');
const motionButtons = document.querySelectorAll('.motion-toggle');
let manuallyPaused = false;

function setMenu(open) {
  navigation.classList.toggle('is-open', open);
  toggle.setAttribute('aria-expanded', String(open));
  toggle.setAttribute('aria-label', open ? 'Cerrar menú' : 'Abrir menú');
}
toggle.addEventListener('click', () => setMenu(toggle.getAttribute('aria-expanded') !== 'true'));
navigation.querySelectorAll('a').forEach(link => link.addEventListener('click', () => setMenu(false)));
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {
    setMenu(false);
    toggle.focus();
  }
});
document.addEventListener('click', event => {
  if (!event.target.closest('.site-header')) setMenu(false);
});
window.matchMedia('(min-width: 701px)').addEventListener('change', event => {
  if (event.matches) setMenu(false);
});

function syncMotion() {
  const paused = manuallyPaused || reducedMotion.matches;
  root.classList.toggle('motion-paused', paused);
  root.classList.toggle('motion-enabled', !paused);
  const label = paused ? 'Reanudar animaciones' : 'Pausar animaciones';
  motionButtons.forEach(button => {
    button.setAttribute('aria-pressed', String(paused));
    button.setAttribute('aria-label', label);
    button.title = reducedMotion.matches ? 'Movimiento reducido por la preferencia de tu dispositivo' : label;
    button.querySelector('span').textContent = paused ? '▷' : 'Ⅱ';
    if (button.querySelector('.motion-label')) button.querySelector('.motion-label').textContent = reducedMotion.matches ? 'Movimiento reducido' : label;
    button.disabled = reducedMotion.matches;
  });
}
motionButtons.forEach(button => button.addEventListener('click', () => {
  manuallyPaused = !manuallyPaused;
  syncMotion();
}));
reducedMotion.addEventListener('change', syncMotion);
if ('IntersectionObserver' in window) {
  const observer = new IntersectionObserver(entries => {
    for (const entry of entries) {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        observer.unobserve(entry.target);
      }
    }
  }, { threshold: 0.08 });
  document.querySelectorAll('.reveal').forEach(element => observer.observe(element));
  syncMotion();
}
document.querySelectorAll('[data-message]').forEach(link => {
  link.href = 'https://wa.me/523342781554?text=' + encodeURIComponent(link.dataset.message);
});
document.getElementById('year').textContent = String(new Date().getFullYear());
