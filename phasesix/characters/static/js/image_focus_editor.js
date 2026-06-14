document.addEventListener("DOMContentLoaded", () => {
    const toggle = document.querySelector(".image-focus-mode-toggle");
    const modalElement = document.getElementById("image-focus-modal");
    if (!toggle || !modalElement) return;

    const modal = new bootstrap.Modal(modalElement);
    const editor = modalElement.querySelector(".image-focus-editor");
    const image = editor.querySelector("img");
    const marker = editor.querySelector(".image-focus-marker");
    const save = modalElement.querySelector(".image-focus-save");
    let activeTarget = null;
    let x = 50;
    let y = 50;

    const positionMarker = () => {
        marker.style.left = `${image.offsetLeft + (image.clientWidth * x) / 100}px`;
        marker.style.top = `${image.offsetTop + (image.clientHeight * y) / 100}px`;
    };

    toggle.addEventListener("click", () => {
        const active = document.body.classList.toggle("image-focus-mode");
        toggle.setAttribute("aria-pressed", active ? "true" : "false");
        toggle.classList.toggle("btn-warning", active);
        toggle.classList.toggle("btn-primary", !active);
    });

    document.addEventListener("click", (event) => {
        if (!document.body.classList.contains("image-focus-mode")) return;
        const target = event.target.closest('[data-focal-editor="true"]');
        if (!target) return;
        event.preventDefault();
        event.stopPropagation();
        activeTarget = target;
        x = Number(target.dataset.focalX);
        y = Number(target.dataset.focalY);
        image.src = target.dataset.focalSrc;
        positionMarker();
        modal.show();
    }, true);

    image.addEventListener("load", positionMarker);

    editor.addEventListener("click", (event) => {
        const rect = image.getBoundingClientRect();
        if (
            event.clientX < rect.left ||
            event.clientX > rect.right ||
            event.clientY < rect.top ||
            event.clientY > rect.bottom
        ) return;
        x = Math.round(((event.clientX - rect.left) / rect.width) * 100);
        y = Math.round(((event.clientY - rect.top) / rect.height) * 100);
        positionMarker();
    });

    editor.addEventListener("keydown", (event) => {
        const movement = {
            ArrowLeft: [-1, 0],
            ArrowRight: [1, 0],
            ArrowUp: [0, -1],
            ArrowDown: [0, 1],
        }[event.key];
        if (!movement) return;
        event.preventDefault();
        x = Math.max(0, Math.min(100, x + movement[0]));
        y = Math.max(0, Math.min(100, y + movement[1]));
        positionMarker();
    });

    save.addEventListener("click", async () => {
        if (!activeTarget) return;
        const body = new URLSearchParams({
            app_label: activeTarget.dataset.focalApp,
            model: activeTarget.dataset.focalModel,
            pk: activeTarget.dataset.focalPk,
            field_name: activeTarget.dataset.focalField,
            x,
            y,
        });
        const response = await fetch(document.body.dataset.focalUpdateUrl, {
            method: "POST",
            headers: {
                "X-CSRFToken": document.body.dataset.csrfToken,
                "Content-Type": "application/x-www-form-urlencoded",
            },
            body,
        });
        if (response.ok) window.location.reload();
    });
});
