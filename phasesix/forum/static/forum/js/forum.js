$(function () {
    let textArea = $("[data-app='forum'] #id_text");
    let url = $("[data-app='forum'] .forum-form").data("image-upload-url");

    function uploadImageFile(file) {
        const formData = new FormData();
        formData.append("image", file);

        try {
            $.ajax({
                url: url,
                type: "POST",
                data: formData,
                contentType: false,
                processData: false,
                success: function (data) {
                    textArea.val(textArea.val() + "\n\n" + data.markdown_link);
                },
            });
        } catch (error) {
            console.error("Error uploading image:", error);
        }
    }

    $("[data-app='forum'] #forumUploadFileInput").on("change", function (e) {
        const file = e.target.files[0];
        uploadImageFile(file);
    });

    $("[data-app='forum'] #forum-upload-image").on("click", function (e) {
        $("[data-app='forum'] #forumUploadFileInput").click();
    });

    textArea.on("paste", function (e) {
        const clipboardItems = event.clipboardData.items;

        for (let item of clipboardItems) {
            if (item.type.startsWith("image/")) {
                const imageFile = item.getAsFile();
                uploadImageFile(imageFile);
                break;
            }
        }
    });

    $("[data-app='forum'] #new-thread-collapse").on(
        "shown.bs.collapse",
        function (e) {
            let elem = document.getElementById("new-thread-collapse");
            elem.scrollIntoView(true);
            elem.focus();
        },
    );

    $("[data-app='forum'] #switch-subscribe").on("change", function (e) {
        $.post(
            $(this).data("url"),
            {
                value: $(this).prop("checked"),
                object: $(this).data("object"),
            },
            function (data) {},
        );
    });

    $("[data-app='forum'] .quote-button").on("click", function (e) {
        let elem = document.getElementById("id_text");
        $.get($(this).data("raw-post-url"), function (data) {
            elem.value = data.text;
            elem.focus();
        });
    });
});
