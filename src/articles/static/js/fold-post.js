const foldButtons = document.querySelectorAll('.fold-button');

for (const button of foldButtons) {
    button.addEventListener('click', event => {
        const post = event.currentTarget.closest('.one-post');
        const folded = post.classList.toggle('folded');
        button.textContent = folded ? 'Развернуть' : 'Свернуть';
        button.setAttribute('aria-expanded', String(!folded));
        console.log('Изменено отображение статьи:', post);
    });
}
