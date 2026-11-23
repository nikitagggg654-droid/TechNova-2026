"use strict";

// ===== Бургер-меню =====
const burger = document.getElementById("burger");
const mainMenu = document.getElementById("mainMenu");

function setMenu(open) {
    mainMenu.classList.toggle("open", open);
    burger.classList.toggle("open", open);
    burger.setAttribute("aria-expanded", String(open));
    burger.setAttribute("aria-label", open ? "Закрити меню" : "Відкрити меню");
}

if (burger && mainMenu) {
    burger.addEventListener("click", () => setMenu(!mainMenu.classList.contains("open")));
    mainMenu.addEventListener("click", (e) => { if (e.target.closest("a")) setMenu(false); });
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") setMenu(false); });
}

// ===== Модальне вікно підтвердження видалення =====
const modal = document.getElementById("confirmModal");

if (modal) {
    const text = document.getElementById("confirmText");
    const confirmBtn = modal.querySelector("[data-modal-confirm]");
    const cancelBtn = modal.querySelector("[data-modal-cancel]");
    let pendingForm = null;
    let lastFocus = null;

    const openModal = (form) => {
        pendingForm = form;
        lastFocus = document.activeElement;
        text.textContent = `Видалити товар «${form.dataset.name}»? Цю дію не можна скасувати.`;
        modal.hidden = false;
        document.body.classList.add("modal-open");   // блокування скролу
        cancelBtn.focus();
    };

    const closeModal = () => {
        modal.hidden = true;
        document.body.classList.remove("modal-open");
        pendingForm = null;
        if (lastFocus) lastFocus.focus();
    };

    document.querySelectorAll(".delete-form").forEach((form) => {
        form.addEventListener("submit", (e) => {
            e.preventDefault();
            openModal(form);
        });
    });

    confirmBtn.addEventListener("click", () => {
        const form = pendingForm;
        closeModal();
        if (form) form.submit();   // submit() не викликає повторно подію submit
    });

    cancelBtn.addEventListener("click", closeModal);
    modal.addEventListener("click", (e) => { if (e.target === modal) closeModal(); });
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && !modal.hidden) closeModal();
    });
}

// ===== Валідація форми реєстрації =====
const registerForm = document.getElementById("registerForm");

if (registerForm) {
    const password = registerForm.elements.password;
    const confirm = registerForm.elements.confirm;
    const check = () => confirm.setCustomValidity(
        confirm.value && password.value !== confirm.value ? "Паролі не збігаються" : ""
    );
    password.addEventListener("input", check);
    confirm.addEventListener("input", check);
}

// ===== Плавна поява карток при прокрутці =====
const revealItems = document.querySelectorAll(".product-card, .category-card");

if ("IntersectionObserver" in window && revealItems.length) {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.classList.add("is-visible");
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.15 });

    revealItems.forEach((card, index) => {
        card.classList.add("reveal");
        card.style.transitionDelay = (index % 4) * 80 + "ms";   // каскад
        observer.observe(card);
    });
}
