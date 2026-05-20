/**
 * Shared custom dropdown — styled list; syncs to hidden native select
 */
const CustomSelect = (function () {
    const instances = new Map();

    function getWrapper(nativeSelect) {
        return nativeSelect?.closest('.custom-select');
    }

    function syncDisplay(nativeSelect, value) {
        const wrapper = getWrapper(nativeSelect);
        if (!wrapper) return;

        const display = wrapper.querySelector('.custom-select-label');
        const options = wrapper.querySelectorAll('.custom-select-option');

        options.forEach((opt) => {
            const selected = opt.dataset.value === value;
            opt.classList.toggle('is-selected', selected);
            opt.setAttribute('aria-selected', selected ? 'true' : 'false');
            if (selected && display) {
                display.textContent =
                    opt.querySelector('.option-title')?.textContent || value;
            }
        });
    }

    function setValue(nativeSelect, value) {
        if (!nativeSelect) return;
        nativeSelect.value = value;
        syncDisplay(nativeSelect, value);
    }

    function init(nativeSelect) {
        if (!nativeSelect || instances.has(nativeSelect)) return;

        const wrapper = getWrapper(nativeSelect);
        const trigger = wrapper?.querySelector('.custom-select-trigger');
        const menu = wrapper?.querySelector('.custom-select-menu');

        if (!wrapper || !trigger || !menu) return;

        function openMenu() {
            wrapper.classList.add('is-open');
            trigger.setAttribute('aria-expanded', 'true');
            menu.hidden = false;
        }

        function closeMenu() {
            wrapper.classList.remove('is-open');
            trigger.setAttribute('aria-expanded', 'false');
            menu.hidden = true;
        }

        function selectOption(optionEl) {
            const value = optionEl.dataset.value;
            setValue(nativeSelect, value);
            closeMenu();
            trigger.focus();
            nativeSelect.dispatchEvent(new Event('change', { bubbles: true }));
        }

        trigger.addEventListener('click', () => {
            if (wrapper.classList.contains('is-open')) {
                closeMenu();
            } else {
                openMenu();
            }
        });

        menu.querySelectorAll('.custom-select-option').forEach((option) => {
            option.addEventListener('click', () => selectOption(option));
            option.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    selectOption(option);
                }
            });
        });

        const onDocClick = (e) => {
            if (!wrapper.contains(e.target)) closeMenu();
        };
        const onDocKey = (e) => {
            if (e.key === 'Escape') closeMenu();
        };

        document.addEventListener('click', onDocClick);
        document.addEventListener('keydown', onDocKey);

        instances.set(nativeSelect, { closeMenu, onDocClick, onDocKey });
        syncDisplay(nativeSelect, nativeSelect.value);
    }

    function initAll(selector = 'select.custom-select-native') {
        document.querySelectorAll(selector).forEach(init);
    }

    return { init, initAll, setValue };
})();

if (typeof window !== 'undefined') {
    window.CustomSelect = CustomSelect;
}
