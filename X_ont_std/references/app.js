// State
let activeView = "dashboard";
let selectedOrderId = "O001";
let orders = [];
let customers = [];
let products = [];

const API_BASE = `${window.location.origin}/api`;
// If you want to force localhost during development:
// const API_BASE = "http://localhost:8000/api";

// DOM Elements
const sideMenu = document.getElementById('side-menu');
const mainContent = document.getElementById('main-content');
const viewTitle = document.getElementById('view-title');
const viewDesc = document.getElementById('view-desc');
const contextBadge = document.getElementById('current-context-badge');

const views = {
    dashboard: document.getElementById('dashboard-view'),
    explorer: document.getElementById('explorer-view'),
    'ai-query': document.getElementById('ai-query-view'),
    workflow: document.getElementById('workflow-view'),
    audit: document.getElementById('audit-view')
};

// Initialization
async function init() {
    setupMenu();
    await refreshData();
    updateView();
    
    document.getElementById('ask-btn').addEventListener('click', handleAsk);
}

// API Helper
async function apiCall(endpoint, options = {}) {
    const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;
    const defaultOptions = {
        headers: { 'Content-Type': 'application/json' }
    };
    
    try {
        const response = await fetch(url, { ...defaultOptions, ...options });
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || `API Error: ${response.status}`);
        }
        return data;
    } catch (error) {
        console.error(`API Call failed to ${url}:`, error);
        throw error;
    }
}

async function refreshData() {
    try {
        const [ordersData, customersData] = await Promise.all([
            apiCall("/objects/orders"),
            apiCall("/objects/customers")
        ]);
        
        orders = ordersData;
        customers = customersData;
        
        renderPendingOrders();
        renderAllOrders();
        await updateContext();
    } catch (error) {
        showError("데이터를 가져오는 중 오류가 발생했습니다. 서버 상태를 확인하세요.");
    }
}

function showError(msg) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message fade-in';
    errorDiv.innerText = msg;
    mainContent.prepend(errorDiv);
    setTimeout(() => errorDiv.remove(), 5000);
}

// Menu handling
function setupMenu() {
    const buttons = sideMenu.querySelectorAll('.menu-item');
    buttons.forEach(btn => {
        btn.addEventListener('click', () => {
            buttons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            activeView = btn.dataset.menu;
            updateView();
        });
    });
}

function updateView() {
    Object.values(views).forEach(v => v.style.display = 'none');
    views[activeView].style.display = 'block';

    const titles = {
        dashboard: ["대시보드", "승인 대기 주문 및 주요 지표를 확인합니다."],
        explorer: ["객체 탐색", "온톨로지 내 객체와 관계를 탐색합니다."],
        'ai-query': ["AI 질의", "자연어로 데이터를 분석하고 의사결정 근거를 찾습니다."],
        workflow: ["승인 워크플로우", "주문 승인 및 반려 액션을 실행합니다."],
        audit: ["감사 로그", "시스템에서 발생한 주요 이벤트 내역을 확인합니다."]
    };

    [viewTitle.innerText, viewDesc.innerText] = titles[activeView];
    
    if (activeView === 'audit') {
        refreshAuditLogs();
    }
}

// Rendering
function renderPendingOrders() {
    const tableBody = document.querySelector('#pending-orders-table tbody');
    const pending = orders.filter(o => o.status === "Submitted");
    document.getElementById('count-pending').innerText = pending.length;

    tableBody.innerHTML = pending.map(o => `
        <tr class="clickable ${selectedOrderId === o.id ? 'active' : ''}" onclick="selectOrder('${o.id}')">
            <td>${o.id}</td>
            <td>${o.customerId}</td>
            <td>${o.amount.toLocaleString()}</td>
            <td><span class="badge badge-medium">${o.status}</span></td>
        </tr>
    `).join('');
}

function renderAllOrders() {
    const tableBody = document.querySelector('#all-orders-table tbody');
    tableBody.innerHTML = orders.map(o => `
        <tr class="clickable ${selectedOrderId === o.id ? 'active' : ''}" onclick="selectOrder('${o.id}')">
            <td>${o.id}</td>
            <td>${o.customerId}</td>
            <td>${o.amount.toLocaleString()}</td>
            <td><span class="badge ${getStatusBadge(o.status)}">${o.status}</span></td>
        </tr>
    `).join('');
}

