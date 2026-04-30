import glob

replacements = {
    '<div class="feature-icon">📊</div>': '<div class="feature-icon"><i data-lucide="bar-chart-2" style="width:32px;height:32px;color:var(--blue)"></i></div>',
    '<div class="feature-icon">🔍</div>': '<div class="feature-icon"><i data-lucide="search" style="width:32px;height:32px;color:var(--blue)"></i></div>',
    '<div class="feature-icon">🤖</div>': '<div class="feature-icon"><i data-lucide="bot" style="width:32px;height:32px;color:var(--blue)"></i></div>',
}

for file in glob.glob('f:/Rafay/resume_checker/frontend/*.html'):
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modified = False
    for old, new in replacements.items():
        if old in content:
            content = content.replace(old, new)
            modified = True
            
    if modified:
        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)
print('Emojis in index.html replaced!')
