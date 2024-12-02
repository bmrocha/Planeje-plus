document.addEventListener('DOMContentLoaded', () => {
    const themeToggle = document.getElementById('themeToggle');
    const themeIcon = themeToggle.querySelector('i');
    const themeText = themeToggle.querySelector('span');
    
    function toggleTheme() {
        const html = document.documentElement;
        const currentTheme = html.getAttribute('data-bs-theme');
        
        if (currentTheme === 'dark') {
            html.setAttribute('data-bs-theme', 'light');
            themeIcon.classList.remove('fa-sun');
            themeIcon.classList.add('fa-moon');
            themeText.textContent = 'Tema Escuro';
            localStorage.setItem('theme', 'light');
        } else {
            html.setAttribute('data-bs-theme', 'dark');
            themeIcon.classList.remove('fa-moon');
            themeIcon.classList.add('fa-sun');
            themeText.textContent = 'Tema Claro';
            localStorage.setItem('theme', 'dark');
        }
    }

    // Verificar tema salvo
    const savedTheme = localStorage.getItem('theme') || 'light';
    const html = document.documentElement;
    
    // Aplicar tema salvo
    html.setAttribute('data-bs-theme', savedTheme);
    
    // Atualizar ícone
    if (savedTheme === 'dark') {
        themeIcon.classList.remove('fa-moon');
        themeIcon.classList.add('fa-sun');
        themeText.textContent = 'Tema Claro';
    } else {
        themeIcon.classList.remove('fa-sun');
        themeIcon.classList.add('fa-moon');
        themeText.textContent = 'Tema Escuro';
    }

    // Alternar tema
    themeToggle.addEventListener('click', toggleTheme);
});
