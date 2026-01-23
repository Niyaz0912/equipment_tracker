/* static/js/base.js */
/* ОСНОВНЫЕ СКРИПТЫ ПРОЕКТА Equipment Tracker */

document.addEventListener('DOMContentLoaded', function() {
    // Авто-сабмит форм при изменении select
    document.querySelectorAll('select[onchange*="submit"]').forEach(select => {
        select.onchange = function() {
            this.form.submit();
        };
    });
    
    // Подтверждение удаления
    document.querySelectorAll('a[href*="delete"]').forEach(link => {
        link.addEventListener('click', function(e) {
            if (!confirm('Вы уверены, что хотите удалить эту запись?')) {
                e.preventDefault();
            }
        });
    });
    
    // Показ/скрытие дополнительных полей
    document.querySelectorAll('.collapse-toggle').forEach(button => {
        button.addEventListener('click', function() {
            const target = document.querySelector(this.dataset.target);
            if (target) {
                target.classList.toggle('show');
            }
        });
    });
});