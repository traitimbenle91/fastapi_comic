import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from typing import List, Optional
from urllib.parse import urlsplit
import re
import json

app = FastAPI(
    title= "Truyen Tranh Scraper API",
    description="API nay cao URL anh tu trang web truyen tranh cu the"
)

#Header giúp giả lập trình duyệt để tránh bị chặn
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

root_url = "https://nettruyenviet1.com"
            

reflex_url = "http://10.0.2.2:8000/api/v1/manga"
class Story:
    def __init__(self, name):
        self.name = name
        self.link = ""
        self.cover = ""
        self.views = ""
        self.comments = ""
        self.hearts = ""
        self.chapter_name = ""
        self.chapter_link = ""
        self.chapter_release = ""

        self.author = ""
        self.status = ""
        self.kind = ""
        self.rating = 3.0
        self.rating_count = ""

        # self.number_view = ""
        # self.star_rating = 5.0
        # self.kind_story = ""
        # self.manufacturer = ""
        # self.dest = ""
        # self.chapters = []

    def __str__(self):
        return "====================================================== \n" + \
            self.name + "\n" + \
            self.link + "\n" + \
            self.cover + "\n" + \
            self.views + "\n" + \
            self.comments + "\n" + \
            self.hearts + "\n" + \
            self.chapter_name + "\n" + \
            self.chapter_link + "\n" + \
            self.chapter_release + "\n"
        

def crawl_story_names(page_number: int) -> Optional[list[Story]]:
    url = f"{root_url}/?page={page_number}"
    
    try:
        response = requests.get(url = url, headers=headers, timeout=15)

        if response.status_code != 200:
            return None
        soup = BeautifulSoup(response.content, 'html.parser')
        raise HTTPException(status_code=404, detail=f"Not found story in page: {soup}")

        storys = {}

        content = soup.find('div', class_ = 'center-side col-md-8')

        # find all item content which contain manga item
        elements = content.find_all('div', class_ = 'item')
        
        if not elements:
            return []
        for e in elements:
            name = e.figure.div.a.get('title')
            storys[name] = Story(name)
            
            url = f"{e.figure.div.a.get('href')}"
            # parsed = urlparse(url)
            # path = parsed.path.lstrip('/')
            storys[name].link = urlsplit(url).path

            storys[name].cover = e.figure.div.a.img.get('data-retries')
            storys[name].views = e.figure.div.find('i', class_ = "fa fa-eye").next_sibling.strip()
            storys[name].comments = e.figure.div.find('i', class_ = "fa fa-comment").next_sibling.strip()
            storys[name].hearts = e.figure.div.find('i', class_ = "fa fa-heart").next_sibling.strip()
            
            chapterContent = e.figure.figcaption.find_all("li", class_ = "chapter clearfix")
            storys[name].chapter_name = chapterContent[0].a.get('title')
            storys[name].chapter_link = chapterContent[0].a.get('href')
            storys[name].chapter_release = chapterContent[0].i.get_text()

            # print(storys[name])

            
            
            # return storys.values()
    
        return storys.values()
    except requests.exceptions.RequestException as e:
        print(f"There is an error when access {e}")


# storys = crawl_story_names(1)


@app.get("/api/v1/manga/{page_number}")
async def get_story_name(page_number: int):
    if page_number <= 0:
        raise HTTPException(status_code=400, detail="Page number must > 0")
    
    storys = crawl_story_names(page_number)

    if storys is None:
        raise HTTPException(status_code=404, detail=f"Not found story in page: {page_number}")

    if not storys:
        raise HTTPException(status_code=404, detail=f"Found a web but there is no story in page{page_number}, the structure of HTML can be change")
    
    objs = []

    for story in storys:
        objs.append({
            "name": story.name,
            "link": story.link,
            "cover": story.cover,
            "views": story.views,
            "comments": story.comments,
            "hearts": story.hearts,
            "lastChapter": story.chapter_name,
            "lastChapterLink": story.chapter_link,
            "lastChapterRelease": story.chapter_release
        })
    return objs
    
    
class Chapter:
    def __init__(self, chapter_name, link_chapter, time, number_view):
        self.chapter_name = chapter_name
        self.link_chapter = link_chapter
        self.time = time
        self.number_view = number_view
    def __str__(self):
        return f"{self.chapter_name}||{self.link_chapter}||{self.time}||{self.number_view}"



