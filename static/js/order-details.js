        // Dropdown Handlers (Synced with layout.html)
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

        function copyContent(btn) {
            const textarea = btn.closest('tr').querySelector('textarea');
            textarea.select();
            document.execCommand('copy');
            const originalText = btn.innerHTML;
            btn.innerHTML = '<i class="fas fa-check"></i> Copied';
            setTimeout(() => { btn.innerHTML = originalText; }, 2000);
        }

        // --- Order Details Logic ---
        let currentOrder = null;
        let orderItems = [];
        let filteredItems = [];
        let currentPage = 1;
        let itemsPerPage = 10;

        function getOrderCodeFromUrl() {
            const pathParts = window.location.pathname.split('/');
            return pathParts[pathParts.length - 1];
        }

        async function loadUserInfo() {
            try {
                const response = await fetch('/api/user/status');
                const data = await response.json();

                if (data.logged_in) {
                    const currentUser = data.user;
                    document.getElementById('userAvatar').textContent = currentUser.username.substring(0, 2).toUpperCase();
                } else {
                    window.location.href = '/login';
                }
            } catch (error) {
                console.error('Error loading user info:', error);
            }
        }

        async function loadOrderDetails() {
            const orderCode = getOrderCodeFromUrl();
            document.getElementById('orderCodeDisplay').innerHTML = `Mã đơn hàng: <b style="color: var(--dark-color);">${orderCode}</b>`;

            try {
                const response = await fetch(`/api/order/${orderCode}`);
                const data = await response.json();

                if (data.success) {
                    currentOrder = data.order;
                    orderItems = data.items;
                    filteredItems = orderItems;
                    renderOrderInfo();
                    renderOrderItems();
                } else {
                    alert('Không tìm thấy đơn hàng hoặc bạn không có quyền truy cập.');
                    window.location.href = '/history';
                }
            } catch (error) {
                console.error('Error loading order details:', error);
                alert('Lỗi kết nối server.');
            }
        }

        function renderOrderInfo() {
            if (!currentOrder) return;

            document.getElementById('productName').textContent = `Sản phẩm: ${currentOrder.product_name}`;
            document.getElementById('orderQty').textContent = `Số lượng mua: ${currentOrder.quantity}`;
            document.getElementById('orderTotal').textContent = `Thanh toán: ${parseFloat(currentOrder.total_amount).toLocaleString('vi-VN')}đ`;
        }

        function renderOrderItems(itemsToRender) {
            if (itemsToRender !== undefined) {
                filteredItems = itemsToRender;
                currentPage = 1; // Reset to page 1 for new filtered list
            }

            const tbody = document.getElementById('orderItemsBody');
            tbody.innerHTML = '';

            const total = filteredItems.length;
            const start = (currentPage - 1) * itemsPerPage;
            const end = Math.min(start + itemsPerPage, total);
            const pagedList = filteredItems.slice(start, end);

            document.getElementById('resultCount').textContent = `Showing ${start + 1}-${end} of ${total} Results`;

            if (pagedList.length === 0) {
                tbody.innerHTML = `<tr><td colspan="4" style="text-align: center;">Không tìm thấy kết quả</td></tr>`;
                renderPagination(0);
                return;
            }

            pagedList.forEach((item, index) => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td style="text-align: center;"><input type="checkbox" class="item-checkbox" data-content="${item.account_content}" style="width: 18px; height: 18px;"></td>
                    <td style="text-align: center;"><b style="color: var(--dark-color);">${start + index + 1}</b></td>
                    <td>
                        <textarea class="textarea-box" rows="2" readonly>${item.account_content}</textarea>
                    </td>
                    <td>
                        <button class="copy-btn-sm" onclick="copyContent(this)"><i class="fas fa-copy"></i> Copy</button>
                    </td>
                `;
                tbody.appendChild(tr);
            });

            renderPagination(total);
        }

        function renderPagination(totalItems) {
            const container = document.getElementById('paginationContainer');
            if (!container) return;
            container.innerHTML = '';

            const totalPages = Math.ceil(totalItems / itemsPerPage);
            if (totalPages <= 1) return;

            // Prev Button
            const prevBtn = document.createElement('a');
            prevBtn.className = `page-link ${currentPage === 1 ? 'disabled' : ''}`;
            prevBtn.innerHTML = '<i class="fas fa-chevron-left"></i>';
            prevBtn.onclick = () => changePage(currentPage - 1);
            container.appendChild(prevBtn);

            // Page Numbers
            let startPage = Math.max(1, currentPage - 2);
            let endPage = Math.min(totalPages, startPage + 4);
            if (endPage - startPage < 4) startPage = Math.max(1, endPage - 4);

            for (let i = startPage; i <= endPage; i++) {
                const pageBtn = document.createElement('a');
                pageBtn.className = `page-link ${currentPage === i ? 'active' : ''}`;
                pageBtn.innerText = i;
                pageBtn.onclick = () => changePage(i);
                container.appendChild(pageBtn);
            }

            // Next Button
            const nextBtn = document.createElement('a');
            nextBtn.className = `page-link ${currentPage === totalPages ? 'disabled' : ''}`;
            nextBtn.innerHTML = '<i class="fas fa-chevron-right"></i>';
            nextBtn.onclick = () => changePage(currentPage + 1);
            container.appendChild(nextBtn);
        }

        function changePage(page) {
            currentPage = page;
            renderOrderItems();
            window.scrollTo({ top: document.querySelector('.details-card').offsetTop - 20, behavior: 'smooth' });
        }

        function changeItemsPerPage(val) {
            itemsPerPage = parseInt(val);
            currentPage = 1;
            renderOrderItems();
        }

        function toggleSelectAll(checkbox) {
            const checkboxes = document.querySelectorAll('.item-checkbox');
            checkboxes.forEach(cb => cb.checked = checkbox.checked);
        }

        // Search Filter Logic
        function searchOrderItems() {
            try {
                const searchInput = document.getElementById('searchInput');
                if (!searchInput) return;

                const keyword = searchInput.value.trim().toLowerCase();
                console.log('Searching for:', keyword);

                if (!keyword) {
                    renderOrderItems(orderItems);
                    return;
                }

                const filtered = orderItems.filter(item => {
                    const content = String(item.account_content || '');
                    const parts = content.split('|');
                    const uid = parts.length > 0 ? parts[0] : '';
                    return uid.toLowerCase().includes(keyword);
                });

                console.log('Found results:', filtered.length);
                renderOrderItems(filtered);
            } catch (e) {
                console.error('Search error:', e);
                alert('Có lỗi xảy ra khi tìm kiếm: ' + e.message);
            }
        }

        function clearFilter() {
            const searchInput = document.getElementById('searchInput');
            if (searchInput) searchInput.value = '';
            renderOrderItems(orderItems);
        }

        // Action Buttons
        document.querySelector('.btn-copy').onclick = function () {
            const allContent = orderItems.map(item => item.account_content).join('\n');
            if (!allContent) return;
            navigator.clipboard.writeText(allContent).then(() => {
                const originalText = this.innerHTML;
                this.innerHTML = '<i class="fas fa-check"></i> Đã Copy';
                setTimeout(() => { this.innerHTML = '<i class="fas fa-copy"></i> Copy'; }, 2000);
            });
        };

        document.querySelector('.btn-download').onclick = function () {
            if (!currentOrder) return;
            const content = orderItems.map(item => item.account_content).join('\n');

            const blob = new Blob([content], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${currentOrder.order_code}.txt`;
            a.click();
            URL.revokeObjectURL(url);
        };

        document.querySelector('.btn-delete').onclick = function () {
            if (confirm("Bạn có chắc chắn muốn xóa đơn hàng này? (Chỉ xóa hiển thị)")) {
                // Implement delete logic if needed, currently just redirect
                alert("Đã xóa đơn hàng (demo)");
                window.location.href = '/history';
            }
        };


        window.onload = async function () {
            await loadUserInfo();
            await loadOrderDetails();
        };
