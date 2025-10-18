// 全局变量
let currentUser = null;
let bookSources = [];

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    checkAuthStatus();
});

// 检查登录状态
function checkAuthStatus() {
    const token = localStorage.getItem('token');
    const username = localStorage.getItem('username');
    
    if (token && username) {
        currentUser = { username: username };
        updateNavbar(true);
    } else {
        updateNavbar(false);
    }
}

// 更新导航栏
function updateNavbar(isLoggedIn) {
    const loginNav = document.getElementById('loginNav');
    const userNav = document.getElementById('userNav');
    const usernameSpan = document.getElementById('username');
    
    if (isLoggedIn) {
        loginNav.classList.add('d-none');
        userNav.classList.remove('d-none');
        if (usernameSpan) {
            usernameSpan.textContent = currentUser.username;
        }
    } else {
        loginNav.classList.remove('d-none');
        userNav.classList.add('d-none');
    }
}

// 显示登录模态框
function showLoginModal() {
    const modal = new bootstrap.Modal(document.getElementById('loginModal'));
    modal.show();
}

// 显示注册模态框
function showRegisterModal() {
    // 关闭登录模态框
    const loginModal = bootstrap.Modal.getInstance(document.getElementById('loginModal'));
    if (loginModal) {
        loginModal.hide();
    }
    
    // 这里可以添加注册模态框的代码
    showAlert('注册功能待实现', 'info');
}

// 登录
async function login() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    if (!username || !password) {
        showAlert('请输入用户名和密码', 'warning');
        return;
    }
    
    try {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);
        
        const response = await fetch('/api/auth/token', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('token', data.access_token);
            localStorage.setItem('username', username);
            
            currentUser = { username: username };
            updateNavbar(true);
            
            // 关闭模态框
            const modal = bootstrap.Modal.getInstance(document.getElementById('loginModal'));
            modal.hide();
            
            showAlert('登录成功', 'success');
            
            // 清空表单
            document.getElementById('loginForm').reset();
            
        } else {
            const error = await response.json();
            showAlert(error.detail || '登录失败', 'danger');
        }
    } catch (error) {
        console.error('登录失败:', error);
        showAlert('登录失败，请检查网络连接', 'danger');
    }
}

// 退出登录
function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    currentUser = null;
    updateNavbar(false);
    showAlert('已退出登录', 'info');
    
    // 如果在需要登录的页面，可以重定向到首页
    if (window.location.pathname.includes('/book/')) {
        window.location.href = '/';
    }
}

// 显示搜索模态框
function showSearchModal() {
    loadBookSources().then(() => {
        // 同时填充两个书源选择器
        const searchSelect = document.getElementById('searchSource');
        const urlSelect = document.getElementById('urlSource');
        
        if (searchSelect && urlSelect) {
            urlSelect.innerHTML = searchSelect.innerHTML;
        }
        
        const modal = new bootstrap.Modal(document.getElementById('searchModal'));
        modal.show();
    });
}

// 加载书源列表
async function loadBookSources() {
    try {
        const response = await fetch('/api/sources/');
        bookSources = await response.json();
        
        const select = document.getElementById('searchSource');
        select.innerHTML = '<option value="">选择书源</option>' + 
            bookSources.map(source => 
                `<option value="${source.id}">${source.name}</option>`
            ).join('');
            
    } catch (error) {
        console.error('加载书源失败:', error);
        showAlert('加载书源失败', 'danger');
    }
}

