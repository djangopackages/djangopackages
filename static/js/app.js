document.addEventListener("DOMContentLoaded", function () {
  // ============================================
  // Mobile Menu Toggle - Using data attributes
  // ============================================
  const mobileMenuBtn = document.getElementById("mobile-menu-btn");
  const mobileMenu = document.getElementById("mobile-menu");

  if (mobileMenuBtn && mobileMenu) {
    const toggle = () => {
      const isOpen = mobileMenu.classList.contains("hidden");
      mobileMenu.classList.toggle("hidden");
      mobileMenuBtn.setAttribute("aria-expanded", isOpen);
      mobileMenuBtn.querySelector("i").className = isOpen
        ? "ph-bold ph-x text-xl"
        : "ph-bold ph-list text-xl";
    };

    mobileMenuBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      toggle();
    });

    document.addEventListener("click", (e) => {
      if (
        !mobileMenu.classList.contains("hidden") &&
        !mobileMenu.contains(e.target) &&
        !mobileMenuBtn.contains(e.target)
      ) {
        toggle();
      }
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && !mobileMenu.classList.contains("hidden")) {
        toggle();
      }
    });
  }

  // ============================================
  // Category Tags Horizontal Scrolling
  // ============================================
  const scrollLeftBtn = document.getElementById("scroll-left");
  const scrollRightBtn = document.getElementById("scroll-right");
  const tagScroll1 = document.getElementById("tag-scroll-1");
  const tagScroll2 = document.getElementById("tag-scroll-2");

  if (scrollLeftBtn && scrollRightBtn && tagScroll1 && tagScroll2) {
    scrollLeftBtn.addEventListener("click", () => {
      const scrollAmount = 200;
      tagScroll1.scrollBy({ left: -scrollAmount, behavior: "smooth" });
      tagScroll2.scrollBy({ left: -scrollAmount, behavior: "smooth" });
    });

    scrollRightBtn.addEventListener("click", () => {
      const scrollAmount = 200;
      tagScroll1.scrollBy({ left: scrollAmount, behavior: "smooth" });
      tagScroll2.scrollBy({ left: scrollAmount, behavior: "smooth" });
    });
  }

  // ============================================
  // Horizontal Scrolling - Using event delegation
  // ============================================
  document.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-scroll]");
    if (!btn) return;

    const target = btn.dataset.scroll;
    const elements = document.querySelectorAll(target);
    const amount = btn.dataset.amount || 200;

    elements.forEach((el) =>
      el.scrollBy({
        left: parseInt(amount),
        behavior: "smooth",
      }),
    );
  });

  // ============================================
  // Search Suggestions Keyboard Navigation
  // ============================================
  const setupSuggestionNav = (input, dropdown) => {
    if (!input || !dropdown) return;

    dropdown.dataset.activeIndex = "-1";
    input.setAttribute("role", "combobox");
    input.setAttribute("aria-controls", dropdown.id);

    const updateSelection = (idx) => {
      const items = dropdown.querySelectorAll(".suggestion-item");
      dropdown.dataset.activeIndex = idx;
      items.forEach((item, i) => {
        const active = i === idx;
        item.classList.toggle("selected", active);
        item.toggleAttribute("aria-selected", active);
        if (active) item.scrollIntoView({ block: "nearest" });
      });
    };

    input.addEventListener("keydown", (e) => {
      const items = dropdown.querySelectorAll(".suggestion-item");
      if (!items.length) return;

      const current = Number(dropdown.dataset.activeIndex);

      if (e.key === "ArrowDown") {
        e.preventDefault();
        const loadMore = dropdown.querySelector(".suggestions-load-more");

        if (current === items.length - 1 && loadMore) {
          loadMore.scrollIntoView({ block: "nearest" });
        } else {
          updateSelection(current < 0 ? 0 : (current + 1) % items.length);
        }
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        updateSelection(current <= 0 ? items.length - 1 : current - 1);
      } else if (e.key === "Enter" && current >= 0) {
        e.preventDefault();
        items[current]?.click();
      } else if (e.key === "Escape") {
        updateSelection(-1);
      }
    });

    input.addEventListener("blur", () =>
      setTimeout(() => updateSelection(-1), 150),
    );
    dropdown.addEventListener("pointermove", () => updateSelection(-1));
  };

  // Setup all search inputs
  ["search-input", "navbar-search-input", "mobile-navbar-search-input"].forEach(
    (id) => {
      const input = document.getElementById(id);
      const dropdown = document.getElementById(
        id.replace("-input", "-dropdown").replace("search", "suggestions"),
      );
      setupSuggestionNav(input, dropdown);
    },
  );

  // Reset on HTMX swap
  document.body.addEventListener("htmx:afterSwap", (e) => {
    if (e.target.dataset.activeIndex !== undefined) {
      e.target.dataset.activeIndex = "-1";
    }
  });

  // ============================================
  // Search Placeholder Animation
  // ============================================
  const animatePlaceholder = (input, texts) => {
    if (!input) return;

    let textIndex = 0;
    let charIndex = 0;
    let isDeleting = false;
    let typeSpeed = 100;

    const type = () => {
      // Stop if input is focused
      if (document.activeElement === input) {
        setTimeout(type, 1000);
        return;
      }

      const currentText = texts[textIndex];

      if (isDeleting) {
        input.setAttribute(
          "placeholder",
          currentText.substring(0, charIndex - 1),
        );
        charIndex--;
        typeSpeed = 50;
      } else {
        input.setAttribute(
          "placeholder",
          currentText.substring(0, charIndex + 1),
        );
        charIndex++;
        typeSpeed = 100;
      }

      if (!isDeleting && charIndex === currentText.length) {
        isDeleting = true;
        typeSpeed = 2000; // Pause at end
      } else if (isDeleting && charIndex === 0) {
        isDeleting = false;
        textIndex = (textIndex + 1) % texts.length;
        typeSpeed = 500; // Pause before typing next
      }

      setTimeout(type, typeSpeed);
    };

    type();
  };

  // Initialize placeholder animation for main search
  const mainSearchInput = document.getElementById("search-input");
  if (mainSearchInput) {
    animatePlaceholder(mainSearchInput, [
      "Search Django packages...",
      'Try "authentication"',
      'Try "cms"',
      'Try "api"',
      'Try "rest"',
    ]);
  }

  // Initialize placeholder animation for navbar search
  const navbarSearchInput = document.getElementById("navbar-search-input");
  if (navbarSearchInput) {
    animatePlaceholder(navbarSearchInput, [
      "Search packages...",
      'Try "auth"',
      'Try "rest"',
      'Try "admin"',
    ]);
  }

  // Initialize placeholder animation for navbar search - mobile
  const mobileNavbarSearchInput = document.getElementById(
    "mobile-navbar-search-input",
  );
  if (mobileNavbarSearchInput) {
    animatePlaceholder(mobileNavbarSearchInput, [
      "Search packages...",
      'Try "auth"',
      'Try "rest"',
      'Try "admin"',
    ]);
  }

  // ============================================
  // Global Keyboard Shortcuts
  // ============================================
  document.addEventListener("keydown", (e) => {
    // CMD+/ or CTRL+/ to focus search
    if ((e.metaKey || e.ctrlKey) && e.key === "/") {
      e.preventDefault();
      const searchInput =
        document.getElementById("search-input") ||
        document.getElementById("navbar-search-input");
      if (searchInput) {
        searchInput.focus();
      }
    }

    // Just / to focus search (if not already in input)
    if (
      e.key === "/" &&
      !["INPUT", "TEXTAREA"].includes(document.activeElement.tagName)
    ) {
      e.preventDefault();
      const searchInput =
        document.getElementById("search-input") ||
        document.getElementById("navbar-search-input");
      if (searchInput) {
        searchInput.focus();
      }
    }

    // Escape to unfocus input
    if (
      e.key === "Escape" &&
      ["INPUT", "TEXTAREA"].includes(document.activeElement.tagName)
    ) {
      document.activeElement.blur();
    }
  });

  // ============================================
  // Flag Button (Package Detail Page)
  // ============================================
  // const flagBtn = document.getElementById('flag-btn');
  // const flagText = document.getElementById('flag-text');

  // if (flagBtn && flagText) {
  //     let flagged = false;
  //     flagBtn.addEventListener('click', function() {
  //         flagged = !flagged;
  //         if (flagged) {
  //             flagBtn.classList.add('bg-destructive/10', 'text-destructive', 'border-destructive');
  //             flagText.textContent = 'Flagged';
  //         } else {
  //             flagBtn.classList.remove('bg-destructive/10', 'text-destructive', 'border-destructive');
  //             flagText.textContent = 'Flag';
  //         }
  //     });
  // }

  // ============================================
  // Copy Badge Button (Package Detail Page)
  // ============================================
  const copyBadgeBtn = document.getElementById("copy-badge-btn");
  if (copyBadgeBtn) {
    const copyText = document.getElementById("copy-text");
    const copyIcon = document.getElementById("copy-icon");
    const originalText = copyText ? copyText.textContent : "";

    copyBadgeBtn.addEventListener("click", function () {
      const badgeText = this.previousElementSibling.textContent;
      navigator.clipboard
        .writeText(badgeText)
        .then(() => {
          if (copyText) copyText.textContent = "Copied!";
          if (copyIcon) copyIcon.className = "ph-bold ph-check text-base mr-2";

          setTimeout(() => {
            if (copyText) copyText.textContent = originalText;
            if (copyIcon) copyIcon.className = "ph-bold ph-copy text-base mr-2";
          }, 2000);
        })
        .catch((err) => {
          console.error("Failed to copy:", err);
        });
    });
  }

  // ============================================
  // Toast Notifications Auto-Dismiss
  // ============================================
  const toastContainer = document.getElementById("toast-container");
  if (toastContainer) {
    const messages = toastContainer.querySelectorAll('[role="alert"]');
    messages.forEach((msg) => {
      setTimeout(() => {
        msg.style.transition = "opacity 0.5s ease-out";
        msg.style.opacity = "0";
        setTimeout(() => msg.remove(), 500);
      }, 10000);
    });
  }
});
