import os, glob

lucide_script = '<script src="https://unpkg.com/lucide@latest"></script>'
init_script = '''<script>
    lucide.createIcons();
  </script>
</body>'''

for file in glob.glob('f:/Rafay/resume_checker/frontend/*.html'):
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace gemini logo
    content = content.replace('<span class="logo-icon">✦</span>', '')

    # Add lucide
    if lucide_script not in content:
        content = content.replace('</head>', f'  {lucide_script}\n</head>')
    
    if 'lucide.createIcons();' not in content:
        content = content.replace('</body>', init_script)
        
    with open(file, 'w', encoding='utf-8') as f:
        f.write(content)
print('Done!')