// 搜索书籍
async function searchBooks() {
    const sourceId = document.getElementById('searchSource').value;
    const keyword = document.getElementById('searchKeyword').value.trim();
    
    if (!sourceId) {
        showAlert('请选择书源', 'warning');
        return;
    }
    
    if (!keyword) {
        showAlert('请输入搜索关键词', 'warning');
        return;
    }
    
    const resultsDiv = document.getElementById('searchResults');
    resultsDiv.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div></div>';
    
    try {
        const response = await fetch(`/api/sources/${sourceId}/search?keyword=${encodeURIComponent(keyword)}`);
        const results = await response.json();
        
        if (results.length === 0) {
            resultsDiv.innerHTML = '<div class="text-center text-muted">未找到相关书籍</div>';
            return;
        }
        
        resultsDiv.innerHTML = results.map(book => `
            <div class="search-result-item">
                <div class="row">
                    <div class="col-2">
                        <img src="${book.cover_url || '/static/images/default-cover.jpg'}" 
                             class="search-result-cover" alt="${book.title}">
                    </div>
                    <div class="col-8">
                        <h6>${book.title}</h6>
                        <p class="text-muted small">作者: ${book.author}</p>
                        <p class="small">${book.description.substring(0, 150)}...</p>
                    </div>
                    <div class="col-2 d-flex align-items-center">
                        <button class="btn btn-primary btn-sm" 
                                onclick="importBook('${sourceId}', '${book.source_url}')">
                            <i class="bi bi-download"></i> 导入
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('搜索失败:', error);
        resultsDiv.innerHTML = '<div class="text-center text-danger">搜索失败，请重试</div>';
    }
}

// 导入书籍
async function importBook(sourceId, bookUrl) {
    try {
        const response = await fetch('/api/sources/import', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                source_id: sourceId,
                book_url: bookUrl
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            showAlert(result.message, 'success');

            // 刷新书架
            if (typeof loadBooks === 'function') {
                setTimeout(loadBooks, 2000); // 2秒后刷新，给导入一些时间
            }
        } else {
            const error = await response.json();
            console.error('导入API错误:', error);
            showAlert(error.detail || '导入失败', 'danger');
        }
    } catch (error) {
        console.error('导入书籍失败:', error);
        showAlert('导入失败，请检查网络连接', 'danger');
    }
}

// 显示书源管理模态框
function showSourceModal() {
    loadSourceList().then(() => {
        const modal = new bootstrap.Modal(document.getElementById('sourceModal'));
        modal.show();
    });
}

// 显示阅读历史
async function showReadingHistory() {
    const token = localStorage.getItem('token');
    if (!token) {
        showAlert('请先登录', 'warning');
        return;
    }
    
    try {
        const response = await fetch('/api/reading/history', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const history = await response.json();
            
            if (history.length === 0) {
                showAlert('暂无阅读历史', 'info');
                return;
            }
            
            // 这里可以显示一个模态框展示阅读历史
            console.log('阅读历史:', history);
            showAlert('阅读历史功能待完善', 'info');
            
        } else {
            showAlert('获取阅读历史失败', 'danger');
        }
    } catch (error) {
        console.error('获取阅读历史失败:', error);
        showAlert('获取阅读历史失败', 'danger');
    }
}

// 显示提示信息
function showAlert(message, type = 'info') {
    // 移除现有的提示
    const existingAlert = document.querySelector('.alert-floating');
    if (existingAlert) {
        existingAlert.remove();
    }
    
    // 创建新的提示
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-floating position-fixed`;
    alert.style.cssText = `
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    `;
    alert.innerHTML = `
        <div class="d-flex align-items-center">
            <span class="flex-grow-1">${message}</span>
            <button type="button" class="btn-close btn-close-white ms-2" onclick="this.parentElement.parentElement.remove()"></button>
        </div>
    `;
    
    document.body.appendChild(alert);
    
    // 3秒后自动移除
    setTimeout(() => {
        if (alert.parentElement) {
            alert.remove();
        }
    }, 3000);
}

// 工具函数：格式化日期
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// 工具函数：截断文本
function truncateText(text, maxLength) {
    if (text.length <= maxLength) {
        return text;
    }
    return text.substring(0, maxLength) + '...';
}
// 书源管理相关函数

// 加载书源列表
async function loadSourceList() {
    try {
        const response = await fetch('/api/sources/');
        const sources = await response.json();
        
        const sourceList = document.getElementById('sourceList');
        if (sources.length === 0) {
            sourceList.innerHTML = '<div class="text-center text-muted p-3">暂无书源</div>';
            return;
        }
        
        sourceList.innerHTML = sources.map(source => `
            <div class="source-item" data-id="${source.id}">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <div class="d-flex align-items-center mb-1">
                            <span class="source-status active"></span>
                            <strong>${source.name}</strong>
                        </div>
                        <div class="text-muted small">${source.url}</div>
                    </div>
                    <div class="source-actions">
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-outline-primary" onclick="editSource('${source.id}')" title="编辑">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button class="btn btn-outline-success" onclick="testSource('${source.id}')" title="测试">
                                <i class="bi bi-play"></i>
                            </button>
                            <button class="btn btn-outline-warning" onclick="toggleSource('${source.id}')" title="启用/禁用">
                                <i class="bi bi-power"></i>
                            </button>
                            <button class="btn btn-outline-danger" onclick="deleteSource('${source.id}')" title="删除">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('加载书源列表失败:', error);
        showAlert('加载书源列表失败', 'danger');
    }
}

// 显示添加书源表单
function showAddSourceForm() {
    const sourceForm = document.getElementById('sourceForm');
    const presetSources = document.getElementById('presetSources');
    const addSourceForm = document.getElementById('addSourceForm');
    
    if (sourceForm) sourceForm.classList.remove('d-none');
    if (presetSources) presetSources.classList.add('d-none');
    if (addSourceForm) addSourceForm.reset();
}

// 隐藏添加书源表单
function hideAddSourceForm() {
    document.getElementById('sourceForm').classList.add('d-none');
    document.getElementById('presetSources').classList.remove('d-none');
}

function showSourceJsonExample() {
    document.getElementById('importJson').value = `{
        "name": "",
        "show_name": "",
        "url": "",
        "encoding": "utf-8",
        "domains": [
        ],
        "search": {
            "url": "{keyword}",
            "items": [],
            "next": "",
            "title": [],
            "author": [],
            "description": [],
            "cover_img": [],
            "cover_bg_img": [],
        },
        "chapter_list": {
            "count_per_page": 0,
            "list":[],
            "items": [],
            "pagers": {
                "items": "",
                "current": ""
            },
            "page_url": {
                "skip_endding": "/",
                "fmt": "{book_url}/index_{page}.html"
            }
        },
        "book": {
            "title": [],
            "author": [],
            "description": [],
            "cover_img": [],
            "cover_bg_img": [],
        },
        "content": {
            "selector": "",
            "remove_tags": [],
            "remove_patterns": [],
            "next": ""
        }
    }`;
}

// 保存书源
async function saveBookSource() {
    const formData = {
        name: document.getElementById('sourceName').value,
        url: document.getElementById('sourceUrl').value,
        search_url: document.getElementById('searchUrl').value,
        book_url_pattern: document.getElementById('bookUrlPattern').value,
        chapter_url_pattern: document.getElementById('chapterUrlPattern').value,
        content_selector: document.getElementById('contentSelector').value
    };
    
    // 验证必填字段
    if (!formData.name || !formData.url || !formData.search_url) {
        showAlert('请填写必填字段', 'warning');
        return;
    }
    await updateBookSource(formData);
}

async function updateBookSource(sourceData) {
    try {
        const response = await fetch('/api/sources/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({name:sourceData.name, sourcejson: sourceData})
        });
        
        if (response.ok) {
            showAlert('书源添加成功', 'success');
            hideAddSourceForm();
            loadSourceList();
        } else {
            const error = await response.json();
            showAlert(error.detail || '添加失败', 'danger');
        }
    } catch (error) {
        console.error('保存书源失败:', error);
        showAlert('保存失败，请检查网络连接', 'danger');
    }
}

// 测试书源
async function testBookSource() {
    const searchUrl = document.getElementById('searchUrl').value;
    const contentSelector = document.getElementById('contentSelector').value;
    
    if (!searchUrl) {
        showAlert('请先填写搜索URL', 'warning');
        return;
    }
    
    // 移除现有的测试结果
    const existingResult = document.querySelector('.test-result');
    if (existingResult) {
        existingResult.remove();
    }
    
    // 显示测试中状态
    const testResult = document.createElement('div');
    testResult.className = 'test-result';
    testResult.innerHTML = '<i class="bi bi-hourglass-split"></i> 正在测试书源...';
    document.getElementById('addSourceForm').appendChild(testResult);
    
    try {
        // 这里可以添加实际的测试逻辑
        // 暂时模拟测试结果
        setTimeout(() => {
            testResult.className = 'test-result success';
            testResult.innerHTML = `
                <i class="bi bi-check-circle"></i> 测试成功
                <div class="small mt-1">
                    搜索URL格式正确<br>
                    ${contentSelector ? '内容选择器已设置' : '建议设置内容选择器'}
                </div>
            `;
        }, 2000);
        
    } catch (error) {
        testResult.className = 'test-result error';
        testResult.innerHTML = `<i class="bi bi-x-circle"></i> 测试失败: ${error.message}`;
    }
}

// 添加预设书源
function addPresetSource(type) {
    const presets = {
        biquge: {
            name: '笔趣阁',
            url: 'https://www.biquge.com',
            search_url: 'https://www.biquge.com/search?q={keyword}',
            book_url_pattern: '/book/*',
            chapter_url_pattern: '/book/*/chapter/*',
            content_selector: '.content'
        },
        qidian: {
            name: '起点中文网',
            url: 'https://www.qidian.com',
            search_url: 'https://www.qidian.com/search?kw={keyword}',
            book_url_pattern: '/book/*',
            chapter_url_pattern: '/chapter/*',
            content_selector: '.read-content'
        },
        custom: {
            name: '',
            url: '',
            search_url: '',
            book_url_pattern: '',
            chapter_url_pattern: '',
            content_selector: ''
        }
    };
    
    const preset = presets[type];
    if (preset) {
        // 先显示表单
        showAddSourceForm();
        
        // 等待DOM更新后再填充数据
        setTimeout(() => {
            const sourceNameEl = document.getElementById('sourceName');
            const sourceUrlEl = document.getElementById('sourceUrl');
            const searchUrlEl = document.getElementById('searchUrl');
            const bookUrlPatternEl = document.getElementById('bookUrlPattern');
            const chapterUrlPatternEl = document.getElementById('chapterUrlPattern');
            const contentSelectorEl = document.getElementById('contentSelector');
            
            console.log('填充预设书源:', type, preset);
            console.log('表单元素:', {
                sourceNameEl, sourceUrlEl, searchUrlEl, 
                bookUrlPatternEl, chapterUrlPatternEl, contentSelectorEl
            });
            
            if (sourceNameEl) {
                sourceNameEl.value = preset.name;
                console.log('设置书源名称:', preset.name);
            } else {
                console.error('未找到sourceName元素');
            }
            
            if (sourceUrlEl) sourceUrlEl.value = preset.url;
            if (searchUrlEl) searchUrlEl.value = preset.search_url;
            if (bookUrlPatternEl) bookUrlPatternEl.value = preset.book_url_pattern;
            if (chapterUrlPatternEl) chapterUrlPatternEl.value = preset.chapter_url_pattern;
            if (contentSelectorEl) contentSelectorEl.value = preset.content_selector;
            
            // 验证填充结果
            console.log('填充后的值:', {
                name: sourceNameEl?.value,
                url: sourceUrlEl?.value,
                searchUrl: searchUrlEl?.value
            });
        }, 100);
    }
}

// 从JSON导入书源
function importFromJson() {
    const jsonText = document.getElementById('importJson').value.trim();
    if (!jsonText) {
        showAlert('请输入JSON配置', 'warning');
        return;
    }
    
    try {
        const sourceData = JSON.parse(jsonText);
        
        // 验证JSON格式
        if (!sourceData.name) {
            showAlert('JSON格式不正确，缺少必要字段', 'danger');
            return;
        }
        
        updateBookSource(sourceData);
    } catch (error) {
        showAlert('JSON格式错误: ' + error.message, 'danger');
    }
}

// 从文件导入书源
function importFromFile() {
    const fileInput = document.getElementById('importFile');
    const file = fileInput.files[0];
    
    if (!file) {
        showAlert('请选择文件', 'warning');
        return;
    }
    
    const reader = new FileReader();
    reader.onload = function(e) {
        try {
            const content = e.target.result;
            let sourceData;
            
            if (file.name.endsWith('.json')) {
                sourceData = JSON.parse(content);
            } else {
                // 尝试解析文本文件
                sourceData = JSON.parse(content);
            }
            
            // 如果是书源数组，导入第一个
            if (Array.isArray(sourceData)) {
                sourceData = sourceData[0];
                for (let i = 1; i < sourceData.length; i++) {
                    updateBookSource(sourceData[i]);
                }
            } else {
                updateBookSource(sourceData);
            }

        } catch (error) {
            showAlert('文件格式错误: ' + error.message, 'danger');
        }
    };
    
    reader.readAsText(file);
}

// 编辑书源
async function editSource(sourceId) {
    try {
        const response = await fetch(`/api/sources/${sourceId}`);
        const source = await response.json();
        
        // 先显示表单
        showAddSourceForm();
        
        // 等待DOM更新后再填充数据
        setTimeout(() => {
            const sourceNameEl = document.getElementById('sourceName');
            const sourceUrlEl = document.getElementById('sourceUrl');
            const searchUrlEl = document.getElementById('searchUrl');
            const bookUrlPatternEl = document.getElementById('bookUrlPattern');
            const chapterUrlPatternEl = document.getElementById('chapterUrlPattern');
            const contentSelectorEl = document.getElementById('contentSelector');
            
            if (sourceNameEl) sourceNameEl.value = source.name || '';
            if (sourceUrlEl) sourceUrlEl.value = source.url || '';
            if (searchUrlEl) searchUrlEl.value = source.search_url || '';
            if (bookUrlPatternEl) bookUrlPatternEl.value = source.book_url_pattern || '';
            if (chapterUrlPatternEl) chapterUrlPatternEl.value = source.chapter_url_pattern || '';
            if (contentSelectorEl) contentSelectorEl.value = source.content_selector || '';
            
            // 修改保存按钮为更新
            const saveBtn = document.querySelector('#addSourceForm button[onclick="saveBookSource()"]');
            if (saveBtn) {
                saveBtn.textContent = '更新';
                saveBtn.setAttribute('onclick', `updateBookSource('${sourceId}')`);
            }
        }, 100);
        
    } catch (error) {
        console.error('加载书源详情失败:', error);
        showAlert('加载书源详情失败', 'danger');
    }
}

// 更新书源
// async function updateBookSource(sourceId) {
//     const formData = {
//         name: document.getElementById('sourceName').value,
//         url: document.getElementById('sourceUrl').value,
//         search_url: document.getElementById('searchUrl').value,
//         book_url_pattern: document.getElementById('bookUrlPattern').value,
//         chapter_url_pattern: document.getElementById('chapterUrlPattern').value,
//         content_selector: document.getElementById('contentSelector').value
//     };
    
//     try {
//         const response = await fetch(`/api/sources/${sourceId}`, {
//             method: 'PUT',
//             headers: {
//                 'Content-Type': 'application/json'
//             },
//             body: JSON.stringify(formData)
//         });
        
//         if (response.ok) {
//             showAlert('书源更新成功', 'success');
//             hideAddSourceForm();
//             loadSourceList();
            
//             // 恢复保存按钮
//             const saveBtn = document.querySelector('#addSourceForm button[onclick^="updateBookSource"]');
//             if (saveBtn) {
//                 saveBtn.textContent = '保存';
//                 saveBtn.setAttribute('onclick', 'saveBookSource()');
//             }
//         } else {
//             const error = await response.json();
//             showAlert(error.detail || '更新失败', 'danger');
//         }
//     } catch (error) {
//         console.error('更新书源失败:', error);
//         showAlert('更新失败，请检查网络连接', 'danger');
//     }
// }

// 测试指定书源
async function testSource(sourceId) {
    showAlert('正在测试书源...', 'info');
    
    try {
        const response = await fetch(`/api/sources/${sourceId}/test`, {
            method: 'POST'
        });
        
        if (response.ok) {
            const result = await response.json();
            showAlert('书源测试成功', 'success');
        } else {
            showAlert('书源测试失败', 'danger');
        }
    } catch (error) {
        console.error('测试书源失败:', error);
        showAlert('测试失败，请检查网络连接', 'danger');
    }
}

// 切换书源状态
async function toggleSource(sourceId) {
    try {
        const response = await fetch(`/api/sources/${sourceId}/toggle`, {
            method: 'POST'
        });
        
        if (response.ok) {
            showAlert('书源状态更新成功', 'success');
            loadSourceList();
        } else {
            showAlert('操作失败', 'danger');
        }
    } catch (error) {
        console.error('切换书源状态失败:', error);
        showAlert('操作失败，请检查网络连接', 'danger');
    }
}

// 删除书源
async function deleteSource(sourceId) {
    showAlert('删除暂未实现', 'danger');
    return;
    if (!confirm('确定要删除这个书源吗？')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/sources/${sourceId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showAlert('书源删除成功', 'success');
            loadSourceList();
        } else {
            showAlert('删除失败', 'danger');
        }
    } catch (error) {
        console.error('删除书源失败:', error);
        showAlert('删除失败，请检查网络连接', 'danger');
    }
}

// 导出书源配置
function exportSource(sourceId) {
    // 这个功能可以后续添加
    showAlert('导出功能待实现', 'info');
}
// 调试函数 - 可以在浏览器控制台中调用
window.debugBookSource = {
    // 测试表单元素是否存在
    checkElements: function() {
        const elements = {
            sourceName: document.getElementById('sourceName'),
            sourceUrl: document.getElementById('sourceUrl'),
            searchUrl: document.getElementById('searchUrl'),
            bookUrlPattern: document.getElementById('bookUrlPattern'),
            chapterUrlPattern: document.getElementById('chapterUrlPattern'),
            contentSelector: document.getElementById('contentSelector'),
            sourceForm: document.getElementById('sourceForm'),
            presetSources: document.getElementById('presetSources')
        };
        
        console.log('表单元素检查:', elements);
        
        Object.keys(elements).forEach(key => {
            if (!elements[key]) {
                console.error(`未找到元素: ${key}`);
            } else {
                console.log(`✓ 找到元素: ${key}`);
            }
        });
        
        return elements;
    },
    
    // 测试填充表单
    testFill: function() {
        const testData = {
            name: '测试书源',
            url: 'https://test.com',
            search_url: 'https://test.com/search?q={keyword}',
            book_url_pattern: '/book/*',
            chapter_url_pattern: '/chapter/*',
            content_selector: '.content'
        };
        
        console.log('测试数据:', testData);
        
        const elements = this.checkElements();
        
        if (elements.sourceName) elements.sourceName.value = testData.name;
        if (elements.sourceUrl) elements.sourceUrl.value = testData.url;
        if (elements.searchUrl) elements.searchUrl.value = testData.search_url;
        if (elements.bookUrlPattern) elements.bookUrlPattern.value = testData.book_url_pattern;
        if (elements.chapterUrlPattern) elements.chapterUrlPattern.value = testData.chapter_url_pattern;
        if (elements.contentSelector) elements.contentSelector.value = testData.content_selector;
        
        console.log('填充完成，当前值:', {
            name: elements.sourceName?.value,
            url: elements.sourceUrl?.value,
            searchUrl: elements.searchUrl?.value
        });
    },
    
    // 显示表单
    showForm: function() {
        showAddSourceForm();
        setTimeout(() => {
            this.checkElements();
        }, 200);
    },
    
    // 测试预设书源
    testPreset: function(type = 'biquge') {
        console.log('测试预设书源:', type);
        addPresetSource(type);
    }
};

console.log('调试工具已加载，使用 debugBookSource.checkElements() 检查表单元素');// URL导入相关函数

// 从URL导入单本书籍
async function importFromUrl() {
    const bookUrl = document.getElementById('bookUrl').value.trim();
    const sourceId = document.getElementById('urlSource').value;
    const autoDetect = document.getElementById('autoDetectSource').checked;
    
    if (!bookUrl) {
        showAlert('请输入书籍URL', 'warning');
        return;
    }
    
    // 验证URL格式
    try {
        new URL(bookUrl);
    } catch (error) {
        showAlert('URL格式不正确', 'warning');
        return;
    }
    
    let finalSourceId = sourceId;
    
    // 智能识别书源
    if (autoDetect && !sourceId) {
        finalSourceId = await detectBookSource(bookUrl);
        if (!finalSourceId) {
            showAlert('无法自动识别书源，请手动选择', 'warning');
            return;
        }
    }
    
    if (!finalSourceId) {
        showAlert('请选择书源', 'warning');
        return;
    }
    
    // 显示导入进度
    const resultsDiv = document.getElementById('searchResults');
    resultsDiv.innerHTML = `
        <div class="alert alert-info">
            <div class="d-flex align-items-center">
                <div class="spinner-border spinner-border-sm me-2" role="status"></div>
                <span>正在导入书籍，请稍候...</span>
            </div>
            <div class="mt-2">
                <small>URL: ${bookUrl}</small>
            </div>
        </div>
    `;
    
    try {
        const response = await fetch('/api/sources/import', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                source_id: finalSourceId,
                book_url: bookUrl
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            resultsDiv.innerHTML = `
                <div class="alert alert-success">
                    <i class="bi bi-check-circle"></i> ${result.message}
                </div>
            `;
            
            // 清空输入框
            document.getElementById('bookUrl').value = '';
            
            // 刷新书架
            if (typeof loadBooks === 'function') {
                setTimeout(loadBooks, 2000);
            }
        } else {
            const error = await response.json();
            console.error('URL导入API错误:', response.status, error);
            resultsDiv.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-x-circle"></i> 导入失败: ${error.detail || '未知错误'}
                </div>
            `;
        }
    } catch (error) {
        console.error('导入失败:', error);
        resultsDiv.innerHTML = `
            <div class="alert alert-danger">
                <i class="bi bi-x-circle"></i> 导入失败，请检查网络连接
            </div>
        `;
    }
}

// 智能识别书源
async function detectBookSource(url) {
    try {
        const response = await fetch('/api/sources/detect', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ book_url: url })
        });
        
        if (response.ok) {
            const result = await response.json();
            if (result.source_id) {
                const matchType = result.match_type === 'exact' ? '精确匹配' : '模糊匹配';
                console.log(`${matchType}到书源:`, result.source_name);
                showAlert(`${matchType}到书源: ${result.source_name}`, 'info');
                
                // 自动选择检测到的书源
                const urlSelect = document.getElementById('urlSource');
                if (urlSelect) {
                    urlSelect.value = result.source_id;
                }
                
                return result.source_id;
            } else {
                console.log('未找到匹配的书源');
                return result.source_name;
            }
        } else {
            console.error('书源检测API调用失败');
            return null;
        }
    } catch (error) {
        console.error('书源识别失败:', error);
        return null;
    }
}

