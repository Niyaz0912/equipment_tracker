// Общие функции для модуля network
document.addEventListener('DOMContentLoaded', function() {
    // Автоматическое обновление прогресс-бара если есть data-width атрибут
    document.querySelectorAll('[data-width]').forEach(function(element) {
        const width = element.getAttribute('data-width');
        if (width) {
            element.style.width = width + '%';
        }
    });
    
    // Подтверждение удаления (если добавим в будущем)
    document.querySelectorAll('.network-confirm-delete').forEach(function(button) {
        button.addEventListener('click', function(e) {
            if (!confirm('Вы уверены, что хотите удалить этот элемент?')) {
                e.preventDefault();
            }
        });
    });
});