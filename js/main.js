/* Fresh Mart Faridpur — progressively enhanced navigation and ordering. */
(function () {
  'use strict';

  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const focusableSelector = 'a[href], button, input, select, textarea, [tabindex], [contenteditable="true"]';
  const savedTabIndexes = new WeakMap();

  function ensureId(element, preferredId) {
    if (element.id) return element.id;
    let id = preferredId;
    let suffix = 2;
    while (document.getElementById(id)) id = preferredId + '-' + suffix++;
    element.id = id;
    return id;
  }

  // Keep inactive content out of keyboard navigation, including older browsers.
  function setUnavailable(element, unavailable) {
    element.setAttribute('aria-hidden', String(unavailable));
    if ('inert' in element) {
      element.inert = unavailable;
      return;
    }
    element.querySelectorAll(focusableSelector).forEach((item) => {
      if (unavailable) {
        if (!savedTabIndexes.has(item)) savedTabIndexes.set(item, item.getAttribute('tabindex'));
        item.setAttribute('tabindex', '-1');
      } else if (savedTabIndexes.has(item)) {
        const previous = savedTabIndexes.get(item);
        if (previous === null) item.removeAttribute('tabindex');
        else item.setAttribute('tabindex', previous);
        savedTabIndexes.delete(item);
      }
    });
  }

  // Content is visible immediately; decorative effects never gate access to it.
  document.querySelectorAll('.reveal').forEach((element) => element.classList.add('in'));

  const toggle = document.querySelector('.nav-toggle');
  const menu = document.querySelector('.nav-menu');
  if (toggle && menu) {
    document.documentElement.classList.add('nav-ready');
    const mobileNavigation = window.matchMedia('(max-width: 960px)');
    toggle.setAttribute('aria-controls', ensureId(menu, 'primaryNavigation'));
    toggle.setAttribute('type', 'button');
    if (!toggle.getAttribute('aria-label')) toggle.setAttribute('aria-label', 'মেনু খুলুন');

    const setMenuOpen = (open, restoreFocus) => {
      const expanded = mobileNavigation.matches && open;
      menu.classList.toggle('open', expanded);
      toggle.setAttribute('aria-expanded', String(expanded));
      toggle.setAttribute('aria-label', expanded ? 'মেনু বন্ধ করুন' : 'মেনু খুলুন');
      setUnavailable(menu, mobileNavigation.matches && !expanded);
      if (restoreFocus) toggle.focus({ preventScroll: true });
    };

    toggle.addEventListener('click', () => setMenuOpen(!menu.classList.contains('open')));
    menu.querySelectorAll('a').forEach((link) => {
      link.addEventListener('click', () => setMenuOpen(false));
    });
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && menu.classList.contains('open')) {
        event.preventDefault();
        setMenuOpen(false, true);
      }
    });
    document.addEventListener('click', (event) => {
      if (!menu.contains(event.target) && !toggle.contains(event.target)) setMenuOpen(false);
    });
    const resetNavigation = () => setMenuOpen(false);
    if (mobileNavigation.addEventListener) mobileNavigation.addEventListener('change', resetNavigation);
    else mobileNavigation.addListener(resetNavigation);
    setMenuOpen(false);
  }

  document.querySelectorAll('.price-tabs').forEach((tablist, groupIndex) => {
    const scope = tablist.closest('.pricelist-wrap') || tablist.parentElement;
    const panels = Array.from(scope.querySelectorAll('.pricelist-panel'));
    const tabs = Array.from(tablist.querySelectorAll('button[data-tab]')).filter((tab) => {
      return panels.some((panel) => panel.dataset.panel === tab.dataset.tab);
    });
    if (!tabs.length) return;
    tablist.setAttribute('role', 'tablist');
    if (!tablist.getAttribute('aria-label')) tablist.setAttribute('aria-label', 'পণ্যের ধরন');

    tabs.forEach((tab, index) => {
      const panel = panels.find((item) => item.dataset.panel === tab.dataset.tab);
      // Preserve category anchors while repairing the legacy nested duplicate IDs.
      const categoryAnchor = panel.id || tab.dataset.tab;
      panel.querySelectorAll('[id]').forEach((child) => {
        if (child.id === categoryAnchor) child.removeAttribute('id');
      });
      const panelId = ensureId(panel, categoryAnchor || 'price-panel-' + groupIndex + '-' + index);
      const tabId = ensureId(tab, 'price-tab-' + groupIndex + '-' + index);
      tab.setAttribute('type', 'button');
      tab.setAttribute('role', 'tab');
      tab.setAttribute('aria-controls', panelId);
      panel.setAttribute('role', 'tabpanel');
      panel.setAttribute('aria-labelledby', tabId);
      panel.setAttribute('tabindex', '0');
      // The hidden attribute becomes the single source of panel visibility.
      panel.style.removeProperty('display');
    });

    const selectTab = (selected, updateHash) => {
      tabs.forEach((tab) => {
        const active = tab === selected;
        tab.classList.toggle('active', active);
        tab.setAttribute('aria-selected', String(active));
        tab.tabIndex = active ? 0 : -1;
      });
      panels.forEach((panel) => {
        panel.hidden = panel.dataset.panel !== selected.dataset.tab;
      });
      if (updateHash) {
        try {
          window.history.replaceState(window.history.state, '', '#' + encodeURIComponent(selected.dataset.tab));
        } catch (error) {
          // Tab selection still works when history changes are unavailable.
        }
      }
    };

    const selectFromHash = () => {
      let hash;
      try { hash = decodeURIComponent(window.location.hash.slice(1)); }
      catch (error) { return false; }
      const tab = tabs.find((item) => item.dataset.tab === hash);
      if (!tab) return false;
      selectTab(tab, false);
      return true;
    };

    tabs.forEach((tab, index) => {
      tab.addEventListener('click', () => selectTab(tab, true));
      tab.addEventListener('keydown', (event) => {
        let targetIndex;
        if (event.key === 'ArrowRight') targetIndex = (index + 1) % tabs.length;
        else if (event.key === 'ArrowLeft') targetIndex = (index - 1 + tabs.length) % tabs.length;
        else if (event.key === 'Home') targetIndex = 0;
        else if (event.key === 'End') targetIndex = tabs.length - 1;
        else return;
        event.preventDefault();
        const target = tabs[targetIndex];
        target.focus({ preventScroll: true });
        selectTab(target, true);
      });
    });
    if (!selectFromHash()) selectTab(tabs.find((tab) => tab.classList.contains('active')) || tabs[0], false);
    window.addEventListener('hashchange', selectFromHash);
  });

  document.querySelectorAll('.reel[data-href]').forEach((element) => {
    const url = element.dataset.href;
    if (!/^https?:\/\//i.test(url)) return;
    if (element.tagName === 'A') {
      element.href = url;
      element.target = '_blank';
      element.rel = 'noopener noreferrer';
      return;
    }
    element.setAttribute('role', 'link');
    element.tabIndex = 0;
    const openReel = () => window.open(url, '_blank', 'noopener,noreferrer');
    element.addEventListener('click', openReel);
    element.addEventListener('keydown', (event) => {
      if (event.key === 'Enter') {
        event.preventDefault();
        openReel();
      }
    });
  });

  const form = document.getElementById('orderForm');
  if (form) {
    let message = form.querySelector('.form-msg');
    if (!message) {
      message = document.createElement('div');
      message.className = 'form-msg';
      form.appendChild(message);
    }
    message.setAttribute('role', 'status');
    message.setAttribute('aria-live', 'polite');
    form.querySelectorAll('[required]').forEach((field) => {
      field.addEventListener('input', () => field.setCustomValidity(''));
    });

    const normalizePhone = (value) => {
      const digits = value.replace(/[০-৯]/g, (digit) => String('০১২৩৪৫৬৭৮৯'.indexOf(digit))).replace(/[\s()-]/g, '');
      if (/^01[3-9]\d{8}$/.test(digits)) return '+88' + digits;
      if (/^8801[3-9]\d{8}$/.test(digits)) return '+' + digits;
      return digits;
    };

    form.addEventListener('submit', (event) => {
      event.preventDefault();
      form.querySelectorAll('[required]').forEach((field) => {
        field.setCustomValidity(field.value.trim() ? '' : 'এই তথ্যটি লিখুন।');
      });
      if (!form.reportValidity()) return;
      const data = new FormData(form);
      const value = (name) => String(data.get(name) || '').trim();
      const lines = [
        '*Fresh Mart Faridpur — অর্ডারের অনুরোধ*',
        'নাম: ' + value('name'),
        'ফোন: ' + normalizePhone(value('phone')),
        'ঠিকানা: ' + value('address'),
        'অর্ডার: ' + value('order'),
        value('note') ? 'নোট: ' + value('note') : null
      ].filter(Boolean);
      const url = 'https://wa.me/8801611402642?text=' + encodeURIComponent(lines.join('\n'));

      // Open within the submit gesture so the browser can allow the new tab.
      try { window.open(url, '_blank', 'noopener,noreferrer'); }
      catch (error) { /* The visible link below remains available. */ }
      message.textContent = 'অর্ডারের বিবরণ প্রস্তুত। WhatsApp-এ মেসেজটি পাঠিয়ে আমাদের সঙ্গে অর্ডার নিশ্চিত করুন। WhatsApp না খুললে: ';
      const fallback = document.createElement('a');
      fallback.href = url;
      fallback.target = '_blank';
      fallback.rel = 'noopener noreferrer';
      fallback.textContent = 'WhatsApp খুলুন';
      message.appendChild(fallback);
      message.classList.add('show');
      // Retain the customer's input until they choose to change it.
    });
  }

  document.querySelectorAll('[data-year], #year').forEach((element) => {
    element.textContent = String(new Date().getFullYear());
  });

  const slider = document.getElementById('heroSlider');
  if (slider) {
    const slides = Array.from(slider.querySelectorAll('.hero-slide'));
    if (!slides.length) return;
    const dots = Array.from(slider.querySelectorAll('.hero-dot'));
    const previous = slider.querySelector('.hero-arrow-prev');
    const next = slider.querySelector('.hero-arrow-next');
    const pause = slider.querySelector('.hero-pause');
    const status = slider.querySelector('#heroSlideStatus');
    let current = Math.max(0, slides.findIndex((slide) => slide.classList.contains('is-active')));
    let timer = null;
    let userPaused = reducedMotion.matches;
    let explicitlyPlaying = false;
    let hovered = false;
    let focusWithin = slider.contains(document.activeElement);
    const bengaliNumber = (number) => String(number).padStart(2, '0').replace(/\d/g, (digit) => '০১২৩৪৫৬৭৮৯'[Number(digit)]);

    if (!slider.getAttribute('role')) slider.setAttribute('role', 'region');
    slider.setAttribute('aria-roledescription', 'carousel');
    if (!slider.getAttribute('aria-label')) slider.setAttribute('aria-label', 'আমাদের পণ্যের ছবি');
    if (!slider.hasAttribute('tabindex')) slider.setAttribute('tabindex', '-1');
    slides.forEach((slide, index) => {
      ensureId(slide, 'hero-slide-' + (index + 1));
      slide.setAttribute('role', 'group');
      slide.setAttribute('aria-roledescription', 'slide');
      if (!slide.getAttribute('aria-label')) slide.setAttribute('aria-label', (index + 1) + ' / ' + slides.length);
    });
    [previous, next, pause, ...dots].filter(Boolean).forEach((button) => button.setAttribute('type', 'button'));
    dots.forEach((dot, index) => {
      const requested = Number(dot.dataset.slide);
      const slideIndex = Number.isInteger(requested) && requested >= 0 && requested < slides.length ? requested : index;
      if (slides[slideIndex]) dot.setAttribute('aria-controls', slides[slideIndex].id);
      if (!dot.getAttribute('aria-label')) dot.setAttribute('aria-label', bengaliNumber(slideIndex + 1) + ' নম্বর ছবি দেখুন');
    });
    if (status) status.setAttribute('aria-atomic', 'true');

    const stop = () => {
      if (timer !== null) window.clearInterval(timer);
      timer = null;
    };

    const syncPlayback = () => {
      stop();
      const interactionPaused = !explicitlyPlaying && (hovered || focusWithin);
      const suspended = userPaused || interactionPaused || document.hidden || slides.length < 2;
      slider.dataset.autoplay = suspended ? 'paused' : 'playing';
      if (status) status.setAttribute('aria-live', userPaused || (focusWithin && !explicitlyPlaying) ? 'polite' : 'off');
      if (pause) {
        pause.setAttribute('aria-pressed', String(userPaused));
        const label = userPaused ? 'স্লাইড চালু করুন' : 'স্লাইড থামান';
        pause.setAttribute('aria-label', label);
        const labelElement = pause.querySelector('[data-pause-label]');
        if (labelElement) labelElement.textContent = userPaused ? 'চালু' : 'বিরতি';
        else if (!pause.querySelector('svg, img')) pause.textContent = label;
        pause.disabled = slides.length < 2;
      }
      if (!suspended) timer = window.setInterval(() => goTo(current + 1), 6500);
    };

    const goTo = (index) => {
      const destination = (index + slides.length) % slides.length;
      const activeElement = document.activeElement;
      if (destination !== current && slides[current].contains(activeElement)) {
        (next || dots[destination] || slider).focus({ preventScroll: true });
      }
      current = destination;
      slides.forEach((slide, slideIndex) => {
        const active = slideIndex === current;
        slide.classList.toggle('is-active', active);
        setUnavailable(slide, !active);
      });
      dots.forEach((dot, dotIndex) => {
        const requested = Number(dot.dataset.slide);
        const slideIndex = Number.isInteger(requested) && requested >= 0 && requested < slides.length ? requested : dotIndex;
        const active = slideIndex === current;
        dot.classList.toggle('is-active', active);
        dot.setAttribute('aria-pressed', String(active));
      });
      if (status) status.textContent = bengaliNumber(current + 1) + ' / ' + bengaliNumber(slides.length);
    };

    const manuallyGoTo = (index) => {
      explicitlyPlaying = false;
      goTo(index);
      syncPlayback();
    };
    if (previous) previous.addEventListener('click', () => manuallyGoTo(current - 1));
    if (next) next.addEventListener('click', () => manuallyGoTo(current + 1));
    dots.forEach((dot, index) => {
      dot.addEventListener('click', () => {
        const requested = Number(dot.dataset.slide);
        manuallyGoTo(Number.isInteger(requested) && requested >= 0 && requested < slides.length ? requested : index);
      });
    });
    // On phones, a horizontal swipe changes the photo without trapping vertical page scroll.
    const swipeArea = slider.querySelector('.hero-image-stage');
    if (swipeArea && slides.length > 1) {
      let swipeStart = null;
      swipeArea.addEventListener('touchstart', (event) => {
        if (event.touches.length !== 1) { swipeStart = null; return; }
        swipeStart = { x: event.touches[0].clientX, y: event.touches[0].clientY };
      }, { passive: true });
      swipeArea.addEventListener('touchend', (event) => {
        if (!swipeStart || event.changedTouches.length !== 1) return;
        const distanceX = event.changedTouches[0].clientX - swipeStart.x;
        const distanceY = event.changedTouches[0].clientY - swipeStart.y;
        swipeStart = null;
        if (Math.abs(distanceX) >= 44 && Math.abs(distanceX) > Math.abs(distanceY) * 1.35) {
          manuallyGoTo(current + (distanceX < 0 ? 1 : -1));
        }
      }, { passive: true });
      swipeArea.addEventListener('touchcancel', () => { swipeStart = null; }, { passive: true });
    }
    if (pause) pause.addEventListener('click', () => {
      userPaused = !userPaused;
      // An explicit play request works while the play control still has focus.
      explicitlyPlaying = !userPaused;
      syncPlayback();
    });
    slider.addEventListener('mouseenter', () => { hovered = true; explicitlyPlaying = false; syncPlayback(); });
    slider.addEventListener('mouseleave', () => { hovered = false; syncPlayback(); });
    slider.addEventListener('focusin', () => { focusWithin = true; explicitlyPlaying = false; syncPlayback(); });
    slider.addEventListener('focusout', (event) => {
      focusWithin = !!event.relatedTarget && slider.contains(event.relatedTarget);
      syncPlayback();
    });
    slider.addEventListener('keydown', (event) => {
      if (event.target.closest('input, textarea, select, [contenteditable="true"]')) return;
      if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return;
      event.preventDefault();
      manuallyGoTo(current + (event.key === 'ArrowRight' ? 1 : -1));
    });
    document.addEventListener('visibilitychange', syncPlayback);
    const handleMotionPreference = () => {
      if (reducedMotion.matches) {
        userPaused = true;
        explicitlyPlaying = false;
      }
      syncPlayback();
    };
    if (reducedMotion.addEventListener) reducedMotion.addEventListener('change', handleMotionPreference);
    else reducedMotion.addListener(handleMotionPreference);
    goTo(current);
    syncPlayback();
  }

  // Product quantities are drafts until the customer adds them to their list.
  const directGrid = document.getElementById('directProductsGrid');
  const filterTabs = Array.from(document.querySelectorAll('.filter-tab'));
  const floatingBar = document.getElementById('floatingOrderBar');
  const cartCountEl = document.getElementById('cartCount');
  const cartTotalEl = document.getElementById('cartTotal');
  const cartTotalNote = document.getElementById('cartTotalNote');
  const filterStatus = document.getElementById('productFilterStatus');
  const productSearch = document.getElementById('productSearch');
  const productEmptyState = document.getElementById('productEmptyState');
  const barOrderBtn = document.getElementById('barOrderBtn');
  const barClearBtn = document.getElementById('barClearBtn');

  if (directGrid) {
    const cards = Array.from(directGrid.querySelectorAll('.direct-card'));
    const bengaliDigits = (num) => String(num).replace(/\d/g, (d) => '০১২৩৪৫৬৭৮৯'[Number(d)]);
    const bengaliPad2 = (num) => String(num).padStart(2, '0').replace(/\d/g, (d) => '০১২৩৪৫৬৭৮৯'[Number(d)]);
    const selected = new Map();
    const controllers = new Map();
    const storageKey = 'freshmart-order-list-v1';
    const categoryNames = new Set(['all', 'veg', 'fish', 'meat', 'spice', 'dairy', 'combos']);
    const availableFilters = filterTabs.filter((tab) => categoryNames.has(tab.dataset.filter));
    let currentCategory = 'all';
    const money = (value) => bengaliDigits(Number(value.toFixed(2)));
    const whatsappLink = (lines) => 'https://wa.me/8801611402642?text=' + encodeURIComponent(lines.join('\n'));
    const cleanText = (value, maxLength) => typeof value === 'string'
      ? value.replace(/[\u0000-\u001f\u007f]/g, ' ').replace(/\s+/g, ' ').trim().slice(0, maxLength)
      : '';
    const productId = (card) => cleanText(card.dataset.productId, 256)
      || 'name:' + cleanText(card.dataset.name || 'পণ্য', 160) + '|unit:' + cleanText(card.dataset.unit || '১ ইউনিট', 100);
    const itemDetails = (card, qty) => {
      const priceText = String(card.dataset.price || '').trim();
      const parsedPrice = priceText ? Number(priceText) : NaN;
      return {
        id: productId(card),
        name: cleanText(card.dataset.name || 'পণ্য', 160),
        unit: cleanText(card.dataset.unit || '১ ইউনিট', 100),
        qty,
        // An absent or invalid price is unknown, never a free item.
        price: Number.isFinite(parsedPrice) && parsedPrice > 0 ? parsedPrice : null
      };
    };
    // Keep only product choices in this tab's session; customer details are never saved.
    const restoreOrderList = () => {
      try {
        const raw = window.sessionStorage.getItem(storageKey);
        if (raw && raw.length > 128000) return false;
        const saved = raw ? JSON.parse(raw) : { version: 1, items: [] };
        if (!saved || saved.version !== 1 || !Array.isArray(saved.items) || saved.items.length > 100) return false;
        const restored = new Map();
        saved.items.forEach((record) => {
          if (!record || typeof record !== 'object') return;
          const id = cleanText(record.id, 256);
          const name = cleanText(record.name, 160);
          const unit = cleanText(record.unit, 100);
          const qty = record.qty;
          const price = record.price;
          if (!id || !name || !unit || !Number.isInteger(qty) || qty < 1 || qty > 99) return;
          if (price !== null && (typeof price !== 'number' || !Number.isFinite(price) || price <= 0 || price > 1000000)) return;
          restored.set(id, { id, name, unit, qty, price });
        });
        // Current card information takes precedence over a saved indicative price.
        const refreshed = new Set();
        cards.forEach((card) => {
          const id = productId(card);
          if (restored.has(id) && !refreshed.has(id)) {
            restored.set(id, itemDetails(card, restored.get(id).qty));
            refreshed.add(id);
          }
        });
        selected.clear();
        restored.forEach((item, id) => selected.set(id, item));
        return true;
      } catch (error) {
        // Ordering remains usable when storage is blocked or contains invalid data.
        return false;
      }
    };
    const saveOrderList = () => {
      try {
        if (selected.size) {
          window.sessionStorage.setItem(storageKey, JSON.stringify({ version: 1, items: Array.from(selected.values()) }));
        } else {
          window.sessionStorage.removeItem(storageKey);
        }
      } catch (error) {
        // The in-memory order remains available even when storage cannot be written.
      }
    };
    restoreOrderList();
    const itemLine = (item) => {
      const amount = item.price === null ? 'দাম নিশ্চিত করুন' : 'আনুমানিক ৳' + money(item.price * item.qty);
      return '• ' + item.name + ' (' + item.unit + ') × ' + bengaliDigits(item.qty) + ' — ' + amount;
    };
    const confirmationLine = 'দয়া করে পণ্যের প্রাপ্যতা, পরিমাণ, চূড়ান্ত দাম ও ডেলিভারি চার্জ জানিয়ে অর্ডার নিশ্চিত করতে সাহায্য করুন।';

    // These are native filter buttons, so Tab, Enter and Space work normally.
    const normalizeSearch = (value) => String(value || '').normalize('NFC').toLocaleLowerCase('bn').trim();
    const filterCards = () => {
      const query = normalizeSearch(productSearch ? productSearch.value : '');
      const terms = query.split(/\s+/).filter(Boolean);
      availableFilters.forEach((tab) => {
        const active = tab.dataset.filter === currentCategory;
        tab.classList.toggle('is-active', active);
        tab.setAttribute('aria-pressed', String(active));
      });
      let visibleCount = 0;
      cards.forEach((card) => {
        const searchText = normalizeSearch([card.dataset.name, card.dataset.unit, card.dataset.search].filter(Boolean).join(' '));
        const match = (currentCategory === 'all' || card.dataset.category === currentCategory)
          && terms.every((term) => searchText.includes(term));
        card.hidden = !match;
        card.classList.remove('is-hidden');
        if (match) visibleCount += 1;
      });
      if (productEmptyState) productEmptyState.hidden = visibleCount > 0;
      if (filterStatus) {
        filterStatus.textContent = visibleCount ? bengaliDigits(visibleCount) + 'টি পণ্য দেখানো হচ্ছে'
          : query ? 'এই খোঁজের সঙ্গে মিলে এমন পণ্য নেই। অন্য নাম বা বিভাগ দিয়ে চেষ্টা করুন।' : 'এই বিভাগে বর্তমানে কোনো পণ্য নেই।';
      }
    };
    const selectFilter = (category, updateHash) => {
      currentCategory = categoryNames.has(category) ? category : 'all';
      filterCards();
      if (updateHash && document.body.classList.contains('catalog-page')) {
        try {
          window.history.replaceState(window.history.state, '', '#' + currentCategory);
        } catch (error) { /* Filtering still works without history access. */ }
      }
    };
    const filterFromHash = () => {
      let category;
      try { category = decodeURIComponent(window.location.hash.slice(1)); }
      catch (error) { return false; }
      if (!categoryNames.has(category) || !availableFilters.some((tab) => tab.dataset.filter === category)) return false;
      selectFilter(category, false);
      return true;
    };
    availableFilters.forEach((tab) => {
      tab.setAttribute('type', 'button');
      tab.removeAttribute('role');
      tab.removeAttribute('aria-selected');
      tab.removeAttribute('tabindex');
      tab.addEventListener('click', () => selectFilter(tab.dataset.filter, true));
    });
    if (availableFilters[0] && availableFilters[0].parentElement) availableFilters[0].parentElement.setAttribute('role', 'group');
    if (filterStatus) {
      filterStatus.setAttribute('role', 'status');
      filterStatus.setAttribute('aria-live', 'polite');
      filterStatus.setAttribute('aria-atomic', 'true');
    }
    if (!filterFromHash()) {
      const initialTab = availableFilters.find((tab) => tab.classList.contains('is-active')) || availableFilters[0];
      selectFilter(initialTab ? initialTab.dataset.filter : 'all', false);
    }
    window.addEventListener('hashchange', filterFromHash);
    if (productSearch) productSearch.addEventListener('input', filterCards);

    const updateSingleCardLink = (card, qty) => {
      const orderBtn = card.querySelector('.direct-btn-order');
      if (!orderBtn) return;
      const item = itemDetails(card, qty);
      orderBtn.href = whatsappLink([
        'আসসালামু আলাইকুম, Fresh Mart Faridpur থেকে অর্ডার করতে চাই:',
        itemLine(item),
        'ডেলিভারি চার্জ আলাদা।',
        confirmationLine
      ]);
      orderBtn.setAttribute('aria-label', item.name + ' ' + bengaliDigits(qty) + ' ইউনিট WhatsApp-এ অর্ডারের অনুরোধ করুন');
    };

    const updateFloatingBar = () => {
      const items = Array.from(selected.values());
      const pricedItems = items.filter((item) => item.price !== null);
      const unknownCount = items.length - pricedItems.length;
      const subtotal = pricedItems.reduce((sum, item) => sum + item.price * item.qty, 0);
      if (floatingBar) floatingBar.hidden = items.length === 0;
      document.body.classList.toggle('has-order-list', items.length > 0);
      if (cartCountEl) cartCountEl.textContent = bengaliDigits(items.length);
      if (cartTotalEl) cartTotalEl.textContent = pricedItems.length ? '৳ ' + money(subtotal) : 'দাম নিশ্চিত করুন';
      const note = [
        pricedItems.length ? 'জানা দামের আনুমানিক উপমোট' : 'পণ্যের দাম নিশ্চিত করতে হবে',
        unknownCount && pricedItems.length ? bengaliDigits(unknownCount) + 'টি পণ্যের দাম যোগ হবে' : null,
        'ডেলিভারি চার্জ আলাদা'
      ].filter(Boolean).join(' · ');
      if (cartTotalNote) cartTotalNote.textContent = note;
      if (barOrderBtn) {
        const summary = pricedItems.length ? 'জানা দামের আনুমানিক উপমোট: ৳' + money(subtotal) : 'পণ্যের দাম নিশ্চিত করুন।';
        barOrderBtn.href = whatsappLink([
          '*Fresh Mart Faridpur — অর্ডারের অনুরোধ*',
          ...items.map(itemLine),
          summary,
          unknownCount ? bengaliDigits(unknownCount) + 'টি পণ্যের দাম এই উপমোটে অন্তর্ভুক্ত নয়।' : null,
          'ডেলিভারি চার্জ আলাদা।',
          confirmationLine
        ].filter(Boolean));
      }
    };

    cards.forEach((card) => {
      let currentQty = 1;
      const minusBtn = card.querySelector('.direct-qty-btn.minus');
      const plusBtn = card.querySelector('.direct-qty-btn.plus');
      const valEl = card.querySelector('.direct-qty-val');
      const addBtn = card.querySelector('.direct-btn-add');
      const name = card.dataset.name || 'পণ্য';

      const updateAddButton = () => {
        if (!addBtn) return;
        const selection = selected.get(productId(card));
        const saved = !!selection && selection.qty === currentQty;
        const isDetailPage = document.body.classList.contains('product-detail-page');
        const label = isDetailPage
          ? (saved ? 'কার্টে যোগ হয়েছে' : selection ? 'কার্ট আপডেট করুন' : 'কার্টে যোগ করুন')
          : (saved ? 'তালিকায় যোগ হয়েছে' : selection ? 'তালিকা আপডেট করুন' : 'তালিকায় যোগ করুন');
        addBtn.textContent = label;
        addBtn.classList.toggle('is-added', saved);
        addBtn.setAttribute('aria-label', name + ' ' + bengaliDigits(currentQty) + ' ইউনিট — ' + label);
        card.dataset.userQty = selection ? String(selection.qty) : '0';
      };

      const setCardQty = (qty) => {
        currentQty = Math.min(99, Math.max(1, Math.floor(qty)));
        card.dataset.currentQty = String(currentQty);
        if (valEl) valEl.textContent = bengaliPad2(currentQty);
        if (minusBtn) minusBtn.disabled = currentQty === 1;
        if (plusBtn) plusBtn.disabled = currentQty === 99;
        updateSingleCardLink(card, currentQty);
        updateAddButton();
      };
      if (valEl) {
        valEl.setAttribute('role', 'status');
        valEl.setAttribute('aria-live', 'polite');
        valEl.setAttribute('aria-atomic', 'true');
        valEl.setAttribute('aria-label', name + ' এর নির্বাচিত পরিমাণ');
      }
      if (plusBtn) {
        plusBtn.setAttribute('aria-label', name + ' এর পরিমাণ বাড়ান');
        plusBtn.addEventListener('click', () => setCardQty(currentQty + 1));
      }
      if (minusBtn) {
        minusBtn.setAttribute('aria-label', name + ' এর পরিমাণ কমান');
        minusBtn.addEventListener('click', () => setCardQty(currentQty - 1));
      }
      if (addBtn) {
        addBtn.setAttribute('type', 'button');
        addBtn.addEventListener('click', () => {
          const id = productId(card);
          if (!selected.has(id) && selected.size >= 100) return;
          selected.set(id, itemDetails(card, currentQty));
          controllers.forEach((controller) => controller.updateAddButton());
          saveOrderList();
          updateFloatingBar();
        });
      }
      controllers.set(card, { setCardQty, updateAddButton });
      const selection = selected.get(productId(card));
      setCardQty(selection ? selection.qty : 1);
    });

    if (barClearBtn) {
      barClearBtn.addEventListener('click', () => {
        // Restore focus before the clearing control disappears with its bar.
        const focused = floatingBar && floatingBar.contains(document.activeElement);
        selected.clear();
        cards.forEach((card) => {
          card.dataset.userQty = '0';
          controllers.get(card).setCardQty(1);
        });
        if (focused) {
          const visibleCard = cards.find((card) => !card.hidden);
          const focusTarget = visibleCard && visibleCard.querySelector('.direct-btn-add, .direct-btn-order');
          if (focusTarget) focusTarget.focus({ preventScroll: true });
        }
        saveOrderList();
        updateFloatingBar();
      });
    }
    // Back/Forward can restore a page without rerunning its script.
    window.addEventListener('pageshow', (event) => {
      if (!event.persisted || !restoreOrderList()) return;
      cards.forEach((card) => {
        const selection = selected.get(productId(card));
        controllers.get(card).setCardQty(selection ? selection.qty : 1);
      });
      saveOrderList();
      updateFloatingBar();
    });
    saveOrderList();
    updateFloatingBar();
  }
})();
