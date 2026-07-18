// Dropdown Handlers (Synced from Profile/Index)
function toggleUserMenu(event) {
    event.stopPropagation();
    document.getElementById('userDropdown').classList.toggle('active');
    document.getElementById('toolsDropdown').classList.remove('active');
    document.getElementById('miscDropdown').classList.remove('active');
}

function toggleToolsMenu(event) {
    event.stopPropagation();
    document.getElementById('toolsDropdown').classList.toggle('active');
    document.getElementById('userDropdown').classList.remove('active');
    document.getElementById('miscDropdown').classList.remove('active');
}

function toggleMiscMenu(event) {
    event.stopPropagation();
    document.getElementById('miscDropdown').classList.toggle('active');
    document.getElementById('userDropdown').classList.remove('active');
    document.getElementById('toolsDropdown').classList.remove('active');
}

window.onclick = function (event) {
    const userDropdown = document.getElementById('userDropdown');
    const userAvatar = document.getElementById('userAvatar');
    // ... (Other dropdown closes remain same logic implicitly or explicitly)

    if (userDropdown && userDropdown.classList.contains('active') && !userAvatar.contains(event.target)) {
        userDropdown.classList.remove('active');
    }
}

// --- Deposit Page Logic ---
let currentUsername = '';
let activeBankData = null;

async function initDepositPage() {
    await loadUserInfo();
    loadHistory();
    startPolling();
}

async function loadUserInfo() {
    try {
        const [userResp, bankResp] = await Promise.all([
            fetch('/api/user/status?t=' + Date.now()),
            fetch('/api/bank/active')
        ]);
        const userData = await userResp.json();
        const bankData = await bankResp.json();

        
        if (!userData.logged_in) {
            window.location.href = '/login';
            return;
        }

        const user = userData.user;
        currentUsername = user.username;
        document.getElementById('userAvatar').innerText = user.username.substring(0, 2).toUpperCase();

        // Generate random deposit code
        let transferContent = currentUsername; // fallback
        try {
            const genResp = await fetch('/api/deposits/generate', { method: 'POST' });
            const genData = await genResp.json();
            if (genData.success && genData.code) {
                transferContent = genData.code;
            }
        } catch (e) {
            console.error('Error generating code', e);
        }
        
        document.getElementById('transferContent').innerText = transferContent;

        // Load bank info from backend
        if (bankData.success && bankData.bank) {
            activeBankData = bankData.bank;
            const bank = bankData.bank;
            document.getElementById('bankBadge').textContent = bank.bank_name;
            document.getElementById('bankOwner').textContent = bank.account_name;
            document.getElementById('bankNumber').textContent = bank.account_number;

            // Build QR URL
            let qrUrl;
            if (bank.qr_url && bank.qr_url.trim()) {
                // Use admin-configured QR URL, append des= with transfer content
                const base = bank.qr_url.replace(/&?des=[^&]*/g, ''); // remove old des if any
                const sep = base.includes('?') ? '&' : '?';
                qrUrl = base + (base.endsWith('&') || base.endsWith('?') ? '' : '&') + 'des=' + encodeURIComponent(transferContent);
                // Clean up double && or ?&
                qrUrl = qrUrl.replace(/&&/g, '&').replace(/\?&/g, '?');
            } else if (bank.bank_code) {
                // Fallback: build sepay URL from bank_code + account_number
                qrUrl = `https://qr.sepay.vn/img?bank=${encodeURIComponent(bank.bank_code)}&acc=${encodeURIComponent(bank.account_number)}&template=compact&amount=&des=${encodeURIComponent(transferContent)}`;
            } else {
                qrUrl = null;
            }

            const qrImg = document.getElementById('qrImage');
            const qrLoading = document.getElementById('qrLoading');
            if (qrUrl) {
                qrImg.src = qrUrl;
                qrImg.style.display = '';
                qrLoading.style.display = 'none';
            } else {
                qrLoading.textContent = 'Chưa có mã QR';
            }
        } else {
            document.getElementById('bankBadge').textContent = 'Chưa có ngân hàng';
            document.getElementById('bankOwner').textContent = '-';
            document.getElementById('bankNumber').textContent = '-';
            document.getElementById('qrLoading').textContent = 'Admin chưa cấu hình ngân hàng';
        }

    } catch (error) {
        console.error('Init Error:', error);
    }
}

async function loadHistory() {
    try {
        const response = await fetch('/api/deposits?limit=10&t=' + Date.now());
        const data = await response.json();
        const tbody = document.getElementById('historyTableBody');

        if (data.success && data.deposits.length > 0) {
            tbody.innerHTML = data.deposits.map(d => `
                        <tr>
                            <td><span style="font-family: monospace; color: #1877F2;">${d.transaction_id}</span></td>
                            <td>${new Date(d.created_at).toLocaleString('vi-VN')}</td>
                            <td style="font-weight: 700; color: var(--secondary-color);">+${parseFloat(d.amount).toLocaleString('vi-VN')}đ</td>
                            <td>${d.method.toUpperCase()}</td>
                            <td>
                                <span class="badge ${d.status === 'completed' ? 'badge-success' : (d.status === 'pending' ? 'badge-pending' : 'badge-danger')}">
                                    ${d.status === 'completed' ? 'Thành công' : (d.status === 'pending' ? 'Chờ xử lý' : 'Thất bại')}
                                </span>
                            </td>
                        </tr>
                    `).join('');
        } else {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 20px; color: var(--gray-color);">Chưa có giao dịch nào.</td></tr>';
        }
    } catch (error) {
        console.error('History Error:', error);
    }
}

function copyBankNumber() {
    const num = document.getElementById('bankNumber').textContent;
    copyToClipboard(num);
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotify('success', 'Đã sao chép', text);
    });
}

function copyTransferContent() {
    const content = document.getElementById('transferContent').innerText;
    copyToClipboard(content);
}

// Notification Modal
function showNotify(type, title, message) {
    const modal = document.getElementById('notifyModal');
    const icon = document.getElementById('modalIcon');

    document.getElementById('modalTitle').innerText = title;
    document.getElementById('modalMessage').innerText = message;

    if (type === 'success') {
        icon.className = 'modal-icon icon-success';
        icon.innerHTML = '<i class="fas fa-check"></i>';
    } else {
        icon.className = 'modal-icon icon-error';
        icon.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
    }

    modal.classList.add('active');
}

function closeModal() {
    document.getElementById('notifyModal').classList.remove('active');
}

// Polling System
let pollInterval;

function startPolling() {
    // Poll every 10 seconds
    pollInterval = setInterval(checkNewDeposit, 10000);
}

async function checkNewDeposit() {
    const transferContent = document.getElementById('transferContent').innerText;
    if (!transferContent || transferContent.includes('...')) return;

    try {
        const response = await fetch(`/api/deposits/check-code?code=${encodeURIComponent(transferContent)}`);
        const data = await response.json();

        if (data.success && data.completed) {
            // Show Notification
            showNotify('success', 'Nạp tiền thành công!', `Bạn vừa nạp thành công ${parseFloat(data.amount).toLocaleString('vi-VN')}đ vào tài khoản.`);

            // Reload History
            loadHistory();

            // Stop polling
            clearInterval(pollInterval);
            
            // Reload page to generate a new code after a short delay
            setTimeout(() => {
                location.reload();
            }, 4000);
        }
    } catch (error) {
        console.error('Polling Error:', error);
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', initDepositPage);

