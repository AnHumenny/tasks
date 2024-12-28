// Функция для обрезки текста с многоточием
function truncateText(selector, maxLength) {
    const elements = document.querySelectorAll(selector);
    elements.forEach(element => {
        const text = element.textContent;
        if (text.length > maxLength) {
            const truncatedText = text.slice(0, maxLength) + '...';
            element.textContent = truncatedText;
        }
    });
}

// Вызываем функцию после загрузки страницы
document.addEventListener('DOMContentLoaded', function() {
    truncateText('.task-describe', 200); // Укажите максимальную длину текста
});

// Функция для обновления контента и обрезки текста
function updateContent(url) {
    fetch(url)
        .then(response => response.text())
        .then(data => {
            // Предположим, что вы обновляете контейнер с задачами
            document.querySelector('.task-container').innerHTML = data;

            // После обновления контента вызываем функцию обрезки текста
            truncateText('.task-describe', 200);
        })
        .catch(error => console.error('Ошибка:', error));
}