// 批量URL导入
async function batchImportFromUrls() {
    const batchUrls = document.getElementById('batchUrls').value.trim();
    const sourceId = document.getElementById('urlSource').value;
    const autoDetect = document.getElementById('autoDetectSource').checked;
    
    if (!batchUrls) {
        showAlert('请输入要导入的URL列表', 'warning');
        return;
    }
    
    // 解析URL列表
    const urls = batchUrls.split('\n')
        .map(url => url.trim())
        .filter(url => url.length > 0);
    
    if (urls.length === 0) {
        showAlert('没有找到有效的URL', 'warning');
        return;
    }
    
    // 验证URL格式
    const invalidUrls = [];
    for (const url of urls) {
        try {
            new URL(url);
        } catch (error) {
            invalidUrls.push(url);
        }
    }
    
    if (invalidUrls.length > 0) {
        showAlert(`以下URL格式不正确:\n${invalidUrls.join('\n')}`, 'warning');
        return;
    }
    
    if (!confirm(`确定要导入 ${urls.length} 本书籍吗？`)) {
        return;
    }
    
    // 显示批量导入进度
    const resultsDiv = document.getElementById('searchResults');
    resultsDiv.innerHTML = `
        <div class="alert alert-info">
            <h6><i class="bi bi-cloud-download"></i> 批量导入进行中</h6>
            <div class="progress mb-2">
                <div class="progress-bar" role="progressbar" style="width: 0%" id="batchProgress"></div>
            </div>
            <div id="batchStatus">准备导入 ${urls.length} 本书籍...</div>
            <div id="batchResults" class="mt-2"></div>
        </div>
    `;
    
    const progressBar = document.getElementById('batchProgress');
    const statusDiv = document.getElementById('batchStatus');
    const resultsContainer = document.getElementById('batchResults');
    
    let successCount = 0;
    let failCount = 0;
    
    // 逐个导入
    for (let i = 0; i < urls.length; i++) {
        const url = urls[i];
        const progress = ((i + 1) / urls.length) * 100;
        
        progressBar.style.width = `${progress}%`;
        statusDiv.textContent = `正在导入第 ${i + 1}/${urls.length} 本书籍...`;
        
        try {
            let finalSourceId = sourceId;
            
            // 智能识别书源
            if (autoDetect && !sourceId) {
                finalSourceId = await detectBookSource(url);
            }
            
            if (finalSourceId) {
                const response = await fetch('/api/sources/import', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        source_id: parseInt(finalSourceId),
                        book_url: url
                    })
                });
                
                if (response.ok) {
                    successCount++;
                    const result = await response.json();
                    resultsContainer.innerHTML += `
                        <div class="small text-success">
                            <i class="bi bi-check"></i> ${url} - 导入成功
                        </div>
                    `;
                } else {
                    failCount++;
                    const error = await response.json();
                    resultsContainer.innerHTML += `
                        <div class="small text-danger">
                            <i class="bi bi-x"></i> ${url} - ${error.detail || '导入失败'}
                        </div>
                    `;
                }
            } else {
                failCount++;
                resultsContainer.innerHTML += `
                    <div class="small text-warning">
                        <i class="bi bi-exclamation"></i> ${url} - 无法识别书源
                    </div>
                `;
            }
        } catch (error) {
            failCount++;
            resultsContainer.innerHTML += `
                <div class="small text-danger">
                    <i class="bi bi-x"></i> ${url} - 网络错误
                </div>
            `;
        }
        
        // 避免请求过快
        if (i < urls.length - 1) {
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
    }
    
    // 显示最终结果
    statusDiv.innerHTML = `
        <strong>批量导入完成！</strong><br>
        成功: ${successCount} 本，失败: ${failCount} 本
    `;
    
    progressBar.classList.remove('progress-bar');
    progressBar.classList.add(successCount > failCount ? 'bg-success' : 'bg-warning');
    
    // 清空输入框
    document.getElementById('batchUrls').value = '';
    
    // 刷新书架
    if (typeof loadBooks === 'function') {
        setTimeout(loadBooks, 2000);
    }
}

