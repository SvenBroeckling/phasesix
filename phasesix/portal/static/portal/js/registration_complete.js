const form = document.querySelector("[data-registration-resend]");

if (form) {
    const button = form.querySelector("[data-registration-resend-button]");
    const status = form.querySelector("[data-registration-resend-status]");
    const countdownTemplate = form.dataset.countdownTemplate;
    const sentMessage = form.dataset.sentMessage;
    let remainingSeconds = Number(status.dataset.remainingSeconds || 0);
    let timer;

    const updateCountdown = () => {
        button.disabled = remainingSeconds > 0;
        status.textContent = remainingSeconds
            ? countdownTemplate.replace("%(seconds)s", remainingSeconds)
            : "";
    };

    const startCountdown = (seconds) => {
        remainingSeconds = seconds;
        clearInterval(timer);
        updateCountdown();
        timer = window.setInterval(() => {
            remainingSeconds = Math.max(0, remainingSeconds - 1);
            updateCountdown();
            if (!remainingSeconds) {
                clearInterval(timer);
            }
        }, 1000);
    };

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        button.disabled = true;

        const response = await fetch(form.action, {
            method: "POST",
            headers: {
                "X-CSRFToken": document.body.dataset.csrfToken,
                "X-Requested-With": "XMLHttpRequest",
            },
        });
        const data = await response.json();

        if (response.ok) {
            status.textContent = sentMessage;
        }
        startCountdown(data.remaining_seconds);
    });

    startCountdown(remainingSeconds);
}
