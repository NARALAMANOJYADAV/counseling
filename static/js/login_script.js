// Initialize login/signup toggle
(function () {
    const container = document.querySelector('.container');
    const LoginLink = document.querySelector('.SignInLink');
    const RegisterLink = document.querySelector('.SignUpLink');
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');

    if (RegisterLink && container) {
        RegisterLink.addEventListener('click', (e) => {
            e.preventDefault();
            container.classList.add('active');
        });
    }

    if (LoginLink && container) {
        LoginLink.addEventListener('click', (e) => {
            e.preventDefault();
            container.classList.remove('active');
        });
    }

    // Forms will now submit directly to the Django backend
})();