function getStatusBadge(status) {
    if (status === 'Approved') return 'badge-low';
    if (status === 'Rejected') return 'badge-high';
    return 'badge-medium';
}

// Interaction
window.selectOrder = async function(id) {
    selectedOrderId = id;
    await updateContext();
    renderPendingOrders();
    renderAllOrders();
    
    if (activeView === 'workflow') {
        document.getElementById('wf-order-id').innerText = id;
    }
};

async function updateContext() {
    try {
        const response = await fetch(`${API_BASE}/objects/orders/${selectedOrderId}`);
        const data = await response.json();
        
        const { order, customer, products: orderProducts } = data;

        // Badge
        contextBadge.innerText = `Context: ${order.id} · ${order.status}`;
        contextBadge.className = `badge ${getStatusBadge(order.status)}`;

        // Sidebar
        document.getElementById('ctx-order-id').innerText = `Order ${order.id}`;
        document.getElementById('ctx-order-status').innerText = order.status;
        document.getElementById('ctx-order-amount').innerText = order.amount.toLocaleString();

        document.getElementById('ctx-cust-name').innerText = customer.name;
        document.getElementById('ctx-cust-risk').innerText = customer.riskTier;
        document.getElementById('ctx-cust-risk').className = `badge badge-${customer.riskTier.toLowerCase()}`;

        document.getElementById('ctx-products').innerHTML = orderProducts.map(p => `
            <div>· ${p.name} (${p.category})</div>
        `).join('');

        const wfId = document.getElementById('wf-order-id');
        if (wfId) wfId.innerText = selectedOrderId;
    } catch (error) {
        console.error("Error updating context", error);
    }
}

// AI Logic
async function handleAsk() {
    const query = document.getElementById('query-input').value;
    const responseArea = document.getElementById('ai-response-area');
    const answerText = document.getElementById('ai-answer-text');
    const evidenceList = document.getElementById('evidence-list');
    const askBtn = document.getElementById('ask-btn');

    if (!query) return;

    askBtn.classList.add('loading');
    answerText.innerText = "분석 중...";
    responseArea.style.display = 'block';

    try {
        const result = await apiCall("/ask", {
            method: "POST",
            body: JSON.stringify({ question: query, selectedOrderId })
        });

        answerText.innerHTML = `
            <p>${result.answer}</p>
            <div style="margin-top: 1rem; font-size: 0.7rem; color: var(--text-muted);">
                <strong>Trace:</strong> ${result.trace.join(' → ')}
            </div>
            ${result.available_actions.length > 0 ? `
                <div style="margin-top: 0.5rem;">
                    <strong>추천 액션:</strong> ${result.available_actions.map(a => `<span class="badge badge-low" style="margin-right: 4px;">${a}</span>`).join('')}
                </div>
            ` : ''}
        `;
        
        evidenceList.innerHTML = result.evidence.map(doc => `
            <div class="context-card" style="background: white;">
                <div class="label">${doc.title} (Score: ${doc.score})</div>
                <div style="font-size: 0.8rem; line-height: 1.4;">${doc.text}</div>
            </div>
        `).join('');
    } catch (error) {
        answerText.innerText = `분석 실패: ${error.message}`;
    } finally {
        askBtn.classList.remove('loading');
    }
}

window.executeAction = async function(action) {
    try {
        const result = await apiCall("/workflow/execute", {
            method: "POST",
            body: JSON.stringify({ orderId: selectedOrderId, action })
        });
        
        showError(`액션 완료: ${result.message}`); // Use showError as a notification too
        await refreshData();
    } catch (error) {
        showError(`액션 실패: ${error.message}`);
    }
};

window.refreshAuditLogs = async function() {
    const tableBody = document.querySelector('#audit-table tbody');
    tableBody.innerHTML = '<tr><td colspan="4">로딩 중...</td></tr>';
    
    try {
        const events = await apiCall("/audit/events");
        tableBody.innerHTML = events.reverse().map(e => `
            <tr>
                <td style="font-size: 0.7rem; color: var(--text-muted);">${new Date(e.timestamp).toLocaleString()}</td>
                <td><span class="badge badge-low">${e.user}</span></td>
                <td><span class="badge badge-medium">${e.event_type}</span></td>
                <td>${e.description}</td>
            </tr>
        `).join('');
    } catch (error) {
        tableBody.innerHTML = `<tr><td colspan="4" style="color: red;">로그 조회 실패: ${error.message}</td></tr>`;
    }
};

init();