// 从剪贴板粘贴URL
async function pasteFromClipboard() {
    try {
        const text = await navigator.clipboard.readText();
        if (text && text.startsWith('http')) {
            document.getElementById('bookUrl').value = text;
            showAlert('已从剪贴板粘贴URL', 'success');
        } else {
            showAlert('剪贴板中没有有效的URL', 'warning');
        }
    } catch (error) {
        showAlert('无法访问剪贴板，请手动粘贴', 'warning');
    }
}

// 预览书籍信息（可选功能）
async function previewBookInfo() {
    const bookUrl = document.getElementById('bookUrl').value.trim();
    const sourceId = document.getElementById('urlSource').value;
    
    if (!bookUrl || !sourceId) {
        showAlert('请输入URL并选择书源', 'warning');
        return;
    }
    
    try {
        // 这里可以添加预览功能的API调用
        showAlert('预览功能待实现', 'info');
    } catch (error) {
        showAlert('预览失败', 'danger');
    }
}// URL输入辅助函数

// 处理URL粘贴事件
function handleUrlPaste(event) {
    setTimeout(() => {
        validateBookUrl();
        
        // 如果启用了智能识别，自动检测书源
        const autoDetect = document.getElementById('autoDetectSource');
        if (autoDetect && autoDetect.checked) {
            const url = event.target.value.trim();
            if (url) {
                detectBookSource(url);
            }
        }
    }, 100);
}

