from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
import requests
import cv2
import numpy as np
import os
from bs4 import BeautifulSoup
import re
from selenium.common.exceptions import TimeoutException, NoSuchElementException, InvalidElementStateException


def detect_gap(bg_path, slider_path):
    """检测滑块缺口位置"""
    # 读取背景图和滑块图
    bg = cv2.imread(bg_path)
    slider = cv2.imread(slider_path)

    # 将图片转换为灰度图
    bg_gray = cv2.cvtColor(bg, cv2.COLOR_BGR2GRAY)
    slider_gray = cv2.cvtColor(slider, cv2.COLOR_BGR2GRAY)

    # 使用模板匹配
    res = cv2.matchTemplate(bg_gray, slider_gray, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

    # 计算缺口位置
    top_left = max_loc
    gap_x = top_left[0]

    return gap_x


def get_slider_images(driver):
    """获取滑块验证码图片并保存"""
    # 等待滑块验证码加载
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "sliderCaptchaDiv"))
    )

    # 获取背景图
    bg_element = driver.find_element(By.CSS_SELECTOR, "#sliderCaptchaDiv .bg-img")
    bg_url = bg_element.value_of_css_property("background-image").split('"')[1]
    bg_data = requests.get(bg_url).content
    bg_path = "captcha_bg.jpg"
    with open(bg_path, "wb") as f:
        f.write(bg_data)

    # 获取滑块图
    slider_element = driver.find_element(By.CSS_SELECTOR, "#sliderCaptchaDiv .slider-img")
    slider_url = slider_element.get_attribute("src")
    slider_data = requests.get(slider_url).content
    slider_path = "captcha_slider.jpg"
    with open(slider_path, "wb") as f:
        f.write(slider_data)

    return bg_path, slider_path


def drag_slider(driver, distance):
    """拖动滑块到指定位置"""
    # 获取滑块元素
    slider_btn = driver.find_element(By.CSS_SELECTOR, "#sliderCaptchaDiv .slider-btn")

    # 创建动作链
    actions = ActionChains(driver)

    # 点击并按住滑块
    actions.click_and_hold(slider_btn).perform()

    # 模拟人类拖动轨迹
    # 先快速拖动到目标位置附近
    actions.move_by_offset(distance - 10, 0).perform()
    time.sleep(0.2)

    # 微调位置
    actions.move_by_offset(5, 0).perform()
    time.sleep(0.1)
    actions.move_by_offset(3, 0).perform()
    time.sleep(0.1)
    actions.move_by_offset(2, 0).perform()

    # 释放滑块
    actions.release().perform()

    # 等待验证完成
    time.sleep(2)


