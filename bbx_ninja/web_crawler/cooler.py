from typing import Optional, List, Union, Tuple, Dict
from pathlib import Path
from urllib.parse import urlparse
import logging
import re
import json

logger = logging.getLogger()


class Cooler:
    def __init__(self, output_dir: Optional[str] = None,
                 urls: Optional[List[str]] = None,
                 crawler_depth: Optional[int] = 0,
                 crawler_limit: Optional[int] = 1,
                 filter_urls: Optional[List[str]] = None,
                 write_to_files: Optional[bool] = False,
                 overwrite_existing_files: Optional[bool] = True):
        """
            Initialize the crawler
            urls:
            crawler_depth:
            crawler_limit:
            filter_urls:
            write_to_files: 
            overwrite_existing_files:
        """
        try:
            from webdriver_manager.chrome import ChromeDriverManager
        except ImportError:
            raise ImportError("Can't find package `webdriver-manager` \n"
                              "You can install it via `pip install webdriver-manager`")
        try:
            from selenium import webdriver
        except ImportError:
            raise ImportError("Can't find package `selenium` \n"
                              "You can install it via `pip install selenium`")

        options = webdriver.chrome.options.Options()
        options.add_argument("--headless")

        self.driver = webdriver.Chrome(
            ChromeDriverManager().install(), options=options)
        self.urls = urls
        self.output_dir = output_dir
        self.crawler_depth = crawler_depth
        self.crawler_limit = crawler_limit
        self.filter_urls = filter_urls
        self.write_to_files = write_to_files
        self.overwrite_existing_files = overwrite_existing_files

    def crawl(self, output_dir: Union[str, Path, None] = None,
              urls: Optional[List[str]] = None,
              crawler_depth: Optional[int] = None,
              crawler_limit: Optional[int] = None,
              filter_urls: Optional[List[str]] = None,
              write_to_files: Optional[int] = None,
              overwrite_existing_files: Optional[bool] = None) -> Tuple[List[dict], List[Path]]:
        """
            Crawl the website and return the text from the HTML
            output_dir:
            urls:
            crawler_depth:
            crawler_limit:
            filter_urls:
            write_to_files:
            overwrite_existing_files:
        """
        urls = urls or self.urls
        if urls is None:
            raise ValueError("Urls can't be empty.")
        output_dir = output_dir or self.output_dir
        filter_urls = filter_urls or self.filter_urls
        if write_to_files is None:
            write_to_files = self.write_to_files
        if overwrite_existing_files is None:
            overwrite_existing_files = self.overwrite_existing_files
        if crawler_depth is None:
            crawler_depth = self.crawler_depth
        if crawler_limit is None:
            crawler_limit = self.crawler_limit

        output_dir = Path(output_dir)
        if not output_dir.exists():
            output_dir.mkdir(parents=True)
        is_not_empty = len(list(output_dir.rglob("*"))) > 0
        if is_not_empty and not overwrite_existing_files:
            logger.info(f"Output folder[{output_dir}] not empty")
            return [], []
        else:
            filepaths = []
            content_list = []

            sub_links: Dict[str, List] = {}

            if crawler_depth == 0:
                # Just crawl the current page.
                result = self._write_to_files(urls, output_dir=output_dir)
                filepaths += result[0]
                content_list += result[1]
            elif crawler_depth == 1:
                # Crawl the current page and current page's links' pages.
                for url_ in urls:
                    existed_links: List = list(
                        sum(list(sub_links.values()), []))
                    sub_links[url_] = list(self._extract_sublinks_from_url(base_url=url_, filter_urls=filter_urls,
                                                                           existed_links=existed_links))
                print(f"sub_links: {sub_links}, existed_links: {existed_links}")

                for url in sub_links:
                    result = self._write_to_files(
                        sub_links[url][:crawler_limit], output_dir=output_dir, base_url=url)
                    filepaths += result[0]
                    content_list += result[1]

            return content_list, filepaths

    def _write_to_files(self, urls: List[str], output_dir: Path, base_url: str = None) -> Tuple[List[dict], List[Path]]:
        paths = []
        content_list = []
        for link in urls:
            self.driver.get(link)
            el = self.driver.find_element_by_tag_name("body")
            text = el.text

            link_split_values = link.replace("https://", "").split('/')
            file_name = f"{'_'.join(link_split_values)}.json"
            file_path = output_dir / file_name

            data = {}
            data["meta"] = {"url": link}
            if base_url:
                data["meta"]["base_url"] = base_url
            data["text"] = text
            if self.write_to_files:
                with open(file_path, 'w', encoding="utf-8") as f:
                    json.dump(data, f)
            paths.append(file_path)
            content_list.append(data)

        return paths, content_list

    @staticmethod
    def _is_internal_url(base_url: str, sub_link: str) -> bool:
        base_url_ = urlparse(base_url)
        sub_link_ = urlparse(sub_link)
        return base_url_.scheme == sub_link_.scheme and base_url_.netloc == sub_link_.netloc

    @staticmethod
    def _is_inpage_navigation(base_url: str, sub_link: str) -> bool:
        base_url_ = urlparse(base_url)
        sub_link_ = urlparse(sub_link)
        return base_url_.path == sub_link_.path and base_url_.netloc == sub_link_.netloc

    def _extract_sublinks_from_url(self, base_url: str,
                                   filter_urls: Optional[List] = None,
                                   existed_links: List = None) -> set:
        self.driver.get(base_url)
        a_elements = self.driver.find_elements_by_tag_name('a')
        sub_links = set()
        if not (existed_links and base_url in existed_links):
            if filter_urls:
                if re.compile('|'.join(filter_urls)).search(base_url):
                    sub_links.add(base_url)

        for i in a_elements:
            sub_link = i.get_attribute('href')
            if not (existed_links and sub_link in existed_links):
                if self._is_internal_url(base_url=base_url, sub_link=sub_link) \
                        and (not self._is_inpage_navigation(base_url=base_url, sub_link=sub_link)):
                    if filter_urls:
                        if re.compile('|'.join(filter_urls)).search(sub_link):
                            sub_links.add(sub_link)
                    else:
                        sub_links.add(sub_link)

        return sub_links
