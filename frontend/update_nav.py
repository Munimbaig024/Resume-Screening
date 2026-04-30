import glob
import os

files = [
    'f:/Rafay/resume_checker/frontend/index.html',
    'f:/Rafay/resume_checker/frontend/dashboard.html',
    'f:/Rafay/resume_checker/frontend/report.html',
    'f:/Rafay/resume_checker/frontend/history.html',
    'f:/Rafay/resume_checker/frontend/auth.html'
]

navbar_link = '<li><a href="how_it_works.html">How It Works</a></li>'
sidebar_link = '<a href="how_it_works.html" class="sidebar-link"><i data-lucide="help-circle" class="link-icon"></i> How It Works</a>'

for file_path in files:
    if not os.path.exists(file_path):
        continue
        
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Add to Navbar
    if navbar_link not in content:
        if '<ul class="navbar-links">' in content:
            nav_start = content.find('<ul class="navbar-links">')
            nav_end = content.find('</ul>', nav_start)
            if nav_end != -1:
                # Find the last </li> before the </ul>
                last_li = content.rfind('</li>', nav_start, nav_end)
                if last_li != -1:
                    insert_pos = last_li + 5
                    content = content[:insert_pos] + '\n        ' + navbar_link + content[insert_pos:]
                else:
                    content = content[:nav_end] + '\n        ' + navbar_link + '\n      ' + content[nav_end:]

    # Add to Sidebar
    if '<aside class="sidebar"' in content and sidebar_link not in content:
        sidebar_start = content.find('<aside class="sidebar"')
        # Find the first sidebar-section-title (Main)
        main_section = content.find('sidebar-section-title">Main', sidebar_start)
        if main_section != -1:
            # Find the end of this sidebar-section
            section_end = content.find('</div>', main_section)
            if section_end != -1:
                content = content[:section_end] + '        ' + sidebar_link + '\n      ' + content[section_end:]

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

print("Navigation links updated.")