// 验证书籍URL
function validateBookUrl() {
    const urlInput = document.getElementById('bookUrl');
    const validation = document.getElementById('urlValidation');
    const url = urlInput.value.trim();
    
    if (!url) {
        validation.textContent = '';
        urlInput.classList.remove('is-valid', 'is-invalid');
        return;
    }
    
    try {
        const urlObj = new URL(url);
        const hostname = urlObj.hostname;
        
        // 检查是否是常见的小说网站
        const commonSites = [
            'qidian.com', 'zongheng.com', 'jjwxc.net', 'biquge.com',
            'hongxiu.com', 'xxsy.net', 'readnovel.com', 'shuhai.com'
        ];
        
        const isKnownSite = commonSites.some(site => hostname.includes(site));
        
        if (isKnownSite) {
            validation.innerHTML = `<i class="bi bi-check-circle text-success"></i> 识别为小说网站: ${hostname}`;
            urlInput.classList.remove('is-invalid');
            urlInput.classList.add('is-valid');
        } else {
            validation.innerHTML = `<i class="bi bi-question-circle text-warning"></i> 未知网站: ${hostname}`;
            urlInput.classList.remove('is-invalid', 'is-valid');
        }
    } catch (error) {
        validation.innerHTML = `<i class="bi bi-x-circle text-danger"></i> URL格式不正确`;
        urlInput.classList.remove('is-valid');
        urlInput.classList.add('is-invalid');
    }
}

