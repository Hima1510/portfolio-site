(function () {
  'use strict';
  var root = document.documentElement;

  // Theme toggle
  var toggle = document.getElementById('theme-toggle');
  function currentTheme() {
    return root.getAttribute('data-theme') ||
      (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  }
  function syncToggle() {
    if (!toggle) return;
    var dark = currentTheme() === 'dark';
    toggle.setAttribute('aria-pressed', String(dark));
    toggle.textContent = dark ? 'Light mode' : 'Dark mode';
  }
  if (toggle) {
    toggle.addEventListener('click', function () {
      var next = currentTheme() === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', next);
      try { localStorage.setItem('theme', next); } catch (e) { /* ignore */ }
      syncToggle();
    });
    syncToggle();
  }

  // Project filter
  var chips = document.querySelectorAll('.chip');
  var projects = document.querySelectorAll('.project');
  var empty = document.getElementById('no-projects');
  chips.forEach(function (chip) {
    chip.addEventListener('click', function () {
      var wanted = chip.getAttribute('data-filter');
      var shown = 0;
      chips.forEach(function (c) { c.setAttribute('aria-pressed', String(c === chip)); });
      projects.forEach(function (p) {
        var match = wanted === 'all' || p.getAttribute('data-tags').split(' ').indexOf(wanted) !== -1;
        p.hidden = !match;
        if (match) shown += 1;
      });
      if (empty) empty.hidden = shown !== 0;
    });
  });

  // Footer year
  var year = document.getElementById('year');
  if (year) year.textContent = String(new Date().getFullYear());

  // Show which release is live (useful for checking deploys and rollbacks)
  var release = document.getElementById('release');
  if (release && window.fetch) {
    fetch('version.json', { cache: 'no-store' })
      .then(function (r) { return r.ok ? r.json() : Promise.reject(new Error('no version')); })
      .then(function (v) {
        var sha = v.git_sha && v.git_sha !== 'unknown' ? ' (' + String(v.git_sha).slice(0, 7) + ')' : '';
        release.textContent = v.version + sha;
      })
      .catch(function () { /* keep default text */ });
  }
})();
