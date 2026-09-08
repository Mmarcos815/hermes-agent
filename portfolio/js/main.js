// Bionic Daughter Portfolio — Interactive Charts & Animations

document.addEventListener('DOMContentLoaded', () => {
  // Animate progress bars on scroll
  animateProgressBars();
  
  // Initialize charts if on stats page
  if (document.getElementById('skills-chart')) {
    renderSkillsChart();
  }
  
  if (document.getElementById('activity-chart')) {
    renderActivityChart();
  }
  
  // Animate stat counters
  animateCounters();
  
  // Highlight active nav item
  highlightNav();
});

function animateProgressBars() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const bar = entry.target;
        const target = bar.getAttribute('data-target');
        if (target) {
          bar.style.width = target + '%';
        }
      }
    });
  }, { threshold: 0.5 });

  document.querySelectorAll('.progress-fill').forEach(bar => {
    observer.observe(bar);
  });
}

function animateCounters() {
  document.querySelectorAll('.counter').forEach(el => {
    const target = parseInt(el.getAttribute('data-target'));
    if (!target) return;
    
    let current = 0;
    const increment = target / 60;
    
    const timer = setInterval(() => {
      current += increment;
      if (current >= target) {
        current = target;
        clearInterval(timer);
      }
      el.textContent = Math.floor(current).toLocaleString();
    }, 16);
  });
}

function renderSkillsChart() {
  const data = [
    { label: 'Pentesting', value: 85 },
    { label: 'Web Exploit', value: 92 },
    { label: 'Forensics', value: 78 },
    { label: 'Crypto', value: 65 },
    { label: 'OSINT', value: 88 },
    { label: 'Reverse Eng', value: 72 },
    { label: 'Networking', value: 90 },
    { label: 'Social Eng', value: 82 }
  ];

  const container = document.getElementById('skills-chart');
  const maxVal = Math.max(...data.map(d => d.value));

  data.forEach(d => {
    const bar = document.createElement('div');
    bar.className = 'chart-bar';
    bar.style.height = (d.value / maxVal * 100) + '%';
    bar.innerHTML = `<span class="tooltip>${d.label}: ${d.value}%</span>`;
    container.appendChild(bar);
  });
}

function renderActivityChart() {
  const data = [
    { label: 'Mon', value: 12 },
    { label: 'Tue', value: 19 },
    { label: 'Wed', value: 8 },
    { label: 'Thu', value: 15 },
    { label: 'Fri', value: 22 },
    { label: 'Sat', value: 7 },
    { label: 'Sun', value: 14 }
  ];

  const container = document.getElementById('activity-chart');
  const labelsContainer = document.getElementById('activity-labels');
  const maxVal = Math.max(...data.map(d => d.value));

  data.forEach(d => {
    const bar = document.createElement('div');
    bar.className = 'chart-bar';
    bar.style.height = (d.value / maxVal * 100) + '%';
    bar.innerHTML = `<span class="tooltip">${d.value} commits</span>`;
    container.appendChild(bar);
    
    const label = document.createElement('span');
    label.textContent = d.label;
    labelsContainer.appendChild(label);
  });
}

function highlightNav() {
  const path = window.location.pathname;
  document.querySelectorAll('nav a').forEach(link => {
    if (link.getAttribute('href') && path.includes(link.getAttribute('href'))) {
      link.classList.add('active');
    }
  });
}

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function(e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute('href'));
    if (target) {
      target.scrollIntoView({ behavior: 'smooth' });
    }
  });
});
