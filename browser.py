from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import time
import json
import shutil
import os
from bs4 import BeautifulSoup
from lxml import html
from os import path
from utils.env import env
from models.MusicEntry import MusicEntry
from selenium.common.exceptions import TimeoutException
from contextlib import ContextDecorator

# https://chromedriver.chromium.org/downloads
# https://selenium-python.readthedocs.io/locating-elements.html

login = env.vk_login
password = env.vk_password

class SearchHandle(ContextDecorator):
    def __init__(self, results: [], download, reset):
        self.results = results
        self.download = download
        self.reset = reset

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc, exc_tb):
        self.reset()

class Browser:

    DOWNLOAD_TAB = 0
    VK_TAB = 1
    
    _busy = False
    _download_count = 0
    _vk_music_url = None

    @property
    def isbusy(self):
        return self._busy

    def quit(self):
        self.driver.quit()

    def __init__(self):
        options = Options()
        options.headless = True

        driver = webdriver.Chrome(options=options)
        self.driver = driver

        # self.__init_vk_stuff()

    def create_room(self, video_url):
        driver = self.driver
        driver.get("https://sync-tube.de/")
        
        self.__wait_one_by_selector('a[href="create"]').click()
        settings = self.__wait_one_by_id('btnSettings')
        time.sleep(0.5) # settings are not accessed immediately somehow
        settings.click()
        time.sleep(0.5) # animation
        self.__wait_by_id('0')[3].click()
        self.__wait_one_by_className('btnClose').click()
        time.sleep(0.5) # animation

        self.__wait_one_by_className('searchInput').send_keys(video_url)
        self.__wait_one_by_className('searchInput').send_keys(Keys.ENTER)

        url = driver.current_url
        driver.get('data:,')
        return url

    def __init_vk_stuff(self):
        driver = self.driver
        driver.get("chrome://downloads/")

        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[self.VK_TAB])
        driver.get('https://vk.com/')

        driver.find_element_by_id('index_email').send_keys(login)
        driver.find_element_by_id('index_pass').send_keys(password)
        driver.find_element_by_id('index_login_button').click()
        self.__wait_one_by_id('l_aud').click()
        self.__wait_one_by_id('audio_search')
        self._vk_music_url = driver.current_url

        self.__open_audio()

    def __wait_for_download_and_rename(self):
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

        result_containers = None
        try:
            result_containers = self.__wait_by_selector('div[data-audio-context="search_global_audios"] > div', 7)
        except TimeoutException:
            return SearchHandle([], None, self.__reset)

        html = driver.page_source
        results = self.__parse_music_results(html)

        def download(index):
            download_button = result_containers[index].find_element_by_class_name('downloadButton')
            download_button.location_once_scrolled_into_view
            download_button.click()

            path = self.__wait_for_download_and_rename()
            self.__reset()
            return path
        
        return SearchHandle(results, download, self.__reset)

    def __reset(self):
        self._busy = False

    def __parse_music_results(self, html):
        soup = BeautifulSoup(html, features="lxml")
        result_containers = soup.select('div[data-audio-context="search_global_audios"] > div')
        return list(map(lambda rc: MusicEntry(
            rc.select_one('.audio_row__title_inner').text,
            rc.select_one('.audio_row__performers').text,
            rc.select_one('.audio_row__duration').text
        ), result_containers))

    def __open_audio(self):
        self.driver.get(self._vk_music_url)
        self.driver.execute_script("""
            document.getElementById('page_header_cont').style.display = 'none';
            document.getElementById('chat_onl_wrap').style.pointerEvents = 'none';
        """)

    def __wait(self, timeout): return WebDriverWait(self.driver, timeout, 0.1)
    def __wait_one_by_selector(self, selector, timeout=60): return self.__wait(timeout).until(EC.visibility_of_element_located((By.CSS_SELECTOR, selector)))
    def __wait_by_selector(self, selector, timeout=60): return self.__wait(timeout).until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, selector)))
    def __wait_one_by_xpath(self, xpath, timeout=60): return self.__wait(timeout).until(EC.visibility_of_element_located((By.XPATH, xpath)))
    def __wait_by_xpath(self, xpath, timeout=60): return self.__wait(timeout).until(EC.visibility_of_all_elements_located((By.XPATH, xpath)))
    def __wait_one_by_id(self, id, timeout=60): return self.__wait(timeout).until(EC.visibility_of_element_located((By.ID, id)))
    def __wait_by_id(self, id, timeout=60): return self.__wait(timeout).until(EC.visibility_of_all_elements_located((By.ID, id)))
    def __wait_one_by_className(self, className, timeout=60): return self.__wait(timeout).until(EC.visibility_of_element_located((By.CLASS_NAME, className)))
    def __wait_by_className(self, className, timeout=60): return self.__wait(timeout).until(EC.visibility_of_all_elements_located((By.CLASS_NAME, className)))