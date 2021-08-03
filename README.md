# Directory Downloader

Directory Downloader
is a Python library for downloading files from websites using the *directory listing* function used mostly in apache/nginx and ftp an example can be seen [here](https://ftp.mozilla.org/)

## Dependencies

Before installation, make sure you have the required dependencies of asyncio, aiohttp, bs4 and colorama.




## Installation
Use the package manager [pip](https://pip.pypa.io/en/stable/) to install directory_downloader.

```bash
pip install directory-downloader 
```

## Usage

```python

import asyncio
from directory_downloader import DDownloader


async def main():
    url = "https://example.com/directory/"
    downloader = DDownloader()
    await downloader.crawl(url)  # fetch all the links from /directory/
    await downloader.download_files()  # download all files to current directory


if __name__ == '__main__':
    asyncio.run(main())
```
## Advanced Usage

### to disable coloring:
```python
downloader = DDownloader(coloring=False)
```
### to disable verbose mode:
```python
downloader = DDownloader(verbose=False)
```
### to change the directory simply add:
```python
downloader.download_files(full_directory=r"C:\Users\User\Desktop")
```
### to make downloads faster you can increase the number of workers (by default 5):
```python
downloader.download_files(workers=5)
```
#### note : increasing the number of workers too much can lead to unstable behavior use at your own risk
### to fetch file links that have extension of pdf only you can use:
```python
await downloader.crawl(extensions=[".pdf"])
```
### you can also use regex like the following:
```python
await downloader.crawl(filter=r"test\d\d\d\.apk")   
```
### to download an existing list of urls you can do as follow:
```python
urls = set(["www.example/example/file1.pdf","www.example/example/file2.pdf",...])
await downloader.download_files(urls=urls)
```
### also you can use filter on downloadable files:
```python
await downloader.download_files(urls=urls,filter=r"test\d\d\d\.apk")
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
