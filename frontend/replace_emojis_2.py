import glob

replacements_html = {
    '👋': '<i data-lucide="hand" style="width:16px;height:16px;display:inline-block;vertical-align:-3px;"></i>',
    '<div class="upload-icon">📄</div>': '<div class="upload-icon"><i data-lucide="file-up" style="width:32px;height:32px;"></i></div>',
    '<span class="file-icon">📎</span>': '<span class="file-icon"><i data-lucide="paperclip" style="width:24px;height:24px;"></i></span>',
    '📋 Copy': '<i data-lucide="clipboard" style="width:16px;height:16px;display:inline-block;vertical-align:-3px;"></i> Copy',
}

for file in glob.glob('f:/Rafay/resume_checker/frontend/*.html'):
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modified = False
    for old, new in replacements_html.items():
        if old in content:
            content = content.replace(old, new)
            modified = True
            
    if modified:
        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)

# main.js
with open('f:/Rafay/resume_checker/frontend/js/main.js', 'r', encoding='utf-8') as f:
    content = f.read()

replacements_js = {
    "const m = { keyword:'🔑', achievement:'🏆', ats:'📈', soft_skills:'💬', completeness:'📋', general:'💡' };": 
    "const m = { keyword:'<i data-lucide=\"key\" style=\"width:16px;height:16px;\"></i>', achievement:'<i data-lucide=\"trophy\" style=\"width:16px;height:16px;\"></i>', ats:'<i data-lucide=\"trending-up\" style=\"width:16px;height:16px;\"></i>', soft_skills:'<i data-lucide=\"message-square\" style=\"width:16px;height:16px;\"></i>', completeness:'<i data-lucide=\"clipboard-list\" style=\"width:16px;height:16px;\"></i>', general:'<i data-lucide=\"lightbulb\" style=\"width:16px;height:16px;\"></i>' };",
    "return m[type] || '💡';": "return m[type] || '<i data-lucide=\"lightbulb\" style=\"width:16px;height:16px;\"></i>';",
    '<div style="font-size:3rem;margin-bottom:1rem">📄</div>': '<div style="margin-bottom:1rem"><i data-lucide="file-x" style="width:48px;height:48px;color:var(--muted)"></i></div>',
    '<div style="font-size:2.5rem;margin-bottom:1rem">📭</div>': '<div style="margin-bottom:1rem"><i data-lucide="inbox" style="width:40px;height:40px;color:var(--muted)"></i></div>',
    '<div style="font-size:1.75rem;margin-bottom:0.5rem">📭</div>': '<div style="margin-bottom:0.5rem"><i data-lucide="inbox" style="width:28px;height:28px;color:var(--muted)"></i></div>',
    '<div class="chat-empty-icon">💬</div>': '<div class="chat-empty-icon"><i data-lucide="message-circle" style="width:48px;height:48px;color:var(--muted)"></i></div>'
}

for old, new in replacements_js.items():
    content = content.replace(old, new)

with open('f:/Rafay/resume_checker/frontend/js/main.js', 'w', encoding='utf-8') as f:
    f.write(content)

print('Emojis replaced!')