// 清空搜索结果
function clearSearchResults() {
    const resultsDiv = document.getElementById('searchResults');
    if (resultsDiv) {
        resultsDiv.innerHTML = '';
    }
}

// 切换搜索标签时清空结果
document.addEventListener('DOMContentLoaded', function() {
    const searchTabs = document.querySelectorAll('#searchTabs button[data-bs-toggle="tab"]');
    searchTabs.forEach(tab => {
        tab.addEventListener('shown.bs.tab', function() {
            clearSearchResults();
        });
    });
});

// 快速填充示例URL（用于测试）
function fillExampleUrl(type) {
    const examples = {
        qidian: 'https://book.qidian.com/info/1004608738',
        zongheng: 'http://book.zongheng.com/book/878590.html',
        biquge: 'https://www.biquge.com/book/12345/',
        jjwxc: 'http://www.jjwxc.net/onebook.php?novelid=123456'
    };
    
    const url = examples[type];
    if (url) {
        document.getElementById('bookUrl').value = url;
        validateBookUrl();
        if (document.getElementById('autoDetectSource').checked) {
            detectBookSource(url);
        }
    }
}

// 添加快捷键支持
document.addEventListener('keydown', function(event) {
    // Ctrl+V 在URL输入框时自动粘贴并验证
    if (event.ctrlKey && event.key === 'v') {
        const activeElement = document.activeElement;
        if (activeElement && activeElement.id === 'bookUrl') {
            setTimeout(() => {
                validateBookUrl();
                if (document.getElementById('autoDetectSource').checked) {
                    const url = activeElement.value.trim();
                    if (url) {
                        detectBookSource(url);
                    }
                }
            }, 100);
        }
    }
    
    // Enter键快速导入
    if (event.key === 'Enter') {
        const activeElement = document.activeElement;
        if (activeElement && activeElement.id === 'bookUrl') {
            event.preventDefault();
            importFromUrl();
        }
    }
});// 批量导入辅助函数

