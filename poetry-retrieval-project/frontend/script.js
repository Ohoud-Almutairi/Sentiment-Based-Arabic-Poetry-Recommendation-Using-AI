
const API_URL = 'http://localhost:5000';

// Get elements
const userInput = document.getElementById('userInput');
const analyzeBtn = document.getElementById('analyzeBtn');
const clearBtn = document.getElementById('clearBtn');
const loading = document.getElementById('loading');
const error = document.getElementById('error');
const result = document.getElementById('result');


// Event Listeners

analyzeBtn.addEventListener('click', analyzeText);
clearBtn.addEventListener('click', () => {
    userInput.value = '';
    result.style.display = 'none';
    error.style.display = 'none';
});

userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        analyzeText();
    }
});


// Main Function
async function analyzeText() {
    const text = userInput.value.trim();
    
    // Clear previous results
    result.style.display = 'none';
    error.style.display = 'none';
    
    // Validate
    if (!text) {
        showError('الرجاء إدخال نص للتحليل');
        return;
    }
    
    if (text.length < 3) {
        showError('النص قصير جداً');
        return;
    }
    
    // Show loading
    loading.style.display = 'block';
    analyzeBtn.disabled = true;
    
    try {
        const response = await fetch(`${API_URL}/get-poetry`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });
        
        if (!response.ok) throw new Error('فشل الاتصال بالخادم');
        
        const data = await response.json();
        displayResults(data);
        result.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        
    } catch (err) {
        showError('حدث خطأ: تأكد من تشغيل الخادم');
        console.error(err);
    } finally {
        loading.style.display = 'none';
        analyzeBtn.disabled = false;
    }
}


// Display Functions
function displayResults(data) {
    const emotionArabic = {
        'joy': 'فرح',
        'love': 'حب',
        'sad': 'حزن'
    };
    
    result.innerHTML = `
        <div class="emotion-section">
            <h2> المشاعر المكتشفة</h2>
            <div class="emotion-card">
                <div class="emotion-main">
                    <span class="emotion-label">المشاعر:</span>
                    <span class="emotion-value ${data.emotion}">${emotionArabic[data.emotion] || data.emotion}</span>
                </div>
                <div class="confidence">
                    <span class="confidence-label">نسبة الثقة:</span>
                    <span class="confidence-value">${(data.confidence * 100).toFixed(1)}%</span>
                </div>
            </div>
            
            <div class="all-emotions">
                <h3> جميع المشاعر:</h3>
                <div class="emotion-bars">
                    ${Object.entries(data.all_probabilities)
                        .sort((a, b) => b[1] - a[1])
                        .map(([emotion, prob]) => `
                            <div class="emotion-bar-container">
                                <div class="emotion-bar-label">
                                    <span>${emotionArabic[emotion] || emotion}</span>
                                    <span>${(prob * 100).toFixed(1)}%</span>
                                </div>
                                <div class="emotion-bar-bg">
                                    <div class="emotion-bar-fill ${emotion}" style="width: ${(prob * 100).toFixed(1)}%"></div>
                                </div>
                            </div>
                        `).join('')}
                </div>
            </div>
        </div>
        
        <div class="poetry-section">
            <h2> القصيدة المناسبة لك</h2>
            ${data.poetry.length > 0 ? `
                <div class="poetry-cards">
                    <div class="poetry-card">
                        <div class="poetry-text">${escapeHtml(data.poetry[0].text)}</div>
                    </div>
                </div>
            ` : '<p style="text-align:center; color: #8C7355;">لا توجد أشعار متاحة</p>'}
        </div>
    `;
    
    result.style.display = 'block';
}

function showError(message) {
    error.innerHTML = `<div class="error-message">⚠️ ${message}</div>`;
    error.style.display = 'block';
    setTimeout(() => error.style.display = 'none', 5000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}


// Check API on Load
window.addEventListener('load', async () => {
    try {
        const response = await fetch(`${API_URL}/health`);
        if (response.ok) {
            console.log('✓ API connected');
        } else {
            showError('تحذير: الخادم قد لا يكون متاحاً');
        }
    } catch {
        showError('تعذر الاتصال بالخادم');
    }
});