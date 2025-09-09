function fallbackCopyTextToClipboard(text) {
    let textArea = document.createElement("textarea");
    textArea.value = text;

    // Avoid scrolling to bottom
    textArea.style.top = "0";
    textArea.style.left = "0";
    textArea.style.position = "fixed";

    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();

    try {
        document.execCommand("copy");
    } catch (err) {
        console.error("Fallback: Oops, unable to copy", err);
    }

    document.body.removeChild(textArea);
}

function copyTextToClipboard(text) {
    if (!navigator.clipboard) {
        fallbackCopyTextToClipboard(text);
        return;
    }
    navigator.clipboard.writeText(text).then(
        function () {},
        function (err) {
            console.error("Async: Could not copy text: ", err);
        },
    );
}

document.addEventListener("DOMContentLoaded", function () {
    document.addEventListener("click", function (e) {
        let clipboardTrigger = e.target.closest("[data-clipboard-value]");
        if (clipboardTrigger) {
            let value = clipboardTrigger.getAttribute("data-clipboard-value");
            copyTextToClipboard(value);
            Toast.setPlacement(TOAST_PLACEMENT.BOTTOM_LEFT);
            Toast.setMaxCount(5);
            Toast.create({
                title: clipboardTrigger.dataset.clipboardTitle || "Copied",
                message:
                    clipboardTrigger.dataset.clipboardMessage ||
                    "Copied to clipboard",
                status: TOAST_STATUS.SUCCESS,
                timeout: 5000,
            });
        }
    });
});
