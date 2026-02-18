        let currentPrice = 0;
        let currentProductId = null;
        let quantity = 1;
        let isFirstLoad = true;
        let currentUser = null;

        function showNotify(type, title, message, duration = 2000) {
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

        async function checkAuth() {
            try {
                const response = await fetch('/api/user/status');
                const data = await response.json();

                const authElements = document.querySelectorAll('.auth-required');
                const userAvatar = document.getElementById('userAvatar');
                const userDropdown = document.getElementById('userDropdown');

                if (data.logged_in) {
                    currentUser = data.user;
                    authElements.forEach(el => el.style.display = 'flex');
                    userAvatar.innerText = currentUser.username.substring(0, 2).toUpperCase();
                    userAvatar.style.background = 'var(--primary-color)';

                    let dropdownHtml = `
                        <a href="/profile">Hồ sơ cá nhân</a>
                        <a href="/history">Lịch sử đơn hàng</a>
                        <a href="/deposit">Nạp tiền</a>
                    `;

                    if (currentUser.role === 'admin') {
                        dropdownHtml += `<a href="/admin/dashboard" style="color: var(--primary-color);">Quản trị viên</a>`;
                    }

                    dropdownHtml += `
                        <div class="divider"></div>
                        <a href="/logout">Đăng xuất</a>
                    `;
                    userDropdown.innerHTML = dropdownHtml;
                } else {
                    currentUser = null;
                    authElements.forEach(el => el.style.display = 'none');
                    userAvatar.innerHTML = '<i class="fas fa-user"></i>';
                    userAvatar.style.background = '#65676B';
                }
            } catch (error) {
                console.error('Auth Check Error:', error);
            }
        }

        function handleAvatarClick(event) {
            if (!currentUser) {
                window.location.href = '/login';
                return;
            }
            toggleUserMenu(event);
        }

        const getSkeletonCard = () => `
            <div class="skeleton-card">
                <div>
                    <div class="skeleton" style="height: 20px; width: 70%; margin-bottom: 12px;"></div>
                    <div class="skeleton" style="height: 14px; width: 90%; margin-bottom: 8px;"></div>
                    <div class="skeleton" style="height: 14px; width: 40%;"></div>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: flex-end;">
                    <div class="skeleton skeleton-price"></div>
                    <div class="skeleton skeleton-button"></div>
                </div>
            </div>
        `;

        const getSkeletonSection = () => `
            <div style="margin-bottom: 40px; width: 100%;">
                <div class="skeleton skeleton-title" style="width: 200px; height: 30px; margin-bottom: 20px;"></div>
                <div class="products">
                    ${getSkeletonCard()}
                    ${getSkeletonCard()}
                    ${getSkeletonCard()}
                </div>
            </div>
        `;

        async function fetchCategories() {
            const response = await fetch('/api/categories');
            return await response.json();
        }

        async function fetchProducts() {
            const response = await fetch('/api/products');
            return await response.json();
        }

        async function renderNavMenu() {
            try {
                const categories = await fetchCategories();
                const navMenu = document.getElementById('navMenu');
                const currentPath = window.location.pathname;

                // Keep the "Trang chủ" link
                navMenu.innerHTML = `<li><a href="/" class="${currentPath === '/' ? 'active' : ''}" onclick="navigate('/', event)">Trang chủ</a></li>`;

                categories.forEach(cat => {
                    if (!cat.slug) return; // skip categories without slug
                    const li = document.createElement('li');
                    const path = `/category/${cat.slug}`;
                    li.innerHTML = `<a href="${path}" class="${currentPath === path ? 'active' : ''}" onclick="navigate('${path}', event)">${cat.name}</a>`;
                    navMenu.appendChild(li);
                });
            } catch (error) {
                console.error('Nav Menu Error:', error);
            }
        }

        async function renderProducts(path = '/') {
            const container = document.getElementById('productList');

            container.innerHTML = getSkeletonSection() + getSkeletonSection();

            try {
                const categories = await fetchCategories();
                const products = await fetchProducts();

                container.innerHTML = '';

                // Group products by category
                const grouped = {};
                categories.forEach(cat => {
                    grouped[cat.id] = {
                        name: cat.name,
                        products: products.filter(p => p.category_id === cat.id)
                    };
                });

                // Filter by path if not home
                let categoriesToRender = categories;
                if (path !== '/' && path.startsWith('/category/')) {
                    const targetSlug = path.replace('/category/', '');
                    categoriesToRender = categories.filter(c => c.slug === targetSlug);
                }

                if (categoriesToRender.length === 0) {
                    container.innerHTML = '<p style="text-align: center; width: 100%; padding: 40px; color: var(--gray-color);">Không tìm thấy sản phẩm trong danh mục này.</p>';
                    return;
                }

                categoriesToRender.forEach(cat => {
                    const catProducts = grouped[cat.id]?.products || [];
                    if (catProducts.length === 0 && path === '#/') return;

                    const sectionHtml = `
                        <section class="category-section" style="margin-bottom: 40px; width: 100%;">
                            <h2 class="section-title" style="margin-bottom: 20px;">
                                <i class="fas fa-chevron-right"></i> ${cat.name}
                            </h2>
                            <div class="products">
                                ${catProducts.map(p => `
                                    <article class="product-card">
                                        <div class="product-info">
                                            <div>
                                                <h3>${p.name}</h3>
                                                <p class="product-description">${p.description}</p>
                                                <div class="product-meta">Kho hàng: ${p.stock} &nbsp;|&nbsp; Đã bán: ${p.sold_count || 0}</div>
                                            </div>
                                            <div class="product-actions">
                                                <div class="product-price">${parseFloat(p.price).toLocaleString('vi-VN')}đ</div>
                                                <div class="product-btn-group">
                                                    <button class="btn btn-buy" onclick="openCheckoutFromData(${p.id}, '${p.name}', '${parseFloat(p.price).toLocaleString('vi-VN')}đ', '${p.description}')"><i class="fas fa-shopping-cart"></i> MUA</button>
                                                    <button class="btn btn-detail" onclick="openImageModal('${p.image_url}', '${p.name}')">Chi tiết</button>
                                                </div>
                                            </div>
                                        </div>
                                    </article>
                                `).join('')}
                            </div>
                        </section>
                    `;
                    container.innerHTML += sectionHtml;
                });

                if (isFirstLoad) {
                    showInitialAnnouncement();
                    isFirstLoad = false;
                }

            } catch (error) {
                console.error('Render Error:', error);
                container.innerHTML = '<p>Lỗi khi tải dữ liệu. Vui lòng thử lại sau.</p>';
            }
        }

        function showInitialAnnouncement() {
            document.getElementById('announcementModal').classList.add('active');
            document.body.style.overflow = 'hidden';
        }

        function navigate(path, event) {
            if (event) event.preventDefault();

            // Update URL using History API
            window.history.pushState({}, '', path);

            // Update Active State
            const links = document.querySelectorAll('.nav-menu a');
            links.forEach(link => {
                const linkPath = link.getAttribute('href');
                if (linkPath === path) {
                    link.classList.add('active');
                } else {
                    link.classList.remove('active');
                }
            });

            // Render Products
            renderProducts(path);
        }

        window.onpopstate = function () {
            const path = window.location.pathname;
            // Update Active State on PopState
            const links = document.querySelectorAll('.nav-menu a');
            links.forEach(link => {
                if (link.getAttribute('href') === path) {
                    link.classList.add('active');
                } else {
                    link.classList.remove('active');
                }
            });
            renderProducts(path);
        };

        function openImageModal(imageUrl, title) {
            const modal = document.getElementById('imageModal');
            const img = document.getElementById('modalImage');
            img.src = imageUrl;
            img.alt = title || 'Thông tin tài khoản Facebook';
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        }

        function closeImageModal() {
            const modal = document.getElementById('imageModal');
            modal.classList.remove('active');
            document.body.style.overflow = 'auto';
        }

        function openCheckoutFromData(productId, title, price, description) {
            if (!currentUser) {
                window.location.href = '/login';
                return;
            }
            // Store product ID
            currentProductId = productId;
            // Extract price number
            currentPrice = parseInt(price.replace(/[^0-9]/g, ''));
            quantity = 1;

            document.getElementById('modalProductTitle').textContent = title;
            document.getElementById('modalPrice').textContent = price;
            document.getElementById('modalDescription').textContent = description;

            // Update user balance display
            if (currentUser && currentUser.balance !== undefined) {
                document.getElementById('userBalance').textContent = parseFloat(currentUser.balance).toLocaleString('vi-VN') + 'đ';
            }

            // Hide badge in modal
            const modalBadge = document.getElementById('modalBadge');
            if (modalBadge) {
                modalBadge.style.display = 'none';
            }
            document.getElementById('quantityInput').value = quantity;

            updateTotal();
            document.getElementById('checkoutModal').classList.add('active');
        }

        function openCheckout(element) {
            if (!currentUser) {
                window.location.href = '/login';
                return;
            }
            const card = element.closest('.product-card');
            if (!card) return;

            const title = card.querySelector('h3').textContent;
            const price = card.querySelector('.product-price').textContent;
            const description = card.querySelector('.product-description').textContent;

            // Extract price number
            currentPrice = parseInt(price.replace(/[^0-9]/g, ''));
            quantity = 1;

            document.getElementById('modalProductTitle').textContent = title;
            document.getElementById('modalPrice').textContent = price;
            document.getElementById('modalDescription').textContent = description;

            // Hide badge in modal if not present on card
            const modalBadge = document.getElementById('modalBadge');
            if (modalBadge) {
                modalBadge.style.display = 'none';
            }
            document.getElementById('quantityInput').value = quantity;

            updateTotal();
            document.getElementById('checkoutModal').classList.add('active');
        }

        function closeCheckout() {
            document.getElementById('checkoutModal').classList.remove('active');
        }

        function increaseQuantity() {
            quantity++;
            document.getElementById('quantityInput').value = quantity;
            updateTotal();
        }

        function decreaseQuantity() {
            if (quantity > 1) {
                quantity--;
                document.getElementById('quantityInput').value = quantity;
                updateTotal();
            }
        }

        function updateTotal() {
            const subtotal = currentPrice * quantity;
            document.getElementById('subtotal').textContent = subtotal.toLocaleString('vi-VN') + 'đ';
            document.getElementById('total').textContent = subtotal.toLocaleString('vi-VN') + 'đ';
        }

        function manualQuantityInput(input) {
            let val = parseInt(input.value);
            if (isNaN(val) || val < 1) {
                quantity = 1;
            } else {
                quantity = val;
            }
            updateTotal();
        }

        let lastOrderCode = null;

        async function checkout() {
            if (!currentProductId) {
                showNotify('error', 'Lỗi', 'Không tìm thấy thông tin sản phẩm');
                return;
            }

            try {
                const response = await fetch('/api/purchase', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        product_id: currentProductId,
                        quantity: quantity
                    })
                });

                const data = await response.json();

                if (data.success) {
                    // Update user balance
                    if (currentUser) {
                        currentUser.balance = data.new_balance;
                    }

                    // Store accounts for copying and order code for redirect
                    purchasedAccounts = data.accounts;
                    lastOrderCode = data.order_code;

                    // Format accounts as simple list without titles
                    const accountsHtml = data.accounts.map(acc =>
                        `<div class="purchase-detail-item">
                            <code>${acc}</code>
                        </div>`
                    ).join('');

                    const detailsHtml = `
                        <div style="background: #fdfdfd; border: 1px dashed #ddd; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 14px;">
                                <span style="color: #666;">Mã đơn hàng:</span>
                                <span style="font-weight: 600;">${data.order_code}</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 14px;">
                                <span style="color: #666;">Số tiền:</span>
                                <span style="color: #d32f2f; font-weight: 700;">-${data.total_amount.toLocaleString('vi-VN')}đ</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; font-size: 14px;">
                                <span style="color: #666;">Số dư hiện tại:</span>
                                <span style="font-weight: 600;">${data.new_balance.toLocaleString('vi-VN')}đ</span>
                            </div>
                        </div>
                        <div>
                            <p style="font-weight: 600; color: #333; margin-bottom: 10px; font-size: 15px;">Dữ liệu tài khoản (${data.accounts.length}):</p>
                            <textarea readonly style="width: 100%; height: 160px; padding: 12px; border: 1px solid #ddd; border-radius: 6px; font-family: monospace; font-size: 13px; background: #fff; line-height: 1.6; resize: none; outline: none;">${data.accounts.join('\n')}</textarea>
                            <p style="margin-top: 10px; font-size: 12px; color: #777; font-style: italic;">
                                Tip: Bạn có thể copy nhanh bằng nút bên dưới hoặc bôi đen trong ô trên.
                            </p>
                        </div>
                    `;

                    document.getElementById('purchaseDetails').innerHTML = detailsHtml;
                    document.getElementById('successPurchaseModal').classList.add('active');
                    closeCheckout();
                } else {
                    showNotify('error', 'Không thể mua hàng', data.error || 'Vui lòng thử lại sau');
                }
            } catch (error) {
                console.error('Purchase error:', error);
                showNotify('error', 'Lỗi kết nối', 'Không thể kết nối với máy chủ. Vui lòng kiểm tra kết nối và thử lại.');
            }
        }

        function copyAllAccounts() {
            if (purchasedAccounts.length === 0) {
                showNotify('error', 'Lỗi', 'Không có tài khoản để sao chép');
                return;
            }

            const allAccountsText = purchasedAccounts.join('\n');

            navigator.clipboard.writeText(allAccountsText).then(() => {
                showNotify('success', 'Đã sao chép!', `Đã sao chép ${purchasedAccounts.length} tài khoản vào clipboard`, 1500);
            }).catch(err => {
                console.error('Copy failed:', err);
                showNotify('error', 'Lỗi', 'Không thể sao chép. Vui lòng sao chép thủ công.');
            });
        }

        function closePurchaseModal() {
            if (lastOrderCode) {
                window.location.href = `/order/${lastOrderCode}`;
            } else {
                const modal = document.getElementById('successPurchaseModal');
                modal.classList.remove('active');
                document.body.style.overflow = 'auto';
                // Refresh products to update stock
                const path = window.location.pathname;
                renderProducts(path);
            }
        }

        function closeAnnouncement() {
            document.getElementById('announcementModal').classList.remove('active');
            document.body.style.overflow = 'auto';
        }

        window.onload = async function () {
            await checkAuth();
            await renderNavMenu();
            const path = window.location.pathname;
            renderProducts(path);
        };

        // Close modal when clicking outside
        window.onclick = function (event) {
            const checkoutModal = document.getElementById('checkoutModal');
            const announcementModal = document.getElementById('announcementModal');
            const userDropdown = document.getElementById('userDropdown');
            const userAvatar = document.getElementById('userAvatar');
            const toolsDropdown = document.getElementById('toolsDropdown');
            const toolsContainer = document.getElementById('toolsContainer');
            const miscDropdown = document.getElementById('miscDropdown');
            const miscContainer = document.getElementById('miscContainer');

            if (event.target == checkoutModal) {
                closeCheckout();
            }
            if (event.target == announcementModal) {
                closeAnnouncement();
            }
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

        function toggleUserMenu(event) {
            event.stopPropagation();
            document.getElementById('userDropdown').classList.toggle('active');
            // Close other menus if open
            document.getElementById('toolsDropdown').classList.remove('active');
            document.getElementById('miscDropdown').classList.remove('active');
        }

        function toggleToolsMenu(event) {
            event.stopPropagation();
            document.getElementById('toolsDropdown').classList.toggle('active');
            // Close other menus if open
            document.getElementById('userDropdown').classList.remove('active');
            document.getElementById('miscDropdown').classList.remove('active');
        }

        function toggleMiscMenu(event) {
            event.stopPropagation();
            document.getElementById('miscDropdown').classList.toggle('active');
            // Close other menus if open
            document.getElementById('userDropdown').classList.remove('active');
            document.getElementById('toolsDropdown').classList.remove('active');
        }
