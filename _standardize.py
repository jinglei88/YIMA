import os, glob, re

count = 0
for f in glob.glob(r'd:\易码\示例\*.ym'):
    with open(f, 'r', encoding='utf-8') as fh:
        content = fh.read()
    original = content
    
    # 1. 教你 → 功能
    content = content.replace('教你 ', '功能 ')
    
    # 2. 收取 → 需要
    content = content.replace(' 收取 ', ' 需要 ')
    
    # 3. 结束 → 完事 (only standalone keyword lines)
    content = re.sub(r'^(\s*)结束\s*$', r'\1完事', content, flags=re.MULTILINE)
    
    # 4. 拼接 → + (as string concat operator)
    content = content.replace(' 拼接 ', ' + ')
    
    # 5. 加上 → +
    content = content.replace(' 加上 ', ' + ')
    
    # 6. 减去 → -
    content = content.replace(' 减去 ', ' - ')
    
    # 7. 乘以 → *
    content = content.replace(' 乘以 ', ' * ')
    
    # 8. 除以 → /
    content = content.replace(' 除以 ', ' / ')
    
    # 9. 大于 → >
    content = content.replace(' 大于 ', ' > ')
    
    # 10. 小于 → <
    content = content.replace(' 小于 ', ' < ')
    
    # 11. 等于 → ==
    content = content.replace(' 等于 ', ' == ')
    
    # 12. 不等于 → !=
    content = content.replace(' 不等于 ', ' != ')
    
    # 13. 至少是 → >=
    content = content.replace(' 至少是 ', ' >= ')
    
    # 14. 最多是 → <=
    content = content.replace(' 最多是 ', ' <= ')
    
    # 15. 取余 → %
    content = content.replace(' 取余 ', ' % ')
    
    # 16. 的话 → 就 (at end of condition line, before newline)
    content = re.sub(r' 的话\s*$', ' 就', content, flags=re.MULTILINE)
    
    # 17. 不然的话 → 不然
    content = content.replace('不然的话', '不然')
    
    if content != original:
        with open(f, 'w', encoding='utf-8') as fh:
            fh.write(content)
        count += 1
        print(f'Updated: {os.path.basename(f)}')

print(f'\nDone! Updated {count} files.')