def szu_login_selenium(username, password):
    """使用Selenium登录深圳大学统一身份认证平台并导航到公文列表页"""
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    # 提高页面加载超时时间
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30)

    try:
        # 访问登录页面
        driver.get(
            "https://authserver.szu.edu.cn/authserver/login?service=http://www1.szu.edu.cn/manage/caslogin.asp?rurl=%2Fboard%2F")

        # 等待页面完全加载
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "username"))
        )

        # 切换到账号登录
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "userNameLogin_a"))
        ).click()

        # 输入用户名 - 显式等待
        username_input = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "username"))
        )
        username_input.clear()

        # 输入用户名时逐个字符输入，模拟真实用户
        for char in username:
            username_input.send_keys(char)
            time.sleep(0.1)

        # 处理密码输入 - 多种方法备选
        password_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "password"))
        )

        # 方法1: 检查只读属性
        if password_input.get_attribute("readonly"):
            print("密码框为只读状态，使用JavaScript解除并输入")
            driver.execute_script("""
                var passInput = document.getElementById('password');
                passInput.removeAttribute('readonly');
                passInput.value = arguments[0];
            """, password)
        # 方法2: 使用JavaScript直接输入
        else:
            print("使用常规方式输入密码")
            password_input.clear()

            # 逐个字符输入密码
            for char in password:
                password_input.send_keys(char)
                time.sleep(0.1)

        # 提交登录
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "login_submit"))
        )
        login_button.click()

        # 等待登录完成
        WebDriverWait(driver, 20).until(
            EC.url_contains("www1.szu.edu.cn/board")
        )
        print("登录成功，当前URL:", driver.current_url)

        # 关键修改：点击"全部"链接进入公文列表页
        try:
            # 等待分类标签栏出现
            tags_container = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "tags"))
            )

            # 寻找分类"全部"标签（始终是第一个标签）
            all_link = WebDriverWait(tags_container, 5).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "tag"))
            )

            # 检查标签文本是否为"全部"
            if "全部" in all_link.text:
                print("找到'全部'标签")
                all_link.click()
            else:
                # 如果第一个标签不是"全部"，尝试寻找文本为"全部"的标签
                all_links = tags_container.find_elements(By.CLASS_NAME, "tag")
                for link in all_links:
                    if "全部" in link.text:
                        link.click()
                        break

            # 等待公文列表页加载完成
            WebDriverWait(driver, 10).until(
                EC.url_contains("infolist.asp")
            )
            print("已进入公文列表页，URL:", driver.current_url)
        except Exception as e:
            print("点击'全部'链接失败:", str(e))
            # 如果点击失败，尝试直接访问公文列表页
            driver.get("https://www1.szu.edu.cn/board/infolist.asp?type=0")
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table[width='100%'][cellspacing='0']"))
            )

        current_url = driver.current_url

        # 获取cookies用于Requests session
        cookies = driver.get_cookies()
        session = requests.Session()
        for cookie in cookies:
            session.cookies.set(cookie['name'], cookie['value'])

        return session, current_url

    except TimeoutException:
        print("页面加载超时")
        driver.save_screenshot("timeout_error.png")
        return None, None
    except NoSuchElementException as e:
        print(f"元素未找到: {str(e)}")
        driver.save_screenshot("element_not_found.png")
        return None, None
    except InvalidElementStateException as e:
        print(f"元素状态无效: {str(e)}")
        driver.save_screenshot("invalid_element_state.png")
        return None, None
    except Exception as e:
        print(f"登录失败: {str(e)}")
        driver.save_screenshot("general_error.png")
        return None, None
    finally:
        # 可临时注释下面行以查看浏览器状态
        # driver.quit()
        pass


def get_document_list(session, page=1):
    """获取公文列表页数据 - 彻底解决编码问题"""
    # 公文列表页的URL
    base_url = "https://www1.szu.edu.cn/board/infolist.asp"
    params = {"type": "0", "page": page}  # type=0表示全部类型

    try:
        response = session.get(
            base_url,
            params=params,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Referer": "https://www1.szu.edu.cn/board/"
            },
            timeout=15
        )

        # 使用更强大的GB18030编码处理（兼容GB2312但支持更多字符）
        response.encoding = 'gb18030'

        # 保存页面供调试 - 使用安全的二进制方式
        filename = f"szu_page_{page}.html"
        with open(filename, "wb") as f:
            f.write(response.content)
        print(f"已保存网页到 {filename}（二进制方式）")

        # 使用BeautifulSoup解析时指定编码
        soup = BeautifulSoup(response.content.decode('gb18030', errors='replace'), 'html.parser')

        # 新解析逻辑 - 根据公文列表页调整
        doc_list = []

        # 找到公文列表表格
        main_table = soup.find('table', {'width': '100%', 'border': '0', 'cellspacing': '0', 'cellpadding': '0'})

        if not main_table:
            print("未找到公文列表表格")
            return []

        # 获取所有行
        rows = main_table.find_all('tr')

        # 跳过第一行（表头）
        # 从19行开始是正式数据（调试得出）
        for i in range(19, len(rows)):
            row = rows[i]
            cells = row.find_all('td')

            # 确保有5列
            if len(cells) < 5:
                continue

            # 提取各项信息
            serial = cells[0].get_text(strip=True)
            category = cells[1].get_text(strip=True)
            department = cells[2].get_text(strip=True)

            # 标题可能有置顶标识
            title_cell = cells[3]
            title_link = title_cell.find('a')

            # 处理没有链接的情况
            if not title_link:
                continue

            title = title_link.get_text(strip=True)

            # 检查是否置顶 - 根据截图中的红色标题
            # 注意: 置顶公文在页面顶部单独列出，可能需要额外处理
            is_top = "置顶" in title_cell.get_text(strip=True) or "置顶" in title

            # 提取公文ID - 增强健壮性
            href = title_link.get('href', '')
            doc_id = ""
            url = ""

            # 使用更健壮的方式提取ID
            if href:
                # 尝试从URL中提取ID
                if "id=" in href:
                    id_match = re.search(r'id=(\d+)', href)
                    if id_match:
                        doc_id = id_match.group(1)
                    else:
                        # 如果正则匹配失败，尝试从URL中提取数字ID
                        id_match = re.search(r'(\d+)$', href)
                        if id_match:
                            doc_id = id_match.group(1)

                # 构建完整URL
                if href.startswith("http"):
                    url = href
                else:
                    # 处理可能的相对URL
                    base_path = "https://www1.szu.edu.cn/board/"
                    if href.startswith("/"):
                        url = base_path + href[1:]
                    elif href.startswith("."):
                        url = base_path + href
                    else:
                        url = base_path + href

            # 提取日期
            publish_date = ""
            try:
                # 尝试从日期列提取
                date_cell = cells[5]
                publish_date = date_cell.get_text(strip=True)

                # 如果日期为空，尝试从标题中提取
                if not publish_date:
                    # 查找标题中的日期格式 (2025-5-31)
                    date_match = re.search(r'(\d{4}-\d{1,2}-\d{1,2})', title)
                    if date_match:
                        publish_date = date_match.group(1)
            except Exception as e:
                print(f"日期提取失败: {str(e)}")
                publish_date = "日期解析失败"

            doc_list.append({
                'doc_id': doc_id,
                'serial': serial,
                'category': category,
                'department': department,
                'title': title,
                'is_top': is_top,
                'publish_date': publish_date,
                'url': url
            })

        return doc_list

    except Exception as e:
        print(f"获取公文列表失败: {str(e)}")
        import traceback
        traceback.print_exc()  # 打印详细错误信息
        return []


