document.addEventListener('DOMContentLoaded', function () {
    const body = document.body;

    body.addEventListener('click', function (e) {
        if (e.target.closest('.sidebar-trigger')) {
            const trigger = e.target.closest('.sidebar-trigger');
            const sidebar = document.querySelector('#sidebar-right');
            sidebar.style.width = '330px';

            const firstH4 = sidebar.querySelector('h4');
            if (firstH4) {
                firstH4.textContent = trigger.dataset.sidebarTitle;
            }

            const sidebarContent = sidebar.querySelector('.sidebar-content');
            if (trigger.classList.contains('sidebar-spinner')) {
                sidebarContent.innerHTML = '<div class="w-100 pt-5 d-flex justify-content-center align-content-center"><i class="fas fa-spinner fa-3x fa-spin"></i></div>';
            }

            sidebarContent.dataset.sidebarUrl = trigger.dataset.sidebarUrl;
            fetch(trigger.dataset.sidebarUrl)
                .then(response => response.text())
                .then(html => {
                    sidebarContent.innerHTML = html;
                });

            e.preventDefault();
        }

        if (e.target.closest('.sidebar-close')) {
            document.querySelector('#sidebar-right').style.width = '';
            e.preventDefault();
        }
    });
});
