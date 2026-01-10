document.addEventListener("DOMContentLoaded", function () {
    // ============================================
    // Grid Comparison Table Functions
    // ============================================

    function abbreviateGridNumbers() {
        document.querySelectorAll('[data-abbreviate]').forEach(function(el) {
            if (el.dataset.abbreviated) return;
            const num = parseInt(el.textContent.replace(/,/g, ''), 10);
            if (!isNaN(num) && num >= 1000) {
                el.title = num.toLocaleString();
                if (num >= 1000000) {
                    el.textContent = (num / 1000000).toFixed(1) + 'M';
                } else if (num >= 1000) {
                    el.textContent = (num / 1000).toFixed(1) + 'K';
                }
                el.dataset.abbreviated = 'true';
            }
        });
    }

    // Initialize grid table if present
    if (document.getElementById('comparison-table')) {
        abbreviateGridNumbers();
    }

    // Re-initialize after HTMX swaps
    document.body.addEventListener('htmx:afterSwap', function(evt) {
        if (evt.detail.target.id === 'comparison-table') {
            abbreviateGridNumbers();
            initMobilePackageNav();
        }
    });

    // Mobile package navigation for comparison grid
    function initMobilePackageNav() {
        const cardsContainer = document.querySelector('.mobile-pkg-cards');
        const swipeArea = document.querySelector('.mobile-pkg-swipe-area');

        if (!cardsContainer || !swipeArea) return;

        // Get fresh references to buttons and dots
        function getButtons() {
            return document.querySelectorAll('.mobile-pkg-btn');
        }
        function getDots() {
            return document.querySelectorAll('.mobile-pkg-dot');
        }

        // Store current index on the container element so it persists
        if (!swipeArea.dataset.currentIndex) {
            swipeArea.dataset.currentIndex = '0';
        }

        function getCurrentIndex() {
            return parseInt(swipeArea.dataset.currentIndex, 10) || 0;
        }

        function setCurrentIndex(index) {
            swipeArea.dataset.currentIndex = String(index);
        }

        function switchToPackage(index) {
            const buttons = getButtons();
            const dots = getDots();

            // Clamp index to valid range
            index = Math.max(0, Math.min(index, buttons.length - 1));
            setCurrentIndex(index);

            // Update cards position
            cardsContainer.style.transform = `translateX(-${index * 100}%)`;

            // Update buttons
            buttons.forEach((btn, i) => {
                if (i === index) {
                    btn.classList.add('bg-primary', 'text-primary-foreground', 'border-primary');
                    btn.classList.remove('bg-card', 'text-foreground', 'border-border', 'hover:border-primary');
                } else {
                    btn.classList.remove('bg-primary', 'text-primary-foreground', 'border-primary');
                    btn.classList.add('bg-card', 'text-foreground', 'border-border', 'hover:border-primary');
                }
            });

            // Update dots
            dots.forEach((dot, i) => {
                if (i === index) {
                    dot.classList.add('bg-primary', 'w-4');
                    dot.classList.remove('bg-muted-foreground/30');
                } else {
                    dot.classList.remove('bg-primary', 'w-4');
                    dot.classList.add('bg-muted-foreground/30');
                }
            });

            // Scroll the active button into view
            buttons[index]?.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
        }

        // Use event delegation for buttons and dots
        document.addEventListener('click', (e) => {
            const btn = e.target.closest('.mobile-pkg-btn');
            const dot = e.target.closest('.mobile-pkg-dot');

            if (btn) {
                e.preventDefault();
                const index = parseInt(btn.dataset.pkgIndex, 10);
                switchToPackage(index);
            } else if (dot) {
                e.preventDefault();
                const index = parseInt(dot.dataset.pkgIndex, 10);
                switchToPackage(index);
            }
        });

        // Swipe support - attach to the swipe area wrapper
        let touchStartX = 0;
        let touchStartY = 0;
        let isDragging = false;
        let swipeDirection = null; // 'horizontal', 'vertical', or null

        function handleTouchStart(e) {
            touchStartX = e.touches[0].clientX;
            touchStartY = e.touches[0].clientY;
            isDragging = true;
            swipeDirection = null;
        }

        function handleTouchMove(e) {
            if (!isDragging) return;

            const touchCurrentX = e.touches[0].clientX;
            const touchCurrentY = e.touches[0].clientY;
            const diffX = touchCurrentX - touchStartX;
            const diffY = touchCurrentY - touchStartY;

            // Determine swipe direction once we've moved enough
            if (swipeDirection === null && (Math.abs(diffX) > 10 || Math.abs(diffY) > 10)) {
                swipeDirection = Math.abs(diffX) > Math.abs(diffY) ? 'horizontal' : 'vertical';
            }

            // If horizontal swipe, prevent default to stop page scroll
            if (swipeDirection === 'horizontal') {
                e.preventDefault();
            }
        }

        function handleTouchEnd(e) {
            if (!isDragging) return;

            const buttons = getButtons();
            const touchEndX = e.changedTouches[0].clientX;
            const diff = touchStartX - touchEndX;
            const threshold = 50;
            const currentIndex = getCurrentIndex();

            if (swipeDirection === 'horizontal' && Math.abs(diff) > threshold) {
                if (diff > 0 && currentIndex < buttons.length - 1) {
                    // Swipe left - go to next
                    switchToPackage(currentIndex + 1);
                } else if (diff < 0 && currentIndex > 0) {
                    // Swipe right - go to previous
                    switchToPackage(currentIndex - 1);
                }
            }

            isDragging = false;
            swipeDirection = null;
        }

        // Only add listeners once - check for flag
        if (!swipeArea.dataset.swipeInit) {
            swipeArea.dataset.swipeInit = 'true';
            swipeArea.addEventListener('touchstart', handleTouchStart, { passive: true });
            swipeArea.addEventListener('touchmove', handleTouchMove, { passive: false });
            swipeArea.addEventListener('touchend', handleTouchEnd, { passive: true });
        }
    }

    // Initialize mobile nav if present
    initMobilePackageNav();

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
            mobileMenuBtn.querySelector("i").className = isOpen ? "ph-bold ph-x text-xl" : "ph-bold ph-list text-xl";
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
            })
        );
    });

    // ============================================
    // Search Suggestions
    // ============================================

    // Click handler
    document.addEventListener("click", (e) => {
        const item = e.target.closest("a.suggestion-item");
        if (item?.href) {
            window.location.href = item.href;
        }
    });

    // Setup keyboard navigation and dropdown visibility for each search input
    const setupSuggestionNav = (input, dropdown) => {
        if (!input || !dropdown) return;

        let blurTimeout = null;

        const open = () => { dropdown.dataset.open = "true"; };
        const close = () => { dropdown.dataset.open = "false"; };

        // Keyboard navigation
        input.addEventListener("keydown", (e) => {
            const items = [...dropdown.querySelectorAll(".suggestion-item")];
            if (!items.length) return;

            const current = items.findIndex(el => el.classList.contains("selected"));

            if (e.key === "ArrowDown") {
                e.preventDefault();
                if (current < items.length - 1) {
                    const next = current + 1;
                    items.forEach((el, i) => el.classList.toggle("selected", i === next));
                    items[next]?.scrollIntoView({ block: "nearest" });
                } else {
                    // At the end - scroll load-more into view to trigger pagination
                    const loadMore = dropdown.querySelector(".suggestions-load-more");
                    if (loadMore) {
                        loadMore.scrollIntoView({ block: "nearest" });
                    } else {
                        // Wrap to first item
                        items.forEach((el, i) => el.classList.toggle("selected", i === 0));
                        items[0]?.scrollIntoView({ block: "nearest" });
                    }
                }
            } else if (e.key === "ArrowUp") {
                e.preventDefault();
                const prev = current > 0 ? current - 1 : items.length - 1;
                items.forEach((el, i) => el.classList.toggle("selected", i === prev));
                items[prev]?.scrollIntoView({ block: "nearest" });
            } else if (e.key === "Enter" && current >= 0 && items[current]?.href) {
                e.preventDefault();
                window.location.href = items[current].href;
            } else if (e.key === "Escape") {
                close();
                input.blur();
            }
        });

        // Show dropdown when input has value and is focused
        input.addEventListener("focus", () => { if (input.value.trim()) open(); });
        input.addEventListener("input", () => { input.value.trim() ? open() : close(); });

        // Delay close on blur to allow clicks on dropdown items to complete
        input.addEventListener("blur", () => {
            blurTimeout = setTimeout(close, 200);
        });

        // Cancel blur-close if user is interacting with dropdown
        dropdown.addEventListener("mousedown", () => clearTimeout(blurTimeout));
        dropdown.addEventListener("touchstart", () => clearTimeout(blurTimeout), { passive: true });
    };

    // Initialize for all search inputs
    [
        ["search-input", "suggestions-dropdown"],
        ["navbar-search-input", "navbar-suggestions-dropdown"],
        ["mobile-navbar-search-input", "mobile-navbar-suggestions-dropdown"],
        ["modal-search-input", "modal-suggestions-dropdown"]
    ].forEach(([inputId, dropdownId]) => {
        setupSuggestionNav(document.getElementById(inputId), document.getElementById(dropdownId));
    });

    // Open dropdown when HTMX loads results
    document.body.addEventListener("htmx:afterSwap", (e) => {
        const dropdown = e.target;
        if (dropdown?.id?.includes("suggestions-dropdown") && dropdown.querySelector(".suggestion-item")) {
            dropdown.dataset.open = "true";
        }
    });

    // ============================================
    // Navbar Search Modal (Command Palette Style)
    // ============================================
    const searchModal = document.getElementById("search-modal");
    const searchModalPanel = document.getElementById("search-modal-panel");
    const searchModalBackdrop = searchModal?.querySelector("[data-search-modal-backdrop]");
    let searchModalLastActive = null;

    const isSearchModalOpen = () => searchModal && searchModal.dataset.open === "true";

    const openSearchModal = () => {
        if (!searchModal || !searchModalPanel) return;
        if (isSearchModalOpen()) return;

        searchModalLastActive = document.activeElement;
        searchModal.dataset.open = "true";
        searchModal.setAttribute("aria-hidden", "false");

        searchModal.classList.remove("hidden");
        document.body.classList.add("overflow-hidden");

        // Kick transitions
        requestAnimationFrame(() => {
            if (searchModalBackdrop) {
                searchModalBackdrop.classList.remove("opacity-0");
            }
            searchModalPanel.classList.remove("opacity-0", "scale-95");
        });

        // Ensure HTMX has processed the modal's hx-* attributes
        if (window.htmx && typeof window.htmx.process === "function") {
            window.htmx.process(searchModal);
        }

        const input = document.getElementById("modal-search-input");
        if (input) {
            // Allow the DOM to paint before focusing
            setTimeout(() => input.focus(), 0);
        }
    };

    const closeSearchModal = () => {
        if (!searchModal || !searchModalPanel) return;
        if (!isSearchModalOpen()) return;

        searchModal.dataset.open = "false";
        searchModal.setAttribute("aria-hidden", "true");

        if (searchModalBackdrop) {
            searchModalBackdrop.classList.add("opacity-0");
        }
        searchModalPanel.classList.add("opacity-0", "scale-95");

        // Let transition finish before hiding
        setTimeout(() => {
            searchModal.classList.add("hidden");
            document.body.classList.remove("overflow-hidden");

            const previous = searchModalLastActive;
            searchModalLastActive = null;
            if (previous && typeof previous.focus === "function") {
                previous.focus();
            }
        }, 160);
    };

    if (searchModal) {
        document.querySelectorAll("[data-open-search-modal]").forEach((btn) => {
            btn.addEventListener("click", (e) => {
                e.preventDefault();
                openSearchModal();
            });
        });

        // Click outside the dialog closes
        searchModal.addEventListener("pointerdown", (e) => {
            if (!isSearchModalOpen()) return;
            if (!searchModalPanel) return;

            const clickedInsidePanel = searchModalPanel.contains(e.target);
            if (!clickedInsidePanel) {
                e.preventDefault();
                closeSearchModal();
            }
        });

        // Basic focus trap inside dialog
        searchModal.addEventListener("keydown", (e) => {
            if (!isSearchModalOpen()) return;
            if (e.key === "Escape") {
                e.preventDefault();
                closeSearchModal();
                return;
            }
            if (e.key !== "Tab") return;

            const focusables = searchModalPanel.querySelectorAll(
                'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])'
            );
            if (!focusables.length) return;

            const first = focusables[0];
            const last = focusables[focusables.length - 1];
            const active = document.activeElement;

            if (e.shiftKey && active === first) {
                e.preventDefault();
                last.focus();
            } else if (!e.shiftKey && active === last) {
                e.preventDefault();
                first.focus();
            }
        });
    }

    // ============================================
    // Search Placeholder Animation
    // ============================================
    const animatePlaceholder = (input, texts, options = {}) => {
        if (!input) return;

        const { pauseOnFocus = true } = options;

        let textIndex = 0;
        let charIndex = 0;
        let isDeleting = false;
        let typeSpeed = 100;

        const type = () => {
            // Stop if input is focused
            if (pauseOnFocus && document.activeElement === input) {
                setTimeout(type, 1000);
                return;
            }

            const currentText = texts[textIndex];

            if (isDeleting) {
                input.setAttribute("placeholder", currentText.substring(0, charIndex - 1));
                charIndex--;
                typeSpeed = 50;
            } else {
                input.setAttribute("placeholder", currentText.substring(0, charIndex + 1));
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

    // Initialize placeholder animation for modal search
    const modalSearchInput = document.getElementById("modal-search-input");
    if (modalSearchInput) {
        animatePlaceholder(modalSearchInput, [
            "Search Django packages...",
            'Try "authentication"',
            'Try "cms"',
            'Try "api"',
            'Try "rest"',
        ], { pauseOnFocus: false });
    }

    // Initialize placeholder animation for navbar search
    const navbarSearchInput = document.getElementById("navbar-search-input");
    if (navbarSearchInput) {
        animatePlaceholder(navbarSearchInput, ["Search packages...", 'Try "auth"', 'Try "rest"', 'Try "admin"']);
    }

    // Initialize placeholder animation for navbar search - mobile
    const mobileNavbarSearchInput = document.getElementById("mobile-navbar-search-input");
    if (mobileNavbarSearchInput) {
        animatePlaceholder(mobileNavbarSearchInput, ["Search packages...", 'Try "auth"', 'Try "rest"', 'Try "admin"']);
    }

    // ============================================
    // Global Keyboard Shortcuts
    // ============================================
    document.addEventListener("keydown", (e) => {
        // CMD+/ or CTRL+/ to focus search
        if ((e.metaKey || e.ctrlKey) && e.key === "/") {
            e.preventDefault();
            if (searchModal) {
                openSearchModal();
                return;
            }
            const searchInput =
                document.getElementById("search-input") || document.getElementById("navbar-search-input");
            if (searchInput) searchInput.focus();
        }

        // Just / to focus search (if not already in input)
        if (e.key === "/" && !["INPUT", "TEXTAREA"].includes(document.activeElement.tagName)) {
            e.preventDefault();
            if (searchModal) {
                openSearchModal();
                return;
            }
            const searchInput =
                document.getElementById("search-input") || document.getElementById("navbar-search-input");
            if (searchInput) searchInput.focus();
        }

        // Escape to unfocus input
        if (e.key === "Escape" && searchModal && isSearchModalOpen()) {
            e.preventDefault();
            closeSearchModal();
            return;
        }
        if (e.key === "Escape" && ["INPUT", "TEXTAREA"].includes(document.activeElement.tagName)) {
            document.activeElement.blur();
        }
    });

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

    // ============================================
    // Commit Graph Logic
    // ============================================
    const svg = document.getElementById("commit-svg");
    if (svg) {
        const commitDataStr = svg.dataset.commits;
        if (commitDataStr) {
            const commitData = commitDataStr.split(",").map(Number);
            const pathLine = document.getElementById("commit-line");
            const pathArea = document.getElementById("commit-area");

            if (pathLine && pathArea && commitData.length > 0) {
                const width = 800;
                const height = 90;
                const maxCommits = Math.max(...commitData, 1); // Avoid division by zero
                const stepX = width / (commitData.length - 1);

                let d = `M 0 ${height - (commitData[0] / maxCommits) * height}`;

                commitData.forEach((val, index) => {
                    const x = index * stepX;
                    const y = height - (val / maxCommits) * height;
                    d += ` L ${x} ${y}`;
                });

                pathLine.setAttribute("d", d);
                pathArea.setAttribute("d", `${d} L ${width} ${height} L 0 ${height} Z`);
            }
        }
    }

    // ============================================
    // Add Grid Package Search Dropdown
    // ============================================
    const gridSearchContainer = document.getElementById("search-container");
    const gridSearchTarget = document.getElementById("target");

    if (gridSearchContainer && gridSearchTarget) {
        document.addEventListener("click", (e) => {
            if (!gridSearchContainer.contains(e.target)) {
                gridSearchTarget.innerHTML = "";
            }
        });

        gridSearchContainer.addEventListener("focusout", (e) => {
            if (e.relatedTarget && !gridSearchContainer.contains(e.relatedTarget)) {
                gridSearchTarget.innerHTML = "";
            }
        });
    }
});