def crawl_list_chapters(story_name: str) -> Optional[Story]:
    url = f"{root_url}/truyen-tranh/{story_name}"
    try:
        response = requests.get(url, headers = headers, timeout=15)

        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.content, 'html.parser')
        
        story = Story("")
        story.name = soup.find('div', class_="center-side col-md-8").article.h1.get_text()
        story.cover = soup.find('div', class_="col-xs-4 col-image").img.get("src")
        story.author = soup.find('li', class_="author row").find('p', class_ = "col-xs-8").get_text()
        story.status = soup.find('li', class_="status row").find('p', class_ = "col-xs-8").get_text()
        story.kind = soup.find('li', class_="kind row").find('p', class_ = "col-xs-8").get_text()
        story.rating = soup.find('div', class_="mrt5 mrb10").find('span', attrs={'itemprop': 'ratingValue'}).text
        story.rating_count = soup.find('div', class_="mrt5 mrb10").find('span', attrs={'itemprop': 'ratingCount'}).text
                
        list_chapters = []
        elements = soup.find(id="chapter_list").find_all('li', class_='row')
        
        for e in elements:        
            chapter_name = e.div.a.get_text()
            
            link_chapter = e.div.a.get('href')
            time = e.find('div', class_="col-xs-4 no-wrap small text-center").get_text()
            number_view = e.find('div', class_="col-xs-3 no-wrap small text-center").get_text()          
            list_chapters.append(Chapter(chapter_name, link_chapter, time, number_view))
        story.chapters = list_chapters

        return story
    except requests.exceptions.RequestException as e:
        print(f"There is an error when access {e}")

# crawl_list_chapters("vo-luyen-dinh-phong")

@app.get("/api/v1/manga/truyen-tranh/{story_name}")
async def get_chapter_list(story_name: str):
    if not story_name or story_name == "":
        raise HTTPException(status_code=404, detail="There is empty story name")
    story = crawl_list_chapters(story_name)

    if story is None:
        raise HTTPException(status_code=404, detail=f"Not found story {story_name}")
    if not story:
        raise HTTPException(status_code=404, detail="Found web but there is no chapters") 
    
    
    
    json_chapters = []
    for ch in story.chapters:
        json_chapters.append(
            {
                "name": ch.chapter_name,
                "link": ch.link_chapter,
                "numberView" : ch.number_view,
                "release": ch.time
            }
        )
    rest = {
        "name": story.name,
        "cover": story.cover,
        "author": story.author,
        "status": story.status,
        "kind": story.kind,
        "rating": float(story.rating),
        "rating_count": story.rating_count,
        # "manufacturer": "",
        "description": "",
        "chapters": json_chapters
    }
    return rest

def crawl_chapter_images(story_name: str, chapter_number: str) -> Optional[List[str]]:
    """ Scrape cac URL anh tu một chương truyện cụ thể"""

    #Xây dựng URL mục tiêu
    # base_manga_name = "vo-luyen-dinh-phong"
    url = f"{root_url}/truyen-tranh/{story_name}/{chapter_number}"

    try:
        response = requests.get(url, headers = headers, timeout=15)

        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.content, 'html.parser')
        elements = soup.find_all('div', class_ = "page-chapter") 
        # print(elements[1])
        # return []
        
        if not elements:
            return []

        img_urls = []
        for e in elements:
            img_url = e.img.get('data-src')
            # print(img_url)
            if img_url != None and (img_url.endswith("jpg") or img_url.endswith("webp")):
                img_urls.append(img_url)

            # img_url = e.get('data-src')
            # if img_url != None and  img_url.startswith("https"):
            #     img_urls.append(img_url)
        # print(img_urls)
        return img_urls
    except requests.exceptions.RequestException as e:
        print(f"There is an error when access {e}")

# urls = crawl_chapter_images("nguoi-choi-moi-cap-toi-da", "chuong-225")


# /api/v1/manga/truyen-tranh/tuyet-the-vo-than/chapter-1076
@app.get("/api/v1/manga/truyen-tranh/{story_name}/{chapter_number}")
async def get_chapter_data(story_name: str, chapter_number: str):
    """
    API get list url image of chapter
    """
    if not story_name or not chapter_number:
        raise HTTPException(status_code=400, detail="There is an empty story name or chapter number")
    #crawls data
    img_list = crawl_chapter_images(story_name, chapter_number)
    # print(img_list)

    if img_list is None:
        raise HTTPException(status_code=404, detail=f"Not found chapter {chapter_number}")

    if not img_list:
        raise HTTPException(status_code=404, detail=f"Found web but there is no image in {chapter_number}, The stucture of HTML can be change")
    return {
        "manga_name": story_name,
        "chapter_name": chapter_number, 
        "total_images": len(img_list),
        "images": img_list
    }

@app.get("/")
def home():
    return {"message": "API Manga is online", "docs": "/docs"}