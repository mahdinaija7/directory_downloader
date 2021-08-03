import asyncio
import os
import re
import aiohttp
from typing import Set, List, Union
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup, SoupStrainer
from colorama import init, Fore

init()


class DDownloader:
    """ A CLASS to download http files recursivly
        coloring:bool -> colored output
        verbose:bool ->  provide details in output
    """

    def __init__(self, coloring=True, verbose=True):
        self.downloadable_links = set()
        self.crawled_links = set()
        self.verbose = verbose
        self.coloring = coloring

    async def get_page_links(self, url: str, extensions: List[str] = None, filter: Union[str, callable] = None) -> List[
        str]:

        """ returns a list of links on the page
            url:str -> the directory link
            filter:str -> regex to filter the files that matches it
            extensions:list[str] ->  specify the extensions of the files you want to fetch
        """

        links = []
        response = await self._get_source_code(url)
        if isinstance(response, bool):
            if self._is_valid_downloadable(url, filter=filter, extensions=extensions):
                self.stdoutOutput("{}Downloadable Detected {}".format(Fore.YELLOW, Fore.GREEN + url + Fore.RESET))
                self.downloadable_links.add(url)
        else:
            for a_tag in BeautifulSoup(response, 'html.parser', parse_only=SoupStrainer('a')):
                if a_tag.has_attr('href'):
                    href = urljoin(url, a_tag['href'])
                    parsed_href = urlparse(href)
                    parsed_url = urlparse(url)
                    previous_folder_path = "/{}/".format(
                        "/".join([x.strip() for x in parsed_url.path.split("/") if x][:-1]))
                    href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path
                    url_previous_folder = parsed_href.scheme + "://" + parsed_href.netloc + previous_folder_path
                    if url_previous_folder == href:
                        self.stdoutOutput("{}Skipped URL{}".format(Fore.CYAN, Fore.RESET))
                        continue
                    if self.is_valid_link(href):
                        if href not in links:
                            self.stdoutOutput("Url:{}".format(href))
                            links.append(href)
        return links

    async def crawl(self, url: str):

        """ crawl a website and search of downloadables files
            url:str -> the directory link
        """

        links = await self.get_page_links(url)
        for link in links:
            if link not in self.crawled_links:
                self.crawled_links.add(link)
                await self.crawl(link)

    async def _get_source_code(self, url: str):

        """
            return the code source of the url if html else return True
            url:str -> the directory link
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if "text/html" not in resp.headers.get("Content-Type"):
                    return True
                text = await resp.read()
                return text.decode("utf-8")

    async def _download_file(self, url: str, session: aiohttp.ClientSession, full_diretory: str = None):
        async with session.get(url) as response:
            if response.status != 200:
                response.raise_for_status()
            parsed_url = urlparse(url)
            directory = full_diretory if full_diretory else "." + "/".join(parsed_url.path.split("/")[:-1])

            file_name = parsed_url.path.split("/")[-1]
            full_file_directory = os.path.join(directory, file_name)

            if not os.path.exists(directory):
                os.makedirs(directory)

            self.stdoutOutput("{}Downloading {}{}".format(Fore.LIGHTGREEN_EX, url, Fore.RESET))

            with open(full_file_directory, "wb") as file:
                file_content = await response.read()
                file.write(file_content)
                self.stdoutOutput("{}Done..{}".format(Fore.GREEN, Fore.RESET))
                return

    async def _start_downloads(self, session: aiohttp.ClientSession, full_directory: str = None):
        self.stdoutOutput(Fore.YELLOW + "Start Downloading" + Fore.RESET)
        tasks = []
        for url in self.downloadable_links:
            task = asyncio.create_task(self._download_file(url, session, full_diretory=full_directory))
            tasks.append(task)
        results = await asyncio.gather(*tasks)
        return results

    async def download_files(self, workers: int = 5, urls: Set[str] = None, filter: Union[str, callable] = None,
                             extensions: List[str] = None, full_directory: str = None):
        """ Download multiple files
            workers:int -> number of workers on downloading
            urls:Set[str]
            filter:str -> regex to filter the files that matches it
            extensions:list[str] ->  specify the extensions of the files you want to fetch
        """
        if urls:
            self.downloadable_links = urls
        connector = aiohttp.TCPConnector(limit=workers)
        async with aiohttp.ClientSession(connector=connector) as session:
            await self._start_downloads(session, full_directory=full_directory)

    def _get_filename(self, url: str):
        parsed_url = urlparse(url)
        return parsed_url.path.split("/")[-1]

    def is_valid_link(self, url: str):
        regex = re.compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        return re.match(regex, url) is not None

    def _check_filter(self, filter, name):
        if callable(filter):
            return filter(name)

        elif isinstance(filter, str):
            return bool(re.match(filter, name))
        else:
            raise ValueError("filter needs to be either a callable or a string")

    def _check_extension(self, extensions, name):
        valid_extension = False

        for extension in extensions:

            if name.endswith(extension):
                valid_extension = True
                break
        return valid_extension

    def _is_valid_downloadable(self, url, filter: Union[str, callable] = None, extensions: List[str] = None) -> bool:
        name = self._get_filename(url)
        if filter and extensions:
            return self._check_extension(extensions, name) and self._check_filter(filter, name)

        elif filter:
            return self._check_filter(filter, name)

        elif extensions:
            return self._check_extension(extensions, name)

        else:  # if no paramaters are specified
            return True

    def clearColors(self, message):
        retVal = message

        if isinstance(message, str):
            retVal = re.sub(r"\x1b\[[\d;]+m", "", message)

        return retVal

    def stdoutOutput(self, message):
        if self.verbose:
            output = message
            if not self.coloring:
                output = self.clearColors(output)
            print(output)