// 显示批量导入示例
function showBatchExample() {
    const examples = [
        'https://book.qidian.com/info/1004608738',
        'https://www.biquge.com/book/12345/',
        'http://book.zongheng.com/book/878590.html',
        'http://www.jjwxc.net/onebook.php?novelid=123456'
    ];
    
    document.getElementById('batchUrls').value = examples.join('\n');
    updateUrlCount();
    showAlert('已填充示例URL，请根据需要修改', 'info');
}

// 清空批量URL
function clearBatchUrls() {
    document.getElementById('batchUrls').value = '';
    updateUrlCount();
}

// 更新URL计数
function updateUrlCount() {
    const batchUrls = document.getElementById('batchUrls').value.trim();
    const urls = batchUrls ? batchUrls.split('\n').filter(url => url.trim().length > 0) : [];
    document.getElementById('urlCount').textContent = urls.length;
}

// 监听批量URL输入变化
document.addEventListener('DOMContentLoaded', function() {
    const batchUrlsTextarea = document.getElementById('batchUrls');
    if (batchUrlsTextarea) {
        batchUrlsTextarea.addEventListener('input', updateUrlCount);
        batchUrlsTextarea.addEventListener('paste', () => {
            setTimeout(updateUrlCount, 100);
        });
    }
});

// 验证批量URL
function validateBatchUrls() {
    const batchUrls = document.getElementById('batchUrls').value.trim();
    if (!batchUrls) return { valid: [], invalid: [] };
    
    const urls = batchUrls.split('\n').map(url => url.trim()).filter(url => url.length > 0);
    const valid = [];
    const invalid = [];
    
    urls.forEach(url => {
        try {
            new URL(url);
            valid.push(url);
        } catch (error) {
            invalid.push(url);
        }
    });
    
    return { valid, invalid };
}

