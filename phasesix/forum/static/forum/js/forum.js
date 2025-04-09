$(function () {
    let textArea = $('#id_text');
    let url = $(".forum-form").data('image-upload-url');

    function uploadImageFile(file) {
        const formData = new FormData();
        formData.append("image", file);

        try {
            $.ajax(
                {
                    url: url,
                    type: 'POST',
                    data: formData,
                    contentType: false,
                    processData: false,
                    success: function (data) {
                        textArea.val(textArea.val() + "\n\n" + data.markdown_link)
                    }
                }
            )
        } catch (error) {
            console.error("Error uploading image:", error);
        }
    }

    $('#forumUploadFileInput').on('change', function (e) {
        const file = e.target.files[0];
        uploadImageFile(file);
    })

    $('#forum-upload-image').on('click', function (e) {
        $('#forumUploadFileInput').click();
    })

    textArea.on('paste', function (e) {
        const clipboardItems = event.clipboardData.items;

        for (let item of clipboardItems) {
            if (item.type.startsWith("image/")) {
                const imageFile = item.getAsFile();
                uploadImageFile(imageFile);
                break;
            }
        }
    })

    $('#new-thread-collapse').on('shown.bs.collapse', function (e) {
        let elem = document.getElementById('new-thread-collapse')
        elem.scrollIntoView(true);
        elem.focus()
    });

    $('#switch-subscribe').on('change', function (e) {
        $.post($(this).data('url'), {
            value: $(this).prop('checked'), object: $(this).data('object')
        }, function (data) {
        })
    })

    $('.quote-button').on('click', function (e) {
        let elem = document.getElementById('id_text')
        $.get($(this).data('raw-post-url'), function (data) {
            elem.value = data.text
            elem.focus()
        })
    })
})

