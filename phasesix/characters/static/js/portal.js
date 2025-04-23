$(document).ready(function () {

        function getCookie(name) {
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                let cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    let cookie = jQuery.trim(cookies[i]);
                    // Does this cookie string begin with the name we want?
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }

        let csrftoken = getCookie('csrftoken');

        function csrfSafeMethod(method) {
            // these HTTP methods do not require CSRF protection
            return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
        }

        $.ajaxSetup({
            beforeSend: function (xhr, settings) {
                if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                }
            }
        });

        $('table.table-sortable').tablesorter();

        $(".navigation-link").on("click", function (e) {
            const myModal = bootstrap.Modal.getInstance(document.getElementById('bottom-nav-modal'));
            if (myModal)
                myModal.hide();
        })

        $('.language-link').on('click', function (event) {
            $.post(
                $(this).attr('href'),
                {language: $(this).data('language')},
                function (data) {
                    window.location.reload()
                })
            event.preventDefault()
            return false
        })

        document.querySelectorAll('.toggle-lightbox').forEach((el) => el.addEventListener('click', (e) => {
            e.preventDefault();
            const lightbox = new Lightbox(el, {
                keyboard: true,
                size: 'fullscreen'
            });
            lightbox.show();
        }));

        const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]')
        const popoverList = [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl, {html: true}))
        $('.template').tilt({glare: false, perspective: 1800})
    }
)

function toggleDiceLog() {
    const diceLog = document.getElementById('dice-log');
    if (diceLog) diceLog.classList.toggle('show');
}