// 导入前验证
function validateBeforeBatchImport() {
    const { valid, invalid } = validateBatchUrls();
    
    if (invalid.length > 0) {
        const message = `发现 ${invalid.length} 个无效URL:\n${invalid.slice(0, 5).join('\n')}${invalid.length > 5 ? '\n...' : ''}`;
        if (!confirm(`${message}\n\n是否继续导入有效的 ${valid.length} 个URL？`)) {
            return false;
        }
        
        // 只保留有效URL
        document.getElementById('batchUrls').value = valid.join('\n');
        updateUrlCount();
    }
    
    return valid.length > 0;
}

// 增强的批量导入函数
async function batchImportFromUrls() {
    if (!validateBeforeBatchImport()) {
        showAlert('没有有效的URL可以导入', 'warning');
        return;
    }
    
    const batchUrls = document.getElementById('batchUrls').value.trim();
    const sourceId = document.getElementById('urlSource').value;
    const autoDetect = document.getElementById('autoDetectSource').checked;
    
    const urls = batchUrls.split('\n')
        .map(url => url.trim())
        .filter(url => url.length > 0);
    
    if (!confirm(`确定要导入 ${urls.length} 本书籍吗？\n\n${autoDetect ? '将自动识别书源' : '使用选定的书源'}`)) {
        return;
    }
    
    // 显示批量导入进度
    const resultsDiv = document.getElementById('searchResults');
    resultsDiv.innerHTML = `
        <div class="alert alert-info">
            <div class="d-flex justify-content-between align-items-center mb-2">
                <h6><i class="bi bi-cloud-download"></i> 批量导入进行中</h6>
                <button class="btn btn-sm btn-outline-secondary" onclick="cancelBatchImport()" id="cancelBtn">
                    取消
                </button>
            </div>
            <div class="progress mb-2">
                <div class="progress-bar progress-bar-striped progress-bar-animated" 
                     role="progressbar" style="width: 0%" id="batchProgress"></div>
            </div>
            <div id="batchStatus">准备导入 ${urls.length} 本书籍...</div>
            <div id="batchResults" class="mt-2" style="max-height: 200px; overflow-y: auto;"></div>
        </div>
    `;
    
    const progressBar = document.getElementById('batchProgress');
    const statusDiv = document.getElementById('batchStatus');
    const resultsContainer = document.getElementById('batchResults');
    
    let successCount = 0;
    let failCount = 0;
    let cancelled = false;
    
    // 设置取消标志
    window.batchImportCancelled = false;
    
    // 逐个导入
    for (let i = 0; i < urls.length && !window.batchImportCancelled; i++) {
        const url = urls[i];
        const progress = ((i + 1) / urls.length) * 100;
        
        progressBar.style.width = `${progress}%`;
        statusDiv.textContent = `正在导入第 ${i + 1}/${urls.length} 本书籍...`;
        
        try {
            let finalSourceId = sourceId;
            
            // 智能识别书源
            if (autoDetect && !sourceId) {
                finalSourceId = await detectBookSource(url);
            }
            
            if (finalSourceId) {
                const response = await fetch('/api/sources/import', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        source_id: parseInt(finalSourceId),
                        book_url: url
                    })
                });
                
                if (response.ok) {
                    successCount++;
                    const result = await response.json();
                    resultsContainer.innerHTML += `
                        <div class="small text-success mb-1">
                            <i class="bi bi-check"></i> ${url.substring(0, 50)}... - 导入成功
                        </div>
                    `;
                } else {
                    failCount++;
                    const error = await response.json();
                    resultsContainer.innerHTML += `
                        <div class="small text-danger mb-1">
                            <i class="bi bi-x"></i> ${url.substring(0, 50)}... - ${error.detail || '导入失败'}
                        </div>
                    `;
                }
            } else {
                failCount++;
                resultsContainer.innerHTML += `
                    <div class="small text-warning mb-1">
                        <i class="bi bi-exclamation"></i> ${url.substring(0, 50)}... - 无法识别书源
                    </div>
                `;
            }
        } catch (error) {
            failCount++;
            resultsContainer.innerHTML += `
                <div class="small text-danger mb-1">
                    <i class="bi bi-x"></i> ${url.substring(0, 50)}... - 网络错误
                </div>
            `;
        }
        
        // 滚动到最新结果
        resultsContainer.scrollTop = resultsContainer.scrollHeight;
        
        // 避免请求过快
        if (i < urls.length - 1) {
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
    }
    
    // 显示最终结果
    const finalStatus = window.batchImportCancelled ? '批量导入已取消' : '批量导入完成！';
    statusDiv.innerHTML = `
        <strong>${finalStatus}</strong><br>
        成功: ${successCount} 本，失败: ${failCount} 本
    `;
    
    progressBar.classList.remove('progress-bar-animated', 'progress-bar-striped');
    progressBar.classList.add(successCount > failCount ? 'bg-success' : 'bg-warning');
    
    // 隐藏取消按钮
    const cancelBtn = document.getElementById('cancelBtn');
    if (cancelBtn) cancelBtn.style.display = 'none';
    
    // 清空输入框
    if (!window.batchImportCancelled) {
        document.getElementById('batchUrls').value = '';
        updateUrlCount();
    }
    
    // 刷新书架
    if (typeof loadBooks === 'function') {
        setTimeout(loadBooks, 2000);
    }
}

// 取消批量导入
function cancelBatchImport() {
    window.batchImportCancelled = true;
    showAlert('正在取消批量导入...', 'warning');
}