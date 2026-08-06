/**
 * 共享的模板模态框管理
 * 用于 my_templates.html 和 reader.html
 */

// 全局变量
let currentEditTemplateId = null;
let currentKeywords = [];
let allTemplates = [];

/**
 * 显示创建模板表单
 */
function showCreateTemplateForm(content) {
    currentEditTemplateId = null;
    currentKeywords = [];
    document.getElementById('templateModalTitle').textContent = '创建模板';
    document.getElementById('templateName').value = '';
    document.getElementById('templateContent').value = content || '';
    document.getElementById('templateTagInput').value = '';
    document.getElementById('templateDescription').value = '';
    document.getElementById('keywordsList').innerHTML = '';
    document.getElementById('tagsList').innerHTML = '';

    extractKeywords();
    showTemplateForm();
}

function showTemplateForm() {
    if (!allTemplates || allTemplates.length === 0) {
        loadTemplates();
    }

    const modal = new bootstrap.Modal(document.getElementById('templateModal'));
    modal.show();
}

/**
 * 从内容提取关键词
 */
function extractKeywords() {
    let content = document.getElementById('templateContent').value.trim();
    if (!content) return;

    const keywords = currentKeywords.filter(k => k.checked);
    if (keywords.length > 0) {
        for (const keyword of keywords) {
            content = content.replace(new RegExp(`\\{${keyword.key}\\}`, 'g'), keyword.value);
        }
        document.getElementById('templateContent').value = content;
    }

    // 综合姓氏列表（单姓 + 复姓）
    const surnames = new Set([
        '李', '王', '张', '刘', '陈', '杨', '赵', '黄', '周', '吴',
        '徐', '孙', '胡', '朱', '高', '林', '何', '郭', '马', '罗',
        '梁', '宋', '郑', '谢', '韩', '唐', '冯', '于', '董', '萧',
        '程', '曹', '袁', '邓', '许', '傅', '沈', '曾', '彭', '吕',
        '苏', '卢', '蒋', '蔡', '贾', '丁', '魏', '薛', '叶', '阎',
        '余', '潘', '杜', '戴', '夏', '钟', '汪', '田', '任', '姜',
        '范', '方', '石', '姚', '谭', '廖', '邹', '熊', '金', '陆',
        '郝', '孔', '白', '崔', '康', '毛', '邱', '秦', '江', '史',
        '顾', '侯', '邵', '孟', '龙', '万', '段', '雷', '钱', '汤',
        '尹', '黎', '易', '常', '武', '乔', '贺', '赖', '龚', '文',
        '欧阳', '司马', '上官', '司徒', '诸葛', '夏侯', '东方', '南宫'
    ]);

    function isChineseCharacters(str) {
        return /^[\u4e00-\u9fa5]+$/.test(str);
    }

    const names = new Set();
    const cleanContent = content.replace(/[\s\.,，。!！?？;；:：、（）()《》""''"“”]/g, '');

    // 预定义一些常见的非名字词语，用于过滤误识别
    const commonWords = new Set(['今天', '明天', '昨天', '我们', '你们', '他们', '这个', '那个', '这里', '那里']);
    const noendings = new Set([
        '的', '了', '在', '是', '有', '和', '就', '都', '被', '从', '以', '为', '上', '要', '出', '一', '这',
        '那', '他', '她', '它', '我', '你', '们', '什', '么', '怎', '样', '哪', '候', '地', '个', '说', '话',
        '看', '见', '听', '到', '想', '着', '了', '吗', '呢', '吧', '啊', '呀', '哦', '嗯', '与', '哼', '嘿',
        '嘻', '哈', '呵', '嘿', '咦', '哇', '哎', '唉', '哟', '喂', '喔', '噢', '嗨', '咳', '咯', '嗯', '唔',
        '嗷', '哼', '哦', '啊', '呀', '哎', '唉', '哟', '喂', '喔', '噢', '嗨', '咳', '咯', '嗯', '唔', '嗷']);

    for (let i = 0; i < cleanContent.length; i++) {
        // 检查所有可能的2-4字符组合
        for (let len = 2; len <= 4 && i + len <= cleanContent.length; len++) {
            const candidate = cleanContent.substring(i, i + len);

            // 基本验证：全中文且不在常见词语列表中
            if (!isChineseCharacters(candidate) || commonWords.has(candidate) || noendings.has(candidate[len - 1])) {
                continue;
            }

            let isValidName = false;

            if (len === 2) {
                // 2字符：单姓+单名
                const surname = candidate[0];
                if (surnames.has(surname)) {
                    isValidName = true;
                }
            } else if (len === 3) {
                // 3字符：可能是单姓+双名 或 复姓+单名
                const singleSurname = candidate[0];
                const compoundSurname = candidate.substring(0, 2);

                if (surnames.has(singleSurname) || surnames.has(compoundSurname)) {
                    isValidName = true;
                }
            } else if (len === 4) {
                // 4字符：复姓+双名
                const compoundSurname = candidate.substring(0, 2);
                if (surnames.has(compoundSurname)) {
                    isValidName = true;
                }
            }
            if (isValidName) {
                names.add(candidate);
            }
        }
    }
    let suggested_keywords = {};
    let index = 1;
    if (content.includes('我')) {
        suggested_keywords['man1'] = '我';
        index += 1;
    }
    names.forEach(name => {
        suggested_keywords['man' + index] = name;
        index += 1;
    })
    displayKeywords(suggested_keywords);
}

/**
 * 显示关键词列表
 */
function displayKeywords(suggestedKeywords, checked = false) {
    const container = document.getElementById('keywordsList');
    currentKeywords = [];

    let html = '';
    Object.entries(suggestedKeywords).forEach(([key, value]) => {
        html += `
            <div class="d-flex align-items-center mb-2">
                <input type="checkbox" class="form-check-input me-2" id="keyword_${key}" ${checked ? 'checked' : ''}
                        onchange="toggleKeyword('${key}')">
                <label class="form-check-label me-2" for="keyword_${key}">${key}:</label>
                <span class="text-primary">${value}</span>
            </div>
        `;
        currentKeywords.push({key, value, checked});
    });

    container.innerHTML = html;
}

function toggleKeyword(key) {
    const checkbox = document.getElementById(`keyword_${key}`);
    const content = document.getElementById('templateContent');

    const keyword = currentKeywords.find(k => k.key === key);
    if (!keyword) {
        return;
    }

    keyword.checked = checkbox.checked;
    const value = keyword.value;
    if (checkbox.checked) {
        // 替换内容中的文本为模板变量
        content.value = content.value.replace(new RegExp(value, 'g'), `{${key}}`);
    } else {
        // 恢复原文本
        content.value = content.value.replace(new RegExp(`\\{${key}\\}`, 'g'), value);
    }
}

function addCustomKeyword() {
    const key = document.getElementById('customKeyword').value.trim();
    const value = document.getElementById('customKeywordValue').value.trim();
    if (!value || !key) {
        showAlert('请输入关键词和文本', 'warning');
        return;
    }

    const existingKeyword = currentKeywords.find(k => k.key === key);
    if (existingKeyword) {
        if (existingKeyword.checked) {
            if (existingKeyword.value != value) {
                showAlert('已存在相同的关键词', 'warning');
            }
            return;
        }
        if (existingKeyword.value !== value) {
            existingKeyword.value = value;
            document.getElementById(`keyword_${key}`).nextElementSibling.nextElementSibling.textContent = value;
        }
        document.getElementById(`keyword_${key}`).click();
        return;
    }

    const content = document.getElementById('templateContent');
    if (content.value.includes(value)) {
        currentKeywords.push({key, value, checked: true});
        content.value = content.value.replace(new RegExp(value, 'g'), `{${key}}`);

        // 更新显示
        const container = document.getElementById('keywordsList');
        const kwditem = document.createElement('div');
        kwditem.classList.add('d-flex', 'align-items-center', 'mb-2');
        kwditem.innerHTML = `
            <input type="checkbox" class="form-check-input me-2" id="keyword_${key}" checked 
                    onchange="toggleKeyword('${key}')">
            <label class="form-check-label me-2">${key}:</label>
            <span class="text-primary">${value}</span>
        `;
        container.appendChild(kwditem);
        document.getElementById('customKeywordValue').value = '';
    } else {
        showAlert('在模板内容中未找到指定文本', 'warning');
    }
}

function clearKeywordsList() {
    const keywords = {};
    const numkeywords = [];
    currentKeywords.filter(k => k.checked).forEach(k => {
        if (k.key.startsWith('man')) {
            numkeywords.push({key: k.key, value: k.value, num: k.key.split('_')[0].replace('man', '')});
        } else {
            keywords[k.key] = k.value;
        }
    });
    if (numkeywords.length > 0) {
        numkeywords.sort((a, b) => a.num - b.num);
        numkeywords.forEach((k, i) => {
            keywords[k.key.replace(k.num, i + 1)] = k.value;
        });
    }
    displayKeywords(keywords, true);
}

function updateTagsList() {
    const tag = document.getElementById('templateTagInput').value.trim();
    const container = document.getElementById('tagsList');
    container.innerHTML += `
        <div class="d-flex align-items-center mb-2">
            <input type="checkbox" class="form-check-input me-2" value="${tag}" checked>
            <label class="form-check-label me-2">${tag}</label>
        </div>
    `;
    document.getElementById('templateTagInput').value = '';
}

function getCheckedTags() {
    const container = document.getElementById('tagsList');
    const tags = [];
    container.querySelectorAll('input[type="checkbox"]:checked').forEach(checkbox => {
        tags.push(checkbox.value);
    })
    return tags;
}

/**
 * 保存模板 (需要在各页面中实现具体逻辑)
 * 这是一个默认实现，各页面可以覆盖
 */
async function saveTemplate() {
    const name = document.getElementById('templateName').value.trim();
    const content = document.getElementById('templateContent').value.trim();
    
    if (!name || !content) {
        showAlert('请填写模板名称和内容', 'warning');
        return;
    }
    
    const description = document.getElementById('templateDescription').value.trim();
    const tags = getCheckedTags();
    const keywords = currentKeywords.filter(k => k.checked).map(k => k.key);
    
    try {
        const response = await fetch(`/api/templates/${currentEditTemplateId??''}`, {
            method: currentEditTemplateId ? 'PUT' : 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: name,
                content: content,
                keywords: keywords,
                tags: tags,
                description: description
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '保存失败');
        }
        
        showAlert(currentEditTemplateId ? '模板更新成功' : '模板创建成功', 'success');
        
        // 关闭模态框
        const modal = bootstrap.Modal.getInstance(document.getElementById('templateModal'));
        modal.hide();
        
        // 如果页面有 loadAllTemplates，调用它
        if (typeof loadAllTemplates === 'function') {
            loadAllTemplates();
        } else {
            loadTemplates();
        }
        
        return true;
        
    } catch (error) {
        console.error('保存模板失败:', error);
        showAlert('保存失败: ' + error.message, 'danger');
        return false;
    }
}

/**
 * 编辑模板
 * @param {Object} template - 模板对象
 */
function editTemplate(templateId) {
    const template = allTemplates.find(t => t.id === templateId);
    if (!template) return;

    currentEditTemplateId = template.id;
    document.getElementById('templateModalTitle').textContent = '编辑模板';
    document.getElementById('templateName').value = template.name;
    document.getElementById('templateContent').value = template.content;
    document.getElementById('templateDescription').value = template.description || '';
    
    // 显示关键词
    let keywords = {};
    template.keywords.forEach(k => {
        keywords[k] = `{${k}}`;
    });
    displayKeywords(keywords, true);

    // 显示标签
    let html = '';
    template.tags.forEach(tag => {
        html += `
            <div class="d-flex align-items-center mb-2">
                <input type="checkbox" class="form-check-input me-2" value="${tag}" checked>
                <label class="form-check-label me-2">${tag}</label>
            </div>
        `;
    });
    const container = document.getElementById('tagsList');
    container.innerHTML = html;

    showTemplateForm();
}

async function loadTemplates() {
    try {
        const response = await fetch('/api/templates/');

        if (response.ok) {
            allTemplates = await response.json();
            return allTemplates;
        }
    } catch (error) {
        console.error('加载模板失败:', error);
        return [];
    }

    return [];
}


// 导出函数供全局使用
window.TemplateModal = {
    showTemplateForm,
    showCreateTemplateForm,
    extractKeywords,
    displayKeywords,
    saveTemplate,
    loadTemplates,
    editTemplate
};
