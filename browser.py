from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import json
from selenium.webdriver.chrome.options import Options
import shutil
import os
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
from lxml import html
from os import path

# https://chromedriver.chromium.org/downloads
# https://selenium-python.readthedocs.io/locating-elements.html

login = os.getenv('VK_LOGIN')
password = os.getenv('VK_PASSWORD')

class MusicEntry:
    def __init__(self, title, author, duration):
        self.title = title
        self.author = author
        self.duration = duration

class SearchResultHandle:
    def __init__(self, results: [], download, reset):
        self.results = results
        self.download = download
        self.reset = reset

class Browser:

    DOWNLOAD_TAB = 0
    VK_TAB = 1
    
    _busy = False
    _download_count = 0
    _vk_music_url = None

    @property
    def isbusy(self):
        return self._busy

    def __init__(self):
        options = Options()
        options.add_extension(r'extensions\vk_music_downloader.crx3')

        driver = webdriver.Chrome(options=options)
        self.driver = driver

        driver.get("chrome://downloads/")

        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[self.VK_TAB])
        driver.get('https://vk.com/')

        driver.find_element_by_id('index_email').send_keys(login)
        driver.find_element_by_id('index_pass').send_keys(password)
        driver.find_element_by_id('index_login_button').click()
        self.__wait_by_id('l_aud').click()
        self.__wait_by_id('audio_search')
        self._vk_music_url = driver.current_url

        self.__open_audio()

    def wait_for_download_and_rename(self):
        driver = self.driver
        driver.switch_to.window(driver.window_handles[self.DOWNLOAD_TAB])

        def chrome_downloads(drv):
            return drv.execute_script("""
                const items = document.querySelector('downloads-manager').shadowRoot.querySelector('#downloadsList').items;
                const completed = items.filter(e => e.state === 'COMPLETE');
                if (items.length !== %d && items.length === completed.length) {
                    const i = items[0]
                    return i.filePath || i.file_path || i.fileUrl || i.file_url;
                }
            """ % self._download_count)

        file_path = WebDriverWait(driver, 60).until(chrome_downloads)
        self._download_count += 1
        driver.switch_to.window(driver.window_handles[self.VK_TAB])
        return file_path

    def search(self, query: str):
        while (self._busy):
            time.sleep(0.1)
        self._busy = True
        self.__open_audio()

        driver = self.driver
        search = driver.find_element_by_id('audio_search')

        search.send_keys(query)
        search.send_keys(Keys.ENTER)

        result_container_selector = 'div[data-audio-context="search_global_audios"] > div'
        self.__wait_by_selector(result_container_selector)

        html = driver.page_source
        results = self.parse_music_results(html)

        def reset():
            driver.get(self._vk_music_url)
            self.disable_stuff()
            self._busy = False

        def download(index):
            result_containers = driver.find_elements_by_css_selector(result_container_selector)
            download_button = result_containers[index].find_element_by_class_name('downloadButton')
            download_button.click()

            path = self.wait_for_download_and_rename()
            reset()
            return path
        
        return SearchResultHandle(results, download, reset)

    def parse_music_results(self, html):
        soup = BeautifulSoup(html, features="lxml")
        result_containers = soup.select('div[data-audio-context="search_global_audios"] > div')
        return list(map(lambda rc: MusicEntry(
            rc.select_one('.audio_row__title_inner').text,
            rc.select_one('.audio_row__performers').text,
            rc.select_one('.audio_row__duration').text
        ), result_containers))

    def disable_stuff(self):
        self.driver.execute_script("""
            document.getElementById('chat_onl_wrap').style.pointerEvents = 'none';
            document.getElementById('page_header_cont').style.pointerEvents = 'none';
        """)

    def quit(self):
        self.driver.quit()

    def __open_audio(self):
        self.driver.get(self._vk_music_url)
        self.disable_stuff()

    def __wait(self): return WebDriverWait(self.driver, 60, 0.1)
    def __wait_by_selector(self, selector): return self.__wait().until(EC.visibility_of_element_located((By.CSS_SELECTOR, selector)))
    def __wait_by_xpath(self, xpath): return self.__wait().until(EC.visibility_of_element_located((By.XPATH, xpath)))
    def __wait_by_id(self, id): return self.__wait().until(EC.visibility_of_element_located((By.ID, id)))
    def __wait_by_className(self, className): return self.__wait().until(EC.visibility_of_element_located((By.CLASS_NAME, className)))