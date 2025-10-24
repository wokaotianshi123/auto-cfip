import requests
from bs4 import BeautifulSoup # 导入 BS4 用于解析HTML
import re
import os
import base64
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

# 使用字典来存储IP和其对应的数据
# 格式: { "1.1.1.1": {"isp": "移动", "source": "ip.haogege.xyz"} }
ip_data_map = {}

# 1. 优先处理能解析运营商的网站
print("--- 开始HTML结构化解析 (带运营商) ---")
sites_with_isp = ['ip.haogege.xyz'] # 在这里添加你知道的、提供运营商信息的网站
simple_sites = []

for url in URLS:
    # 提取域名作为来源标识
    try:
        source_domain = urlparse(url).netloc
    except Exception:
        source_domain = url # 如果解析失败，使用完整URL作为备选
        
    if any(site in url for site in sites_with_isp):
        print(f"\n--- 正在处理 (HTML模式): {url} ---")
        try:
            response = requests.get(url, headers=REQUEST_HEADERS, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                rows = soup.find_all('tr')
                if not rows:
                    rows = soup.find_all('li')
                if not rows:
                    rows = soup.find_all('div')
                    
                print(f"在 {url} 找到 {len(rows)} 个可能的条目...")
                
                count = 0
                for row in rows:
                    row_text = row.get_text()
                    ip_match = ip_pattern.search(row_text)
                    
                    if ip_match:
                        ip = ip_match.group(0)
                        
                        if ip in ip_data_map:
                            continue
                            
                        # 确定运营商
                        isp = "通用" # 默认值
                        if "移动" in row_text:
                            isp = "移动"
                        elif "联通" in row_text:
                            isp = "联通"
                        elif "电信" in row_text:
                            isp = "电信"
                        
                        # 保存数据，包括来源域名
                        ip_data_map[ip] = {"isp": isp, "source": source_domain}
                        count += 1
                print(f"从 {url} 成功解析到 {count} 个新的 IP-ISP 对。")
                        
            else:
                print(f"请求 {url} 失败，状态码: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"请求 {url} 失败: {e}")
    else:
        # 如果不是带ISP的网站，先存起来
        simple_sites.append((url, source_domain)) # 把域名也存起来

# 2. 处理那些纯文本IP列表的网站
print("\n--- 开始纯文本IP列表解析 ---")
for url, source_domain in simple_sites: # 循环时带上域名
    print(f"\n--- 正在处理 (Text模式): {url} ---")
    try:
        response = requests.get(url, headers=REQUEST_HEADERS, timeout=10)
        if response.status_code == 200:
            ip_matches = ip_pattern.findall(response.text)
            count = 0
            for ip in ip_matches:
                if ip not in ip_data_map:
                    # 保存数据，包括来源域名
                    ip_data_map[ip] = {"isp": "通用", "source": source_domain}
                    count += 1
            print(f"从 {url} 成功找到 {len(ip_matches)} 个IP (新增了 {count} 个)。")
        else:
            print(f"请求 {url} 失败，状态码: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"请求 {url} 失败: {e}")
        continue

# --- 处理和保存 ---

if ip_data_map:
    # 按IP地址的数字顺序排序
    # ip_data_map.items() 会得到 [('1.1.1.1', {'isp': '移动', 'source': 'ip.haogege.xyz'}), ...]
    sorted_ip_data = sorted(
        ip_data_map.items(), 
        key=lambda item: [int(part) for part in item[0].split('.')]
    )
    
    print(f"\n成功！共找到 {len(sorted_ip_data)} 个唯一的IP地址。")
    
    # 1. 保存IP列表到 ip.txt
    with open(IP_LIST_FILE, 'w') as file:
        for ip, data in sorted_ip_data:
            file.write(ip + '\n')
            
    # 2. 生成节点链接并保存到 nodes.txt
    # 用于为每个域名单独编号
    domain_counters = {}
    
    with open(NODES_FILE, 'w', encoding='utf-8') as file:
        for ip, data in sorted_ip_data:
            # 替换IP地址
            new_node_url = VLESS_TEMPLATE.replace("ABCDEFG", ip)
            
            # 获取来源域名
            source = data['source']
            
            # 为该域名生成一个唯一的编号
            if source not in domain_counters:
                domain_counters[source] = 1
            else:
                domain_counters[source] += 1
            
            count = domain_counters[source]
            
            # 构建新的节点名称, 格式如: #ip.haogege.xyz-1
            node_name = f"#{source}-{count}"
            
            # 替换节点名称
            new_node_url = new_node_url.replace("#1", node_name)
            
            file.write(new_node_url + '\n')
    
    print(f"成功！已生成 {len(sorted_ip_data)} 个VLESS节点到 {NODES_FILE} (带来源域名信息)")

else:
    print('\n未找到任何有效的IP地址。')

