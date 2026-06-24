import sys
import re

with open('c:\\Documents\\Project\\9study\\demo.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = re.sub(r'\s*province=[\'"][^\'"]+[\'"],', '', content)
content = re.sub(r'\s*budget_max=[0-9.]+,', '', content)

with open('c:\\Documents\\Project\\9study\\demo.py', 'w', encoding='utf-8') as f:
    f.write(content)
