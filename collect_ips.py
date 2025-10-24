import requests
import re
import os
from urllib.parse import urlparse # 用于解析URL以获取域名

# --- 配置区 ---

# 伪装成浏览器的 Headers，解决 403 Forbidden 错误
REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
}

# 目标URL列表 (已按您的要求更新)
URLS = [
    'https://ip.164746.xyz',
    'https://cf.090227.xyz/CloudFlareYes',
    'https://api.uouin.com/cloudflare.html',
    'https://ip.haogege.xyz/',
    'https://www.wetest.vip/page/cloudflare/address_v4.html'
]

# VLESS 节点模板
VLESS_TEMPLATE = "vless://eb7638b8-3dc0-431f-8080-d0f8521d61a6@ABCDEFG:2083?encryption=none&security=tls&sni=x.yangqian.dpdns.org&alpn=h2%2Chttp%2F1.1&fp=chrome&type=ws&host=x.yangqian.dpdns.org&path=%2Fprime#1"

# 输出文件名
IP_LIST_FILE = 'ip.txt'
NODES_FILE = 'nodes.txt'

# --- 脚本主逻辑 ---

# 正则表达式用于匹配IP地址
ip_pattern = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')

# 检查并删除旧文件
for f in [IP_LIST_FILE, NODES_FILE]:
    if os.path.exists(f):
        os.remove(f)
        print(f"已删除旧文件: {f}")

# 使用字典来存储IP和其对应的精简来源 (e.g., {"1.1.1.1": "haogege"})
ip_source_map = {}

print("--- 开始爬取所有网站 (纯文本模式) ---")

for url in URLS:
    # 提取域名并精简
    short_name = url # 默认备选方案
    try:
        full_domain = urlparse(url).netloc # e.g., ip.haogege.xyz
        domain_parts = full_domain.split('.') # e.g., ['ip', 'haogege', 'xyz']
        
        # 提取二级域名 (e.g., haogege, 090227)
        if len(domain_parts) > 1:
            short_name = domain_parts[-2] # 获取倒数第二个部分
        else:
            short_name = full_domain
            
    except Exception:
        # 如果解析失败，short_name 保持为原始URL
        pass

    print(f"\n--- 正在处理: {url} (来源标识: {short_name}) ---")
    
    # 统一使用纯文本模式处理
    try:
        response = requests.get(url, headers=REQUEST_HEADERS, timeout=10)
        if response.status_code == 200:
            ip_matches = ip_pattern.findall(response.text)
            count = 0
            for ip in ip_matches:
                if ip not in ip_source_map:
                    # 保存数据，只保存精简后的来源名
                    ip_source_map[ip] = short_name
                    count += 1
            print(f"从 {url} 成功找到 {len(ip_matches)} 个IP (新增了 {count} 个)。")
        else:
            print(f"请求 {url} 失败，状态码: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"请求 {url} 失败: {e}")
        continue

# --- 处理和保存 ---

if ip_source_map:
    # 按IP地址的数字顺序排序
    # ip_source_map.items() 会得到 [('1.1.1.1', 'haogege'), ...]
    sorted_ip_data = sorted(
        ip_source_map.items(), 
        key=lambda item: [int(part) for part in item[0].split('.')]
    )
    
    print(f"\n成功！共找到 {len(sorted_ip_data)} 个唯一的IP地址。")
    
    # 1. 保存IP列表到 ip.txt
    with open(IP_LIST_FILE, 'w') as file:
        for ip, source in sorted_ip_data:
            file.write(ip + '\n')
            
    # 2. 生成节点链接并保存到 nodes.txt
    # 用于为每个域名单独编号
    domain_counters = {}
    
    with open(NODES_FILE, 'w', encoding='utf-8') as file:
        for ip, source in sorted_ip_data: # 'source' 已经是精简后的名称
            # 替换IP地址
            new_node_url = VLESS_TEMPLATE.replace("ABCDEFG", ip)
            
            # 为该域名生成一个唯一的编号
            if source not in domain_counters:
                domain_counters[source] = 1
            else:
                domain_counters[source] += 1
            
            count = domain_counters[source]
            
            # 构建新的节点名称, 格式如: #haogege-1
            node_name = f"#{source}-{count}"
            
            # 替换节点名称 (使用 urlsafe 编码处理特殊字符，以防万一)
            # URL 锚点 (#) 后的内容最好不要有特殊字符
            import urllib.parse
            safe_node_name = urllib.parse.quote(node_name)
            
            new_node_url = new_node_url.replace("#1", safe_node_name)
            
            file.write(new_node_url + '\n')
    
    print(f"成功！已生成 {len(sorted_ip_data)} 个VLESS节点到 {NODES_FILE} (带精简来源信息)")

else:
    print('\n未找到任何有效的IP地址。')

