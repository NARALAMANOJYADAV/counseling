(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', function () {
        // Function to close all other fieldsets
        function closeOthers(currentFieldset) {
            const fieldsets = document.querySelectorAll('fieldset.collapse');
            fieldsets.forEach(fieldset => {
                if (fieldset !== currentFieldset && !fieldset.classList.contains('collapsed')) {
                    const toggle = fieldset.querySelector('.collapse-toggle');
                    if (toggle) {
                        // Let Django's own collapse logic handle it
                        toggle.click();
                    }
                }
            });
        }

        // Listen for clicks on the collapse/expand headers
        document.addEventListener('click', function (e) {
            const toggle = e.target.closest('.collapse-toggle');
            if (toggle) {
                const fieldset = toggle.closest('fieldset.collapse');
                // If it's currently collapsed, clicking it will open it
                if (fieldset && fieldset.classList.contains('collapsed')) {
                    // Close all other open fieldsets first
                    closeOthers(fieldset);
                }
            }

            // Also handle clicks on the H2 title itself
            const header = e.target.closest('fieldset.collapse h2');
            if (header) {
                const fieldset = header.closest('fieldset.collapse');
                if (fieldset && fieldset.classList.contains('collapsed')) {
                    closeOthers(fieldset);
                }
            }
        });
    });
})();
