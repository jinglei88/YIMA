import re
import os

files_to_update = [
    r'd:\易码\文档\语言规范.md',
    r'd:\易码\文档\开发指南.md'
]

for filepath in files_to_update:
    if not os.path.exists(filepath):
        continue
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Text replacements in code snippets / documentation
    
    # Fix the reference table in language spec
    content = content.replace('| `说` / `显示` | 输出内容 | `说 "你好"` |', '| `说` / `显示` | 输出内容 | `显示 "你好"` |')
    content = content.replace('| `让` | 极简赋值 | `让 名字 = "张三"` |', '| `让` (已弃用) | 极简赋值 | `名字 = "张三"` |')
    content = content.replace('| `结束` | 代码块收尾 | `结束` |', '| `结束` / `完事` | 代码块收尾 | `完事` |')
    
    # Generic replacements in code blocks
    content = content.replace('说 ', '显示 ')
    content = content.replace('说"', '显示"')
    content = content.replace(' 结束\n', ' 完事\n')
    content = content.replace('\n结束\n', '\n完事\n')
    
    # Let assignments
    content = content.replace('让 玩家血量 = 100', '玩家血量 = 100')
    content = content.replace('让 名字 = "林克"', '名字 = "林克"')
    content = content.replace('让 回答 = 问 "你叫什么名字？"', '回答 = 问 "你叫什么名字？"')
    content = content.replace('让 名字 = "小明"', '名字 = "小明"')
    content = content.replace('让 水果 = ["苹果", "香蕉", "橘子"]', '水果 = ["苹果", "香蕉", "橘子"]')
    content = content.replace('让 面积 = 算面积(5, 4)', '面积 = 算面积(5, 4)')
    content = content.replace('让 结果 = 数学库.sin(3.14159 / 2)', '结果 = 数学库.sin(3.14159 / 2)')
    content = content.replace('让 购物车 = ["苹果", "牛奶"]', '购物车 = ["苹果", "牛奶"]')
    content = content.replace('让 数字们 = 新列表(10, 20, 30)', '数字们 = 新列表(10, 20, 30)')
    content = content.replace('让 资料 = {"名字": "张三", "年龄": 18}', '资料 = {"名字": "张三", "年龄": 18}')
    content = content.replace('让 小说 = "这是一本好书"', '小说 = "这是一本好书"')
    content = content.replace('让 内容 = 读文件("乱写的路径.txt")', '内容 = 读文件("乱写的路径.txt")')
    
    # Comparisons & Operations
    content = content.replace(' 至少是 ', ' >= ')
    content = content.replace(' 大于 ', ' > ')
    content = content.replace(' 小于 ', ' < ')
    content = content.replace(' 等于 ', ' == ')
    content = content.replace(' 加上 ', ' + ')
    content = content.replace(' 拼接 ', ' + ')
    
    # Conditional suffixes
    content = content.replace(' 的话\n', ' 就\n')
    content = content.replace(' 不然的话\n', ' 不然\n')
    content = content.replace(' 的时候\n', ' 的时候\n') # keep this one as is, it's fine for loops
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {os.path.basename(filepath)}")
        
print("Doc updates complete.")
