        function showForm(formId) {
            const forms = document.querySelectorAll('.auth-form');
            forms.forEach(form => form.classList.remove('active'));

            const targetForm = document.getElementById(formId);
            if (targetForm) {
                targetForm.classList.add('active');
            }
        }

        function showNotify(type, title, message, duration = 1500) {
            const modal = document.getElementById('notifyModal');
            const icon = document.getElementById('modalIcon');
            const titleEl = document.getElementById('modalTitle');
            const messageEl = document.getElementById('modalMessage');
            const loader = document.getElementById('loaderBar');

            // Reset loader
            loader.style.transition = 'none';
            loader.style.width = '0%';

            // Set content
            titleEl.innerText = title;
            messageEl.innerText = message;

            if (type === 'success') {
                icon.className = 'modal-icon icon-success';
                icon.innerHTML = '<i class="fas fa-check"></i>';
                loader.style.background = 'var(--secondary-color)';
            } else {
                icon.className = 'modal-icon icon-error';
                icon.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
                loader.style.background = '#ef4444';
            }

            modal.classList.add('active');

            // Start loader
            setTimeout(() => {
                loader.style.transition = `width ${duration}ms linear`;
                loader.style.width = '100%';
            }, 50);

            return new Promise(resolve => {
                setTimeout(() => {
                    modal.classList.remove('active');
                    resolve();
                }, duration + 300);
            });
        }

        // Handle Login Submission
        document.querySelector('#login-form form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = e.target.querySelector('input[type="text"]').value;
            const password = e.target.querySelector('input[type="password"]').value;

            try {
                const response = await fetch('/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });
                const result = await response.json();

                if (result.success) {
                    await showNotify('success', 'Đăng nhập thành công', 'Đang chuyển hướng đến trang chủ...');
                    window.location.href = result.redirect;
                } else {
                    showNotify('error', 'Đăng nhập thất bại', result.message);
                }
            } catch (error) {
                console.error('Error:', error);
                showNotify('error', 'Lỗi hệ thống', 'Có lỗi xảy ra, vui lòng thử lại sau.');
            }
        });

        // Handle Register Submission
        document.querySelector('#register-form form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const fullname = e.target.querySelectorAll('input')[0].value;
            const email = e.target.querySelectorAll('input')[1].value;
            const password = e.target.querySelectorAll('input')[2].value;
            const confirm_password = e.target.querySelectorAll('input')[3].value;

            try {
                const response = await fetch('/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ fullname, email, password, confirm_password })
                });
                const result = await response.json();

                if (result.success) {
                    await showNotify('success', 'Đăng ký thành công', result.message, 2000);
                    showForm('login-form');
                } else {
                    showNotify('error', 'Đăng ký thất bại', result.message);
                }
            } catch (error) {
                console.error('Error:', error);
                showNotify('error', 'Lỗi hệ thống', 'Có lỗi xảy ra, vui lòng thử lại sau.');
            }
        });
