// RAG 策略配置页面 JavaScript

// 策略改变时显示/隐藏权重配置
document.getElementById('retrieval-strategy').addEventListener('change', function() {
    const weightConfig = document.getElementById('weight-config');
    const strategy = this.value;

    // 只在混合检索策略下显示权重配置
    if (strategy === 'hybrid' || strategy === 'hybrid_rerank') {
        weightConfig.style.display = 'block';
    } else {
        weightConfig.style.display = 'none';
    }
});

// 权重滑块实时更新
document.getElementById('vector-weight').addEventListener('input', function() {
    document.getElementById('vector-weight-value').textContent = this.value;
    // 自动更新另一个权重，保持总和为1
    const bm25Weight = (1 - parseFloat(this.value)).toFixed(1);
    document.getElementById('bm25-weight').value = bm25Weight;
    document.getElementById('bm25-weight-value').textContent = bm25Weight;
});

document.getElementById('bm25-weight').addEventListener('input', function() {
    document.getElementById('bm25-weight-value').textContent = this.value;
    // 自动更新另一个权重，保持总和为1
    const vectorWeight = (1 - parseFloat(this.value)).toFixed(1);
    document.getElementById('vector-weight').value = vectorWeight;
    document.getElementById('vector-weight-value').textContent = vectorWeight;
});

// 分类问题
async function classifyQuery() {
    const query = document.getElementById('query-input').value.trim();
    const resultBox = document.getElementById('classification-result');

    if (!query) {
        showError(resultBox, '请输入问题');
        return;
    }

    resultBox.innerHTML = '<div class="loading"></div> 正在分类...';

    try {
        const response = await fetch('/api/rag/classify', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: query })
        });

        const data = await response.json();

        if (data.status === 'success') {
            const result = data.result;

            // 显示分类结果
            const typeLabels = {
                'concept': '概念型',
                'process': '流程型',
                'compare': '对比型',
                'factual': '事实型',
                'rule': '规则型',
                'troubleshooting': '故障排查',
                'general': '通用型'
            };

            let html = `<div class="success">`;
            html += `<strong>问题类型:</strong> ${typeLabels[result.type] || result.type}<br>`;
            html += `<strong>置信度:</strong> ${(result.confidence * 100).toFixed(1)}%<br>`;
            html += `<strong>分类原因:</strong> ${result.reason}<br>`;
            html += `</div>`;

            resultBox.innerHTML = html;
        } else {
            showError(resultBox, data.error || '分类失败');
        }
    } catch (error) {
        showError(resultBox, '网络错误: ' + error.message);
    }
}

// 执行检索
async function executeRetrieve() {
    const query = document.getElementById('query-input').value.trim();
    const strategy = document.getElementById('retrieval-strategy').value;
    const topK = parseInt(document.getElementById('top-k').value);
    const resultBox = document.getElementById('retrieval-result');

    if (!query) {
        showError(resultBox, '请输入问题');
        return;
    }

    resultBox.innerHTML = '<div class="loading"></div> 正在检索...';

    try {
        const response = await fetch('/api/rag/retrieve', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                strategy: strategy,
                top_k: topK
            })
        });

        const data = await response.json();

        if (data.status === 'success') {
            const result = data.result;

            // 显示检索结果
            let html = '';
            if (result.summary) {
                html += `<pre>${result.summary}</pre>`;
            }

            if (result.verbose) {
                html += '<div style="margin-top: 15px; padding: 10px; background: #e7f3ff; border-radius: 5px;">';
                html += `<strong>检索详情:</strong><br>`;
                html += `问题类型: ${result.verbose.question_type}<br>`;
                html += `策略: ${result.verbose.strategy_selected}<br>`;
                html += `方法: ${result.verbose.method_used}<br>`;
                html += `文档数: ${result.verbose.documents_retrieved}<br>`;
                html += `</div>';
            }

            resultBox.innerHTML = html;
        } else {
            showError(resultBox, data.error || '检索失败');
        }
    } catch (error) {
        showError(resultBox, '网络错误: ' + error.message);
    }
}

// 对比不同检索方法
async function compareMethods() {
    const query = document.getElementById('query-input').value.trim();
    const topK = parseInt(document.getElementById('top-k').value);
    const resultBox = document.getElementById('compare-result');

    if (!query) {
        showError(resultBox, '请输入问题');
        return;
    }

    resultBox.innerHTML = '<div class="loading"></div> 正在对比...';

    try {
        const response = await fetch('/api/rag/compare', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                top_k: topK
            })
        });

        const data = await response.json();

        if (data.status === 'success') {
            const result = data.result;

            // 显示对比结果
            let html = '';
            if (result.summary) {
                html += `<pre>${result.summary}</pre>`;
            }

            resultBox.innerHTML = html;
        } else {
            showError(resultBox, data.error || '对比失败');
        }
    } catch (error) {
        showError(resultBox, '网络错误: ' + error.message);
    }
}

// 批量测试
async function batchTest() {
    const queriesText = document.getElementById('batch-queries').value.trim();
    const resultBox = document.getElementById('batch-result');

    if (!queriesText) {
        showError(resultBox, '请输入测试问题列表（每行一个问题）');
        return;
    }

    const queries = queriesText.split('\n').filter(q => q.trim());

    if (queries.length === 0) {
        showError(resultBox, '至少需要一个问题');
        return;
    }

    resultBox.innerHTML = '<div class="loading"></div> 正在批量测试...';

    try {
        const response = await fetch('/api/rag/batch', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                queries: queries,
                strategy: 'auto'
            })
        });

        const data = await response.json();

        if (data.status === 'success') {
            const result = data.result;

            // 显示批量测试结果
            let html = '';
            if (result.summary) {
                html += `<pre>${result.summary}</pre>`;
            }

            resultBox.innerHTML = html;
        } else {
            showError(resultBox, data.error || '批量测试失败');
        }
    } catch (error) {
        showError(resultBox, '网络错误: ' + error.message);
    }
}

// 获取统计信息
async function getStatistics() {
    const queriesText = document.getElementById('batch-queries').value.trim();
    const resultBox = document.getElementById('statistics-result');

    if (!queriesText) {
        showError(resultBox, '请输入测试问题列表（每行一个问题）');
        return;
    }

    const queries = queriesText.split('\n').filter(q => q.trim());

    if (queries.length === 0) {
        showError(resultBox, '至少需要一个问题');
        return;
    }

    resultBox.innerHTML = '<div class="loading"></div> 正在统计...';

    try {
        const response = await fetch('/api/rag/statistics', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                queries: queries
            })
        });

        const data = await response.json();

        if (data.status === 'success') {
            const result = data.result;

            // 显示统计结果
            let html = '';
            if (result.summary) {
                html += `<pre>${result.summary}</pre>`;
            }

            resultBox.innerHTML = html;
        } else {
            showError(resultBox, data.error || '统计失败');
        }
    } catch (error) {
        showError(resultBox, '网络错误: ' + error.message);
    }
}

// 显示错误
function showError(container, message) {
    container.innerHTML = `<div class="error">${message}</div>`;
}

// 显示成功
function showSuccess(container, message) {
    container.innerHTML = `<div class="success">${message}</div>`;
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 初始化权重配置显示状态
    const weightConfig = document.getElementById('weight-config');
    weightConfig.style.display = 'none';

    console.log('RAG 策略配置页面已加载');
});
