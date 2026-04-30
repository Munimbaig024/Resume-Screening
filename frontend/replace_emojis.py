import glob

replacements = {
    '<span class="link-icon">📊</span>': '<i data-lucide="layout-dashboard" class="link-icon"></i>',
    '<span class="link-icon">📝</span>': '<i data-lucide="file-text" class="link-icon"></i>',
    '<span class="link-icon">📄</span>': '<i data-lucide="file-plus" class="link-icon"></i>',
    '<span class="link-icon">⚙️</span>': '<i data-lucide="settings" class="link-icon"></i>',
    '<span class="link-icon">🚪</span>': '<i data-lucide="log-out" class="link-icon"></i>',
    '<div class="upload-drop-icon">📄</div>': '<div class="upload-drop-icon"><i data-lucide="upload-cloud"></i></div>',
    '<span class="fi-icon">📎</span>': '<i data-lucide="paperclip" class="fi-icon"></i>',
    '<span>🔍</span>': '<i data-lucide="search" style="width:18px;height:18px"></i>',
    '<button class="ai-fab" id="aiFab" title="AI Assistant">🤖</button>': '<button class="ai-fab" id="aiFab" title="AI Assistant"><i data-lucide="bot" style="width:28px;height:28px;"></i></button>',
    '🗑': '<i data-lucide="trash-2" style="width:16px;height:16px"></i>',
    'style="width:32px;height:32px;font-size:0.9rem">✕</button>': 'style="width:32px;height:32px;font-size:0.9rem"><i data-lucide="x" style="width:16px;height:16px"></i></button>',
    '<button id="chatSendBtn">➤</button>': '<button id="chatSendBtn"><i data-lucide="send" style="width:18px;height:18px;margin-left:2px;margin-top:2px;"></i></button>',
}

for file in glob.glob('f:/Rafay/resume_checker/frontend/*.html'):
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for old, new in replacements.items():
        content = content.replace(old, new)
        
    with open(file, 'w', encoding='utf-8') as f:
        f.write(content)
print('Emojis replaced in HTML files!')

# Update main.js for the greeting emoji
main_js_path = 'f:/Rafay/resume_checker/frontend/js/main.js'
with open(main_js_path, 'r', encoding='utf-8') as f:
    js_content = f.read()

js_content = js_content.replace('dashboardGreeting.textContent = `Good ${getGreeting()}, ${firstName} 👋`;', 
                                'dashboardGreeting.innerHTML = `Good ${getGreeting()}, ${firstName} <i data-lucide="sun" style="display:inline-block; vertical-align:-3px; width:28px; height:28px; color:var(--warning)"></i>`;\n      lucide.createIcons();')

with open(main_js_path, 'w', encoding='utf-8') as f:
    f.write(js_content)

print('Emojis replaced in JS files!')
