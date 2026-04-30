import glob

# Remove redundant links and buttons
# Replace type="email" with type="text" in auth.html
with open('f:/Rafay/resume_checker/frontend/auth.html', 'r', encoding='utf-8') as f:
    auth_content = f.read()

auth_content = auth_content.replace('type="email"', 'type="text"')
# Also update the placeholder
auth_content = auth_content.replace('placeholder="you@example.com"', 'placeholder="Email address (e.g. rafay@test.com)"')

with open('f:/Rafay/resume_checker/frontend/auth.html', 'w', encoding='utf-8') as f:
    f.write(auth_content)

# Clean up sidebar in all files
for file in glob.glob('f:/Rafay/resume_checker/frontend/*.html'):
    if file.endswith('index.html') or file.endswith('auth.html'):
        continue
        
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove "New Analysis" from sidebar if present
    content = content.replace('<a href="onboarding.html" class="sidebar-link"><i data-lucide="file-plus" class="link-icon"></i> New Analysis</a>', '')
    content = content.replace('<a href="onboarding.html" class="sidebar-link active"><i data-lucide="file-plus" class="link-icon"></i> New Analysis</a>', '')
    
    # Remove "Settings" from sidebar if present
    content = content.replace('<a href="#" class="sidebar-link"><i data-lucide="settings" class="link-icon"></i> Settings</a>', '')
    
    # Remove sidebarToggle button from navbar if present (as per user's "does nothing" comment)
    content = content.replace('<button class="btn btn-icon btn-secondary" id="sidebarToggle" title="Toggle Sidebar">☰</button>', '')
    content = content.replace('<button class="btn btn-icon btn-secondary" id="sidebarToggle">☰</button>', '')
    
    with open(file, 'w', encoding='utf-8') as f:
        f.write(content)

print("Auth and Sidebar cleaned up.")
