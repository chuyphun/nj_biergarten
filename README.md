# New Jersey Biergarten
A Web scraping practice


## Tools
- HTML/XML parsers

    - [beautifulsoup]()
    - [lxml](https://lxml.de/)
    - [parsel](https://github.com/scrapy/parsel)
    - [selectolax](https://github.com/rushter/selectolax)

  Which one to choose?
    - <https://lxml.de/intro.html>
    - <https://github.com/rushter/selectolax?tab=readme-ov-file#simple-benchmark>
- Browser automation
    - [playwright]
    - [selenium]
    - [puppeteer]
    - [nodriver]
    - [selenium-driverless]
- Make requests
    - [requests]()
    - [httpx]()
- scrapy


## Knowledge
- <https://pixelscan.net/>
- [CDP](https://chromedevtools.github.io/devtools-protocol/)


## TODO
- Login
    - [x] Success & Alert
    - [ ] Failure & Retry
        - [ ] Model's confidence too low => Change another captcha?
- Download captcha images for training
    - [ ] Async
- Download photos
    - [ ] Cache image URLs
    - [ ] Database
    - [ ] Async and sync
    - [ ] Ensure no duplicate download
    - [ ] Ensure all photos (on diff pages) are downloaded
    - [ ] No new image => logout
- crontab?
- `snakeviz` to catch culprit who is slowing down scraping


## Q&A
- Why the `response.read()`, when feeded to `PIL.Image`, shoud use neither
  `Image.frombytes` nor `Image.open(response.read())`? And why `io.BytesIO`
  works?
- Find out the logic behind photo naming. E.g. `images/aa503/1754/dva2rckme26sy4w.jpg`
- No significant boost of speed btw my `lxml` and `bs4` code, why?
