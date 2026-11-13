document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    const signupForm = document.getElementById('signupForm');
    
    const loginBox = document.getElementById('loginBox');
    const signupBox = document.getElementById('signupBox');
    
    const showSignUpBtn = document.getElementById('showSignUp');
    const showLoginBtn = document.getElementById('showLogin');
    
    // Toast Elements
    const toast = document.getElementById('toast');
    const toastMsg = document.getElementById('toast-msg');
    const toastIcon = document.getElementById('toast-icon');

    // Toggle forms
    showSignUpBtn.addEventListener('click', (e) => {
        e.preventDefault();
        loginBox.style.display = 'none';
        signupBox.style.display = 'block';
    });

    showLoginBtn.addEventListener('click', (e) => {
        e.preventDefault();
        signupBox.style.display = 'none';
        loginBox.style.display = 'block';
    });

    // Toggle Password Visibility Helpers
    function attachPasswordToggle(toggleId, inputId) {
        const toggleBtn = document.getElementById(toggleId);
        const input = document.getElementById(inputId);
        if(!toggleBtn || !input) return;
        
        toggleBtn.addEventListener('click', function() {
            const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
            input.setAttribute('type', type);
            if (type === 'text') {
                this.classList.remove('bx-hide');
                this.classList.add('bx-show');
            } else {
                this.classList.remove('bx-show');
                this.classList.add('bx-hide');
            }
        });
    }

    attachPasswordToggle('togglePassword', 'password');
    attachPasswordToggle('toggleSignupPassword', 'signupPassword');

    // Login Handler
    loginForm.addEventListener('submit', function (e) {
        e.preventDefault();
        
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value.trim();
        const submitBtn = this.querySelector('button');

        if (!username || !password) {
            showToast('Please fill in all fields', 'error');
            return;
        }

        submitBtn.innerHTML = "<i class='bx bx-loader-alt bx-spin'></i> Authenticating...";
        submitBtn.disabled = true;

        fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        })
        .then(response => response.json())
        .then(data => {
            submitBtn.innerHTML = "Sign In";
            submitBtn.disabled = false;

            if (data.success) {
                showToast(`Welcome back, ${username}!`, 'success');
                setTimeout(() => { window.location.href = '/chat.html'; }, 1000);
            } else {
                showToast(data.message || 'Invalid credentials. Try again.', 'error');
            }
        })
        .catch(error => {
            submitBtn.innerHTML = "Sign In";
            submitBtn.disabled = false;
            showToast('Server error. Try again.', 'error');
        });
    });

    // Signup Handler
    signupForm.addEventListener('submit', function (e) {
        e.preventDefault();
        
        const username = document.getElementById('signupUsername').value.trim();
        const password = document.getElementById('signupPassword').value.trim();
        const confirmPassword = document.getElementById('signupConfirmPassword').value.trim();
        const submitBtn = this.querySelector('button');

        if (!username || !password || !confirmPassword) {
            showToast('Please fill in all fields', 'error');
            return;
        }

        if (password !== confirmPassword) {
            showToast('Passwords do not match!', 'error');
            return;
        }

        if (password.length < 6) {
            showToast('Password must be at least 6 characters', 'error');
            return;
        }

        submitBtn.innerHTML = "<i class='bx bx-loader-alt bx-spin'></i> Creating account...";
        submitBtn.disabled = true;

        fetch('/api/signup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        })
        .then(response => response.json())
        .then(data => {
            submitBtn.innerHTML = "Create Account";
            submitBtn.disabled = false;

            if (data.success) {
                showToast(`Account created! Please sign in.`, 'success');
                setTimeout(() => {
                    // Switch to login box
                    signupBox.style.display = 'none';
                    loginBox.style.display = 'block';
                    document.getElementById('username').value = username;
                    document.getElementById('password').value = '';
                }, 1500);
            } else {
                showToast(data.message || 'Failed to create account.', 'error');
            }
        })
        .catch(error => {
            submitBtn.innerHTML = "Create Account";
            submitBtn.disabled = false;
            showToast('Server error. Try again.', 'error');
        });
    });

    let toastTimeout;
    
    function showToast(message, type = 'success') {
        clearTimeout(toastTimeout);
        toastMsg.textContent = message;
        toast.className = 'toast'; 
        
        if (type === 'error') {
            toast.classList.add('error');
            toastIcon.className = 'bx bx-error-circle';
        } else {
            toast.classList.add('success');
            toastIcon.className = 'bx bx-check-circle';
        }

        setTimeout(() => { toast.classList.add('show'); }, 10);
        toastTimeout = setTimeout(() => { toast.classList.remove('show'); }, 3000);
    }
    
    // Initial display setup
    signupBox.style.display = 'none';
});