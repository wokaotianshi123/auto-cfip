import requests
from bs4 import BeautifulSoup  # 尽管导入了，但未使用，可以保留
import re
import os
import base64

# --- 配置区 ---

# 目标URL列表
#
# --- 如何排查问题 ---
# 如果您怀疑某个网站的数据有问题，可以在对应的URL行首添加一个 # 号来“注释掉”它。
# 这样脚本在运行时就会跳过这一行，您就可以逐个排查了。
#
# 示例：
# # 'https://ip.164746.xyz',  <-- 这一行被注释掉了，脚本不会爬取它
#   'https://cf.090227.xyz/CloudFlareYes', <-- 这一行会正常爬取
#
URLS = [
    'https://ip.164746.xyz',
    'https://cf.090227.xyz/CloudFlareYes',
    'https://stock.hostmonit.com/CloudFlareYes',
    'https://ip.haogege.xyz/',
    # 'https://www.wetest.vip/page/edgeone/address_v4.html', # <-- 已根据您的要求注释掉 (无效)
    # 'https://www.wetest.vip/page/cloudfront/address_v4.html', # <-- 已根据您的要求注释掉 (无效)
    'https://www.wetest.vip/page/cloudflare/address_v4.html'
]

# VLESS 节点模板
# ABCDEFG 将被替换为IP, #1 将被替换为节点名称
VLESS_TEMPLATE = "vless://eb7638b8-3dc0-431f-8080-d0f8521d61a6@ABCDEFG:2083?encryption=none&security=tls&sni=x.yangqian.dpdns.org&alpn=h2%2Chttp%2F1.1&fp=chrome&type=ws&host=x.yangqian.dpdns.org&path=%2Fprime#1"

# 输出文件名
IP_LIST_FILE = 'ip.txt'
NODES_FILE = 'nodes.txt'
# SUBSCRIPTION_FILE = 'sub.txt' # <-- 已根据您的要求移除

# --- 脚本主逻辑 ---

# 正则表达式用于匹配IP地址
ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'

# 检查并删除旧文件，确保每次都是全新的
# for f in [IP_LIST_FILE, NODES_FILE, SUBSCRIPTION_FILE]: # <-- 旧代码
for f in [IP_LIST_FILE, NODES_FILE]: # <-- 修改后: 移除 sub.txt
    if os.path.exists(f):
        os.remove(f)
        print(f"已删除旧文件: {f}")

# 使用集合存储IP地址实现自动去重
unique_ips = set()

print("开始从URL抓取IP...")
for url in URLS:
    # 新增: 打印当前正在处理的URL，方便调试
    print(f"\n--- 正在处理: {url} ---")
    try:
        # 发送HTTP请求获取网页内容
        response = requests.get(url, timeout=5)
        
        # 确保请求成功
        if response.status_code == 200:
            # 获取网页的文本内容
            html_content = response.text
            
            # 使用正则表达式查找IP地址
            ip_matches = re.findall(ip_pattern, html_content, re.IGNORECASE)
            
            # 将找到的IP添加到集合中（自动去重）
            unique_ips.update(ip_matches)
            # 修改: 打印从当前URL找到了多少IP
            print(f"从 {url} 成功找到 {len(ip_matches)} 个IP。")
        else:
            print(f"请求 {url} 失败，状态码: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"请求 {url} 失败: {e}")
        continue

# --- 处理和保存 ---

if unique_ips:
    # 按IP地址的数字顺序排序（非字符串顺序）
    sorted_ips = sorted(unique_ips, key=lambda ip: [int(part) for part in ip.split('.')])
    
    # 1. 保存IP列表到 ip.txt
    with open(IP_LIST_FILE, 'w') as file:
        for ip in sorted_ips:
            file.write(ip + '\n')
    print(f"\n成功！已保存 {len(sorted_ips)} 个唯一IP地址到 {IP_LIST_FILE}")

    # 2. 生成节点链接列表
    all_nodes = []
    for i, ip in enumerate(sorted_ips):
        # 替换IP地址
        new_node_url = VLESS_TEMPLATE.replace("ABCDEFG", ip)
        # 替换节点名称 (例如: #1 替换为 #CF-优选-1)
        new_node_url = new_node_url.replace("#1", f"#CF-优选-{i+1}")
        all_nodes.append(new_node_url)
    
    # 将节点列表连接成一个字符串，供后续两个文件使用
    subscription_content = "\n".join(all_nodes)
    
    # 3. 保存原始节点链接到 nodes.txt
    with open(NODES_FILE, 'w', encoding='utf-8') as file:
        file.write(subscription_content)
    print(f"成功！已生成 {len(all_nodes)} 个VLESS节点到 {NODES_FILE}")

    # 4. 生成并保存【未编码】订阅文件到 sub.txt (此功能已移除)
    # (原Base64编码步骤已被移除)
    # encoded_subscription = base64.b64encode(subscription_content.encode('utf-8')).decode('utf-8')
    
    # with open(SUBSCRIPTION_FILE, 'w', encoding='utf-8') as file:
    #     file.write(subscription_content) # <-- 直接写入未编码的字符串
    # print(f"成功！已生成【未编码】订阅文件到 {SUBSCRIPTION_FILE}")

else:
    print('\n未找到任何有效的IP地址。')

