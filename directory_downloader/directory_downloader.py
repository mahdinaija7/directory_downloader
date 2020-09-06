import asyncio
import aiohttp
import os
import re
import logging
from typing import Set
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class DDownloader:
    """ A CLASS to download http files recursivly

        url:str -> the directory link
        workers:int -> number of workers on downloading
        retries:int -> number of retries when an error occurs
        directory:str -> the directory where files will be downloaded
    """

    def __init__(self, url: str, workers: int = 5, retries: int = 5, directory: str = None):
        self.url = url
        self.workers = workers
        self.files_urls = set()
        self.retries = retries
        if not directory:
            self.directory = "./"
        else:
            self.directory = directory

    async def fetch_file_links(self, url: str = None, filter: str = None, extension: str = None) -> Set[str]:
        """ returns a set of downloadable files urls


            url:str -> the directory link
            filter:str -> regex to filter the files that matches it
            extension:str ->  specify the extension of the files you want to fetch
        """
        if not url:
            url = self.url
        res = await self._get_site_content(url)
        soup = BeautifulSoup(res, "lxml")
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if href != "/":
                if href.count("/") in [0, 1]:
                    next_url = url + href
                    if href.count("/") == 0:
                        file_name = next_url.split("/")[-1]
                        if filter:
                            matched = re.match(filter, file_name)
                            is_match = bool(matched)
                            if not is_match:
                                continue

                        if extension:
                            if not file_name.endswith(extension):
                                continue

                        logging.info(f"'{next_url}',")
                        self.files_urls.add(next_url)
                    else:
                        await self.fetch_file_links(next_url, filter=filter, extension=extension)

        return self.files_urls

    async def _get_site_content(self, url: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                text = await resp.read()
                return text.decode("utf-8")

    async def _download_file(self, session: aiohttp.ClientSession, url: str, full_directory: str):
        for i in range(self.retries):
            try:
                async with session.get(url) as response:
                    if response.status != 200:
                        response.raise_for_status()
                    logging.info("downloading", url)
                    with open(os.path.join(full_directory), "wb") as file:
                        file_content = await response.read()
                        file.write(file_content)
                    return
            except Exception as e:
                logging.warning(f"Something goes wrong trying again {url} for {i} time ")

        logging.warning(f"Could'nt Download {url}")
        raise e

    async def _start_downloads(self, session: aiohttp.ClientSession, filter: str):
        tasks = []
        for url in self.files_urls:
            download_directory = self.directory + "/".join(url.split("/")[2:-1])
            if not os.path.exists(download_directory):
                os.makedirs(download_directory)
            file_name = url.split("/")[-1]
            if filter:
                matched = re.match(filter, file_name)
                is_match = bool(matched)
                if not is_match:
                    continue
            full_directory = os.path.join(download_directory, file_name)
            task = asyncio.create_task(self._download_file(session, url, full_directory))
            tasks.append(task)
        results = await asyncio.gather(*tasks)
        return results

    async def download_files(self, urls: Set[str] = None, filter: str = None):
        """ Download multiple files

            urls:set[str]-> a set of urls files to download
            filter:str -> regex to filter the files that matches it

        """
        if urls:
            self.files_urls = urls
        connector = aiohttp.TCPConnector(limit=self.workers)
        async with aiohttp.ClientSession(connector=connector) as session:
            _ = await self._start_downloads(session, filter)
