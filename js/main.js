// Page Load Transition
document.addEventListener('DOMContentLoaded', () => {
  const transitionEl = document.getElementById('page-transition');
  if (transitionEl && typeof anime !== 'undefined') {
    anime({
      targets: transitionEl,
      opacity: 0,
      duration: 800,
      easing: 'easeInOutQuad',
      complete: () => {
        transitionEl.style.display = 'none';
      }
    });
  }

  // Intercept links for smooth transition out
  const links = document.querySelectorAll('a');
  links.forEach(link => {
    link.addEventListener('click', (e) => {
      const target = link.getAttribute('href');

      // Ignore anchors or external links for now
      if(target.startsWith('#') || target.startsWith('http')) return;

      e.preventDefault();

      if (transitionEl) {
        transitionEl.style.display = 'flex';
        anime({
          targets: transitionEl,
          opacity: 1,
          duration: 400,
          easing: 'easeInOutQuad',
          complete: () => {
            window.location.href = target;
          }
        });
      } else {
        window.location.href = target;
      }
    });
  });

  // Scroll triggers for revealing elements
  const observerOptions = {
    root: null,
    rootMargin: '0px',
    threshold: 0.1
  };

  const observer = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('revealed');

        // Use anime for specific reveal
        anime({
          targets: entry.target,
          translateY: [30, 0],
          opacity: [0, 1],
          duration: 800,
          easing: 'easeOutQuart'
        });

        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  document.querySelectorAll('.reveal-on-scroll').forEach(el => {
    el.style.opacity = 0; // hide initially
    observer.observe(el);
  });
});
