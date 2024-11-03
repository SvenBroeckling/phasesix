$(function () {
    let body = $('body')

    body.on('click', '.profile-image-upload-button', function () {
        $('#id_profile_image_upload').click()
    })

    body.on('change', '#id_profile_image_upload', function () {
        $('#profile-image-form').submit()
    })

})
