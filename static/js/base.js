// static/js/base.js - ИСПРАВЛЕННАЯ ВЕРСИЯ

document.addEventListener('DOMContentLoaded', function() {
    // Автоматическое определение активной вкладки
    const currentPath = window.location.pathname;
    
    console.log('Текущий путь:', currentPath); // Для отладки
    
    // Убираем активность со всех вкладок
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    
    // Находим и активируем подходящую вкладку
    const navLinks = document.querySelectorAll('.nav-link');
    let activeLink = null;
    
    navLinks.forEach(link => {
        let linkPath = link.getAttribute('href');
        
        // Дебаг: выводим информацию о каждой ссылке
        console.log('Ссылка:', {
            href: linkPath,
            text: link.textContent.trim()
        });
        
        // Нормализуем пути
        // Добавляем / в начало если нет
        if (!linkPath.startsWith('/')) {
            linkPath = '/' + linkPath;
        }
        
        // Убираем trailing slash для сравнения
        const normalizedLinkPath = linkPath.replace(/\/$/, '');
        const normalizedCurrentPath = currentPath.replace(/\/$/, '');
        
        // Проверяем точное совпадение
        if (normalizedLinkPath === normalizedCurrentPath) {
            activeLink = link;
            console.log('Точное совпадение найдено:', linkPath);
        } 
        // Проверяем вложенные страницы (например, /equipments/1/)
        else if (normalizedCurrentPath.startsWith(normalizedLinkPath + '/')) {
            activeLink = link;
            console.log('Вложенное совпадение:', linkPath);
        }
    });
    
    // Если нашли подходящую вкладку, активируем её
    if (activeLink) {
        activeLink.classList.add('active');
        console.log('Активирована вкладка:', activeLink.textContent.trim());
    } else {
        console.log('Активная вкладка не найдена');
    }
    
    // Специальная проверка для network модуля
    if (currentPath.includes('/network/')) {
        document.querySelectorAll('.nav-link').forEach(link => {
            const href = link.getAttribute('href');
            if (href && href.includes('network')) {
                link.classList.add('active');
                console.log('Network активирована по ключевому слову');
            }
        });
    }
    
    // Добавляем обработчики для плавного перехода
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', function(e) {
            // Снимаем активность со всех
            document.querySelectorAll('.nav-link').forEach(l => {
                l.classList.remove('active');
            });
            // Активируем текущую
            this.classList.add('active');
        });
    });
    
    // Добавляем класс для текущей страницы в body
    const pathSegments = currentPath.split('/').filter(segment => segment);
    if (pathSegments.length > 0) {
        document.body.classList.add('page-' + pathSegments[0]);
    }
});