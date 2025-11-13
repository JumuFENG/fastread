/**
 * Token管理器
 * 负责token的验证、刷新和过期检查
 */

// Token刷新配置
const TOKEN_REFRESH_DAYS_BEFORE_EXPIRY = 3; // 过期前3天开始刷新
const TOKEN_CHECK_INTERVAL = 60 * 60 * 1000; // 每小时检查一次 (毫秒)

// 初始化token管理器
function initTokenManager() {
    // 页面加载时检查token
    checkAndRefreshToken();
    
    // 定期检查token
    setInterval(checkAndRefreshToken, TOKEN_CHECK_INTERVAL);
    
    // 页面可见性变化时检查token
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) {
            checkAndRefreshToken();
        }
    });
}

// 检查token是否过期
function isTokenExpired() {
    const token = localStorage.getItem('token');
    const expiresAt = localStorage.getItem('token_expires_at');
    
    if (!token || !expiresAt) {
        return true;
    }
    
    const expirationTime = new Date(expiresAt);
    const now = new Date();
    
    return now >= expirationTime;
}

// 检查token是否即将过期（3天内）
function isTokenExpiringSoon() {
    const expiresAt = localStorage.getItem('token_expires_at');
    const rememberMe = localStorage.getItem('remember_me') === 'true';
    
    if (!expiresAt || !rememberMe) {
        return false;
    }
    
    const expirationTime = new Date(expiresAt);
    const now = new Date();
    const daysUntilExpiry = (expirationTime - now) / (1000 * 60 * 60 * 24);
    
    return daysUntilExpiry <= TOKEN_REFRESH_DAYS_BEFORE_EXPIRY && daysUntilExpiry > 0;
}

// 刷新token
async function refreshToken() {
    const token = localStorage.getItem('token');
    
    if (!token) {
        return false;
    }
    
    try {
        const response = await fetch('/api/auth/refresh', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            
            // 更新存储的token信息
            localStorage.setItem('token', data.access_token);
            localStorage.setItem('token_expires_at', data.expires_at);
            localStorage.setItem('remember_me', data.remember_me.toString());
            
            console.log('Token已自动刷新，新的过期时间:', data.expires_at);
            return true;
        } else {
            console.error('Token刷新失败');
            return false;
        }
    } catch (error) {
        console.error('Token刷新出错:', error);
        return false;
    }
}

// 检查并刷新token
async function checkAndRefreshToken() {
    // 如果token已过期，跳转到登录页
    if (isTokenExpired()) {
        handleTokenExpired();
        return;
    }
    
    // 如果token即将过期且用户选择了记住我，自动刷新
    if (isTokenExpiringSoon()) {
        console.log('Token即将过期，尝试自动刷新...');
        const refreshed = await refreshToken();
        
        if (!refreshed) {
            console.warn('Token自动刷新失败');
        }
    }
}

// 处理token过期
function handleTokenExpired() {
    console.log('Token已过期，清除登录信息');
    
    // 清除所有登录相关信息
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    localStorage.removeItem('token_expires_at');
    localStorage.removeItem('remember_me');
    
    // 如果不在登录页面，跳转到登录页
    if (!window.location.pathname.includes('/auth')) {
        // 保存当前页面URL，登录后可以返回
        const returnUrl = window.location.pathname + window.location.search;
        localStorage.setItem('return_url', returnUrl);
        
        // 显示提示信息
        if (typeof showAlert === 'function') {
            showAlert('登录已过期，请重新登录', 'warning');
        }
        
        // 延迟跳转，让用户看到提示
        setTimeout(() => {
            window.location.href = '/auth';
        }, 1500);
    }
}

// 获取token剩余有效时间（天数）
function getTokenRemainingDays() {
    const expiresAt = localStorage.getItem('token_expires_at');
    
    if (!expiresAt) {
        return 0;
    }
    
    const expirationTime = new Date(expiresAt);
    const now = new Date();
    const remainingMs = expirationTime - now;
    
    return Math.max(0, remainingMs / (1000 * 60 * 60 * 24));
}

// 格式化token过期时间
function formatTokenExpiration() {
    const expiresAt = localStorage.getItem('token_expires_at');
    
    if (!expiresAt) {
        return '未知';
    }
    
    const expirationTime = new Date(expiresAt);
    return expirationTime.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// 手动刷新token（供用户主动调用）
async function manualRefreshToken() {
    if (isTokenExpired()) {
        if (typeof showAlert === 'function') {
            showAlert('Token已过期，请重新登录', 'danger');
        }
        handleTokenExpired();
        return false;
    }
    
    const refreshed = await refreshToken();
    
    if (refreshed) {
        if (typeof showAlert === 'function') {
            showAlert('Token已刷新', 'success');
        }
        return true;
    } else {
        if (typeof showAlert === 'function') {
            showAlert('Token刷新失败', 'danger');
        }
        return false;
    }
}

// 页面加载时初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTokenManager);
} else {
    initTokenManager();
}

// 导出函数供其他脚本使用
window.TokenManager = {
    isTokenExpired,
    isTokenExpiringSoon,
    refreshToken,
    checkAndRefreshToken,
    handleTokenExpired,
    getTokenRemainingDays,
    formatTokenExpiration,
    manualRefreshToken
};
