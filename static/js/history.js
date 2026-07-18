function switchTab(tabId, element) {
    // Update Menu
    document.querySelectorAll('.sidebar-menu a').forEach(a => a.classList.remove('active'));
    element.classList.add('active');

    // Update Content
    document.querySelectorAll('.history-content .card').forEach(card => card.classList.remove('active'));
    document.getElementById(tabId).classList.add('active');
}

// Dropdown Handlers (Standardized with layout.html)
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
    const toolsDropdown = document.getElementById('toolsDropdown');
    const toolsContainer = document.getElementById('toolsContainer');
    const miscDropdown = document.getElementById('miscDropdown');
    const miscContainer = document.getElementById('miscContainer');

    if (userDropdown && userDropdown.classList.contains('active') && !userAvatar.contains(event.target)) {
        userDropdown.classList.remove('active');
    }
    if (toolsDropdown && toolsDropdown.classList.contains('active') && !toolsContainer.contains(event.target)) {
        toolsDropdown.classList.remove('active');
    }
    if (miscDropdown && miscDropdown.classList.contains('active') && !miscContainer.contains(event.target)) {
        miscDropdown.classList.remove('active');
    }
}

// API Integration
let currentUser = null;

async function loadUserInfo() {
    try {
        const response = await fetch('/api/user/status?t=' + Date.now());
        const data = await response.json();

        if (data.logged_in) {
            currentUser = data.user;
            // Update sidebar
            document.querySelector('.sidebar-avatar').textContent = currentUser.username.substring(0, 2).toUpperCase();
            document.querySelector('.sidebar-username').textContent = currentUser.username;
            // Update header avatar
            document.getElementById('userAvatar').textContent = currentUser.username.substring(0, 2).toUpperCase();
        } else {
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('Error loading user info:', error);
    }
}

async function loadOrders(filters = {}) {
    try {
        const params = new URLSearchParams(filters);
        // Set default limit if not present
        if (!params.has('limit')) params.append('limit', '50');

        const response = await fetch(`/api/orders?${params.toString()}`);
        const data = await response.json();

        if (data.success) {
            renderOrdersTable(data.orders);
        }
    } catch (error) {
        console.error('Error loading orders:', error);
    }
}

function renderOrdersTable(orders) {
    const tbody = document.querySelector('#order-history tbody');

    if (orders.length === 0) {
        tbody.innerHTML = `
                    <tr>
                        <td colspan="7" class="empty-state">
                            <i class="fas fa-box-open empty-icon"></i>
                            Không tìm thấy đơn hàng nào
                        </td>
                    </tr>
                `;
        return;
    }

    tbody.innerHTML = orders.map(order => `
                <tr>
                    <td class="txt-bold">${order.order_code}</td>
                    <td>${order.product_name}</td>
                    <td>${order.quantity}</td>
                    <td>${parseFloat(order.total_amount).toLocaleString('vi-VN')}đ</td>
                    <td>${order.note || 'No note'}</td>
                    <td>${new Date(order.created_at).toLocaleString('vi-VN')}</td>
                    <td>
                        <a href="/order/${order.order_code}" class="badge badge-primary action-badge">
                            <i class="fas fa-eye"></i>
                        </a>
                        <a href="#" onclick="downloadOrder('${order.order_code}')" class="badge badge-success action-badge">
                            <i class="fas fa-download"></i>
                        </a>
                    </td>
                </tr>
            `).join('');
}

async function loadActivityLogs(filters = {}) {
    try {
        const params = new URLSearchParams(filters);
        if (!params.has('limit')) params.append('limit', '20');

        const response = await fetch(`/api/activity-logs?${params.toString()}`);
        const data = await response.json();

        if (data.success) {
            renderActivityTable(data.logs);
        }
    } catch (error) {
        console.error('Error loading activity logs:', error);
    }
}

function renderActivityTable(logs) {
    const tbody = document.querySelector('#activity-log tbody');

    if (logs.length === 0) {
        tbody.innerHTML = `
                    <tr>
                        <td colspan="3" class="empty-state">
                            <i class="fas fa-box-open empty-icon"></i>
                            Không tìm thấy hoạt động nào
                        </td>
                    </tr>
                `;
        return;
    }

    tbody.innerHTML = logs.map(log => `
                <tr>
                    <td>${new Date(log.created_at).toLocaleString('vi-VN')}</td>
                    <td>${log.action}</td>
                    <td>${log.ip_address || 'N/A'}</td>
                </tr>
            `).join('');
}

async function loadBalanceHistory(filters = {}) {
    try {
        const params = new URLSearchParams(filters);
        if (!params.has('limit')) params.append('limit', '20');

        const response = await fetch(`/api/balance-history?${params.toString()}`);
        const data = await response.json();

        if (data.success) {
            renderBalanceTable(data.history);
        }
    } catch (error) {
        console.error('Error loading balance history:', error);
    }
}

function renderBalanceTable(history) {
    const tbody = document.querySelector('#balance-history tbody');

    if (history.length === 0) {
        tbody.innerHTML = `
                    <tr>
                        <td colspan="6" class="empty-state">
                            <i class="fas fa-box-open empty-icon"></i>
                            Không tìm thấy giao dịch nào
                        </td>
                    </tr>
                `;
        return;
    }

    tbody.innerHTML = history.map(item => {
        const isPositive = parseFloat(item.amount_change) > 0;
        const changeClass = isPositive ? 'txt-amount-pos' : 'txt-amount-neg';
        const changeSign = isPositive ? '+' : '';

        return `
                    <tr>
                        <td>${new Date(item.created_at).toLocaleString('vi-VN')}</td>
                        <td><span class="badge badge-${item.type === 'deposit' ? 'success' : 'info'}">${item.type}</span></td>
                        <td>${parseFloat(item.amount_before).toLocaleString('vi-VN')}đ</td>
                        <td class="${changeClass}">${changeSign}${parseFloat(item.amount_change).toLocaleString('vi-VN')}đ</td>
                        <td>${parseFloat(item.amount_after).toLocaleString('vi-VN')}đ</td>
                        <td>${item.description}</td>
                    </tr>
                `;
    }).join('');
}

// Filter Handlers
function handleSearch(type) {
    if (type === 'orders') {
        const filters = {
            order_code: document.getElementById('order-code-filter').value,
            date_from: document.getElementById('order-date-filter').value, // Use date_from for date filter for now or update API to specific date
            limit: document.getElementById('order-limit').value
        };
        // If API expects 'date' for exact match, use that. Checking API...
        // API orders uses date_from/date_to. API logs/balance uses 'date' (exact).
        // Let's stick to simple date filter for now.
        // For orders, let's map the single date input to date_from for simplicity or exact? 
        // The UI says "Chọn thời gian", usually implies a specific date. 
        // Let's pass it as date_from and date_to (same day range) if we want exact day, 
        // OR just update the order API to support 'date' exact match too?
        // The previous API code for orders supports date_from and date_to.
        // Let's just use date_from for now as a "Since" filter or maybe exact match is better?
        // Adjusting: Let's assume user wants to see orders ON that day.
        if (filters.date_from) {
            filters.date_to = filters.date_from;
        }
        loadOrders(filters);
    } else if (type === 'logs') {
        const filters = {
            action: document.getElementById('log-action-filter').value,
            ip_address: document.getElementById('log-ip-filter').value,
            date: document.getElementById('log-date-filter').value
        };
        loadActivityLogs(filters);
    } else if (type === 'balance') {
        const filters = {
            description: document.getElementById('balance-desc-filter').value,
            date: document.getElementById('balance-date-filter').value
        };
        loadBalanceHistory(filters);
    }
}

function clearFilter(type) {
    if (type === 'orders') {
        document.getElementById('order-code-filter').value = '';
        document.getElementById('order-date-filter').value = '';
        document.getElementById('order-limit').value = '50';
        loadOrders({ limit: 50 });
    } else if (type === 'logs') {
        document.getElementById('log-action-filter').value = '';
        document.getElementById('log-ip-filter').value = '';
        document.getElementById('log-date-filter').value = '';
        loadActivityLogs();
    } else if (type === 'balance') {
        document.getElementById('balance-desc-filter').value = '';
        document.getElementById('balance-date-filter').value = '';
        loadBalanceHistory();
    }
}

function downloadOrder(orderCode) {
    fetch(`/api/order/${orderCode}`)
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const content = data.items.map(item => item.account_content).join('\n');

                const blob = new Blob([content], { type: 'text/plain' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${orderCode}.txt`;
                a.click();
                URL.revokeObjectURL(url);
            }
        })
        .catch(error => console.error('Download error:', error));
    return false;
}

// Load data on page load
window.onload = async function () {
    await loadUserInfo();
    await loadOrders();
    await loadActivityLogs();
    await loadBalanceHistory();
};