if __name__ == "__main__":
    import sys
    
    USERNAME = ""
    PASSWORD = ""

    # 优先从命令行参数获取
    if len(sys.argv) >= 3:
        USERNAME = sys.argv[1]
        PASSWORD = sys.argv[2]
        print(f"已从命令行参数获取账号: {USERNAME}")
    else:
        # 尝试从文件读取账号密码
        try:
            config_file = "userpsw"
            if not os.path.exists(config_file):
                config_file = "userpsw.txt"
                
            if os.path.exists(config_file):
                with open(config_file, "r", encoding="utf-8") as f:
                    lines = f.read().strip().splitlines()
                    if len(lines) >= 2:
                        USERNAME = lines[0].strip()
                        PASSWORD = lines[1].strip()
                        print(f"已从 {config_file} 读取账号: {USERNAME}")
        except Exception as e:
            print(f"读取配置文件出错: {str(e)}")

    if not USERNAME or not PASSWORD:
        print(f"用法: python {os.path.basename(__file__)} <学号> <密码>")
        print("或者确保当前目录下存在 userpsw 或 userpsw.txt 配置文件")
        exit(1)

    # 使用Selenium登录
    session, final_url = szu_login_selenium(USERNAME, PASSWORD)

    if session:
        print(f"登录成功，最终URL: {final_url}")

        # 爬取公文列表
        documents = get_document_list(session, page=1)
        print(f"获取到 {len(documents)} 条公文信息")

        # 保存到文件
        try:
            with open("gongwen.txt", "w", encoding="utf-8") as f:
                for doc in documents:
                    # 格式化每条公文信息
                    top_marker = "[置顶] " if doc.get('is_top', False) else ""
                    f.write(f"序号: {doc['serial']}\n")
                    f.write(f"标题: {top_marker}{doc['title']}\n")
                    f.write(f"类别: {doc['category']}\n")
                    f.write(f"部门: {doc['department']}\n")
                    f.write(f"日期: {doc['publish_date']}\n")
                    f.write(f"链接: {doc['url']}\n\n")

            print("公文信息已保存到 gongwen.txt 文件")
        except Exception as e:
            print(f"保存文件失败: {str(e)}")

        # 示例：打印前10条公文
        if documents:
            print("\n公文列表 (前10条):")
            for i, doc in enumerate(documents[:10]):
                top_marker = "[置顶] " if doc.get('is_top', False) else ""
                print(f"{doc['serial']}. {top_marker}{doc['title']}")
                print(f"   类别: {doc['category']}, 部门: {doc['department']}, 日期: {doc['publish_date']}")
                if doc.get('url', ''):
                    print(f"   链接: {doc['url']}\n")
    else:
        print("登录失败")