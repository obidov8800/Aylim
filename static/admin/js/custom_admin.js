// static/admin/js/custom_admin.js

(function($) {
    $(document).ready(function() {
        
        // --- Rolga qarab guruh maydonini ko'rsatish/yashirish ---
        const rolSelect = $("#id_rol");
        // Guruh maydonini o'rab turgan qatorni topamiz
        const guruhFieldRow = $(".field-group"); 

        function toggleGuruhField() {
            // Faqat 'Talaba' tanlanganda guruh maydonini ko'rsatamiz
            if (rolSelect.val() === 'TALABA') {
                guruhFieldRow.show();
            } else {
                guruhFieldRow.hide();
            }
        }
        
        // Agar rol tanlash maydoni mavjud bo'lsa...
        if(rolSelect.length) {
            toggleGuruhField(); // Sahifa yuklanganda bir marta tekshirish
            rolSelect.on('change', toggleGuruhField); // Har gal rol o'zgarganda tekshirish
        }

        // --- Yagona parol maydoniga ko'rish tugmasini qo'shish ---
        // Bu faqat "add" sahifasida ishlashi uchun
        const passwordField = $("#id_password");
        if (passwordField.length) {
            const toggleButton = $('<button type="button" style="margin-left: 10px; cursor: pointer;">Ko\'rish</button>');
            passwordField.after(toggleButton);

            toggleButton.on('click', function() {
                const fieldType = passwordField.attr('type');
                if (fieldType === 'password') {
                    passwordField.attr('type', 'text');
                    toggleButton.text('Yashirish');
                } else {
                    passwordField.attr('type', 'password');
                    toggleButton.text('Ko\'rish');
                }
            });
        }
    });
})(django.jQuery);