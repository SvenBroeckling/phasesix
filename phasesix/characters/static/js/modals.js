document.addEventListener('DOMContentLoaded', function () {
    const body = document.querySelector('body');
    const pageModal = document.querySelector('#page-modal');

    body.addEventListener('click', function (e) {
        if (e.target.matches('.modal-trigger')) {
            const modalDialog = document.querySelector('#page-modal .modal-dialog');
            document.querySelector('.modal-header h5').textContent = e.target.dataset.modalTitle;
            pageModal.dataset.url = e.target.dataset.url;
            if (e.target.classList.contains('small-modal')) {
                modalDialog.classList.remove('modal-xl');
            } else {
                modalDialog.classList.add('modal-xl');
            }
            document.querySelector('#sidebar-right').style.width = '';
        }
    });

    pageModal.addEventListener('shown.bs.modal', function (e) {
        fetch(this.dataset.url)
            .then(response => response.text())
            .then(html => {
                document.querySelector('.page-modal-container').innerHTML = html;
            });
    });

    pageModal.addEventListener('hidden.bs.modal', function (e) {
        document.querySelector('.page-modal-container').innerHTML = '';
    });
});
